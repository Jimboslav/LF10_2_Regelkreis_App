import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from streamlit_flow import streamlit_flow
from streamlit_flow.elements import StreamlitFlowNode, StreamlitFlowEdge
from streamlit_flow.state import StreamlitFlowState

# ------------------------------------------------------------
# Seiteneinstellungen
# ------------------------------------------------------------

st.set_page_config(
    page_title="Regelkreis-Labor",
    layout="wide"
)


# ------------------------------------------------------------
# Startformular / Regelkreis-Assistent
# ------------------------------------------------------------

def get_default_parameters(
    lernziel: str,
    controller_type: str,
    plant_type: str,
    disturbance_position: str,
    schwierigkeitsgrad: str
):
    """
    Erzeugt passende Startparameter abhängig von der Auswahl im Formular.
    Nicht relevante Werte werden trotzdem gesetzt, damit die Simulation stabil läuft.
    """

    defaults = {
        "kp": 2.0,
        "ki": 0.5,
        "kd": 0.0,
        "ks": 1.0,
        "ts": 2.0,
        "zeta": 0.7,
        "omega0": 2.0,
        "setpoint": 1.0,
        "t_end": 20.0,
        "dt": 0.01,
        "disturbance_time": 8.0,
        "disturbance_value": -0.3,
    }

    # Reglertypabhängige Standardwerte
    if controller_type == "P":
        defaults["kp"] = 2.0
        defaults["ki"] = 0.0
        defaults["kd"] = 0.0

    elif controller_type == "PI":
        defaults["kp"] = 2.0
        defaults["ki"] = 0.5
        defaults["kd"] = 0.0

    elif controller_type == "PID":
        defaults["kp"] = 3.0
        defaults["ki"] = 0.5
        defaults["kd"] = 0.2

    # Streckentypabhängige Standardwerte
    if plant_type == "PT1":
        defaults["ts"] = 2.0
        defaults["zeta"] = 0.7
        defaults["omega0"] = 2.0

    elif plant_type == "PT2":
        defaults["ts"] = 2.0
        defaults["zeta"] = 0.6
        defaults["omega0"] = 2.0

    # Störung
    if disturbance_position == "Keine Störung":
        defaults["disturbance_time"] = 0.0
        defaults["disturbance_value"] = 0.0

    elif disturbance_position == "Vor der Strecke":
        defaults["disturbance_time"] = 8.0
        defaults["disturbance_value"] = -0.3

    elif disturbance_position == "Am Ausgang":
        defaults["disturbance_time"] = 8.0
        defaults["disturbance_value"] = -0.3

    # Lernzielabhängige Anpassung
    if lernziel == "Grundverhalten verstehen":
        defaults["t_end"] = 20.0
        defaults["dt"] = 0.01

    elif lernziel == "Störverhalten untersuchen":
        defaults["t_end"] = 30.0
        defaults["disturbance_time"] = 10.0

        if disturbance_position == "Keine Störung":
            defaults["disturbance_value"] = 0.0
        else:
            defaults["disturbance_value"] = -0.3

    elif lernziel == "Regler optimieren":
        defaults["t_end"] = 30.0
        defaults["dt"] = 0.005

    # Schwierigkeitsgrad
    if schwierigkeitsgrad == "Einsteiger":
        defaults["dt"] = 0.01

    elif schwierigkeitsgrad == "Fortgeschritten":
        defaults["dt"] = 0.005

    elif schwierigkeitsgrad == "Experte":
        defaults["dt"] = 0.002

    return defaults


if "app_started" not in st.session_state:
    st.session_state.app_started = False


if not st.session_state.app_started:

    st.title("Regelkreis-Assistent")

    st.markdown(
        """
        Diese App unterstützt dich beim Aufbau und bei der Analyse eines geschlossenen Regelkreises.

        Wähle zuerst aus, was du untersuchen möchtest. Danach erstellt die App automatisch einen passenden
        Regelkreis mit sinnvollen Startparametern.
        """
    )

    with st.form("start_formular"):

        st.subheader("1. Ziel der Untersuchung")

        lernziel = st.selectbox(
            "Was möchtest du mit dem Regelkreis untersuchen?",
            [
                "Grundverhalten verstehen",
                "Störverhalten untersuchen",
                "Regler optimieren"
            ]
        )

        st.subheader("2. Aufbau des Regelkreises")

        controller_type = st.selectbox(
            "Welcher Reglertyp soll verwendet werden?",
            ["P", "PI", "PID"],
            index=1
        )

        plant_type = st.selectbox(
            "Welche Strecke soll untersucht werden?",
            ["PT1", "PT2"],
            index=0
        )

        disturbance_position = st.selectbox(
            "Soll eine Störung berücksichtigt werden?",
            [
                "Keine Störung",
                "Vor der Strecke",
                "Am Ausgang"
            ],
            index=0
        )

        st.subheader("3. Bedienmodus")

        schwierigkeitsgrad = st.radio(
            "Wie viele Details möchtest du einstellen können?",
            [
                "Einsteiger",
                "Fortgeschritten",
                "Experte"
            ],
            horizontal=True
        )

        submitted = st.form_submit_button("Regelkreis erstellen")

    if submitted:
        defaults = get_default_parameters(
            lernziel=lernziel,
            controller_type=controller_type,
            plant_type=plant_type,
            disturbance_position=disturbance_position,
            schwierigkeitsgrad=schwierigkeitsgrad
        )

        st.session_state.app_started = True
        st.session_state.lernziel = lernziel
        st.session_state.controller_type = controller_type
        st.session_state.plant_type = plant_type
        st.session_state.disturbance_position = disturbance_position
        st.session_state.schwierigkeitsgrad = schwierigkeitsgrad
        st.session_state.defaults = defaults

        st.rerun()

    st.stop()


# ------------------------------------------------------------
# Hilfsfunktionen
# ------------------------------------------------------------

def blockdiagramm(controller_type: str, plant_type: str, disturbance_position: str) -> str:
    """
    Erzeugt ein DOT-Diagramm für st.graphviz_chart.
    """

    disturbance_label = "Störung d(t)"

    if disturbance_position == "Keine Störung":
        disturbance_part = ""
        input_to_plant = "regler -> strecke"
        output_label = "strecke -> ausgang"

    elif disturbance_position == "Vor der Strecke":
        disturbance_part = f"""
        dist [label="{disturbance_label}", shape=ellipse, style=dashed];
        summ2 [label="Σ", shape=circle, fillcolor="#FFFFFF"];
        regler -> summ2;
        dist -> summ2;
        summ2 -> strecke;
        """

        input_to_plant = ""
        output_label = "strecke -> ausgang"

    else:
        disturbance_part = f"""
        dist [label="{disturbance_label}", shape=ellipse, style=dashed];
        summ3 [label="Σ", shape=circle, fillcolor="#FFFFFF"];
        strecke -> summ3;
        dist -> summ3;
        summ3 -> ausgang;
        """

        input_to_plant = "regler -> strecke"
        output_label = ""

    return f"""
    digraph {{
        rankdir=LR;
        node [shape=box, style="rounded,filled", fillcolor="#F7F7F7", fontname="Arial"];

        soll [label="Sollwert w(t)"];
        summ1 [label="Σ", shape=circle, fillcolor="#FFFFFF"];
        regler [label="{controller_type}-Regler"];
        strecke [label="{plant_type}-Strecke"];
        ausgang [label="Regelgröße y(t)"];
        rueck [label="Rückführung", shape=box];

        soll -> summ1;
        summ1 -> regler [label="e(t)"];
        {input_to_plant};
        {output_label};
        ausgang -> rueck;
        rueck -> summ1 [label="-y(t)"];

        {disturbance_part}
    }}
    """


def simulate_control_loop(
    controller_type: str,
    plant_type: str,
    kp: float,
    ki: float,
    kd: float,
    ks: float,
    ts: float,
    zeta: float,
    omega0: float,
    setpoint: float,
    t_end: float,
    dt: float,
    disturbance_position: str,
    disturbance_time: float,
    disturbance_value: float,
):
    """
    Numerische Simulation eines geschlossenen Regelkreises.

    PT1:
    Ts * dy/dt + y = Ks * u

    PT2:
    y'' + 2*zeta*omega0*y' + omega0^2*y = Ks*omega0^2*u
    """

    t = np.arange(0.0, t_end + dt, dt)

    y_plant = np.zeros_like(t)
    y_out = np.zeros_like(t)
    u_controller = np.zeros_like(t)
    error = np.zeros_like(t)
    disturbance = np.zeros_like(t)

    integral_error = 0.0
    previous_error = 0.0

    # Geschwindigkeit der Regelgröße, nur für PT2 relevant
    velocity = 0.0

    for k in range(1, len(t)):

        # Störung ab einem bestimmten Zeitpunkt aktivieren
        if t[k] >= disturbance_time:
            disturbance[k] = disturbance_value
        else:
            disturbance[k] = 0.0

        # Regeldifferenz: e(t) = w(t) - y(t)
        error[k] = setpoint - y_out[k - 1]

        # P-Anteil
        p_part = kp * error[k]

        # I-Anteil
        if controller_type in ["PI", "PID"]:
            integral_error += error[k] * dt
        else:
            integral_error = 0.0

        i_part = ki * integral_error

        # D-Anteil
        if controller_type == "PID":
            d_part = kd * (error[k] - previous_error) / dt
        else:
            d_part = 0.0

        # Stellgröße des Reglers
        u_controller[k] = p_part + i_part + d_part
        previous_error = error[k]

        # Störung wahlweise vor der Strecke oder am Ausgang
        if disturbance_position == "Vor der Strecke":
            u_effective = u_controller[k] + disturbance[k]
            output_disturbance = 0.0

        elif disturbance_position == "Am Ausgang":
            u_effective = u_controller[k]
            output_disturbance = disturbance[k]

        else:
            u_effective = u_controller[k]
            output_disturbance = 0.0

        # PT1-Strecke
        if plant_type == "PT1":
            dy = (ks * u_effective - y_plant[k - 1]) / ts
            y_plant[k] = y_plant[k - 1] + dy * dt

        # PT2-Strecke
        else:
            acceleration = (
                ks * omega0**2 * u_effective
                - 2 * zeta * omega0 * velocity
                - omega0**2 * y_plant[k - 1]
            )

            velocity = velocity + acceleration * dt
            y_plant[k] = y_plant[k - 1] + velocity * dt

        y_out[k] = y_plant[k] + output_disturbance

    df = pd.DataFrame({
        "Zeit [s]": t,
        "Sollwert w": setpoint,
        "Regelgröße y": y_out,
        "Stellgröße u": u_controller,
        "Regeldifferenz e": error,
        "Störung d": disturbance,
    })

    return df


def calculate_metrics(df: pd.DataFrame, setpoint: float):
    """
    Berechnet einfache Kennwerte aus der Simulation.
    """

    y = df["Regelgröße y"].to_numpy()
    t = df["Zeit [s]"].to_numpy()

    final_value = y[-1]
    steady_error = setpoint - final_value

    if setpoint != 0:
        overshoot = max(0.0, (np.max(y) - setpoint) / abs(setpoint) * 100)
        tolerance = 0.02 * abs(setpoint)
    else:
        overshoot = 0.0
        tolerance = 0.02

    settling_time = None

    for i in range(len(y)):
        if np.all(np.abs(y[i:] - setpoint) <= tolerance):
            settling_time = t[i]
            break

    return final_value, steady_error, overshoot, settling_time


# ------------------------------------------------------------
# Oberfläche nach Startformular
# ------------------------------------------------------------

st.title("Regelkreis-Labor")

st.caption(
    "Interaktive Simulation eines geschlossenen Regelkreises mit Regler, "
    "Strecke, Rückführung und optionaler Störung."
)


# ------------------------------------------------------------
# Sidebar: Eingaben mit einklappbaren Menüs
# ------------------------------------------------------------

defaults = st.session_state.defaults

with st.sidebar:

    with st.expander("Auswahl aus dem Startformular", expanded=True):

        st.info(
            f"""
            **Lernziel:** {st.session_state.lernziel}  
            **Regler:** {st.session_state.controller_type}  
            **Strecke:** {st.session_state.plant_type}  
            **Störung:** {st.session_state.disturbance_position}  
            **Modus:** {st.session_state.schwierigkeitsgrad}
            """
        )

        if st.button("Startformular neu öffnen"):
            st.session_state.app_started = False
            st.rerun()


    with st.expander("1. Regelkreis aufbauen", expanded=True):

        controller_type = st.selectbox(
            "Reglertyp",
            ["P", "PI", "PID"],
            index=["P", "PI", "PID"].index(st.session_state.controller_type)
        )

        plant_type = st.selectbox(
            "Streckentyp",
            ["PT1", "PT2"],
            index=["PT1", "PT2"].index(st.session_state.plant_type)
        )

        disturbance_position = st.selectbox(
            "Störung platzieren",
            ["Keine Störung", "Vor der Strecke", "Am Ausgang"],
            index=["Keine Störung", "Vor der Strecke", "Am Ausgang"].index(
                st.session_state.disturbance_position
            )
        )


    with st.expander("2. Reglerparameter", expanded=False):

        kp = st.number_input(
            "Kp - Proportionalverstärkung",
            min_value=0.0,
            max_value=100.0,
            value=float(defaults["kp"]),
            step=0.1,
            help="Kp bestimmt, wie stark der Regler direkt auf die aktuelle Regelabweichung reagiert."
        )

        if controller_type in ["PI", "PID"]:
            ki = st.number_input(
                "Ki - Integralverstärkung",
                min_value=0.0,
                max_value=100.0,
                value=float(defaults["ki"]),
                step=0.1,
                help="Ki baut eine bleibende Regelabweichung über die Zeit ab."
            )
        else:
            ki = 0.0
            st.caption("Ki wird beim P-Regler automatisch auf 0 gesetzt.")

        if controller_type == "PID":
            kd = st.number_input(
                "Kd - Differentialverstärkung",
                min_value=0.0,
                max_value=100.0,
                value=float(defaults["kd"]),
                step=0.1,
                help="Kd reagiert auf schnelle Änderungen der Regelabweichung und kann Überschwingen dämpfen."
            )
        else:
            kd = 0.0
            st.caption("Kd ist nur beim PID-Regler relevant und wird automatisch auf 0 gesetzt.")


    with st.expander("3. Streckenparameter", expanded=False):

        ks = st.number_input(
            "Ks - Streckenverstärkung",
            min_value=0.1,
            max_value=100.0,
            value=float(defaults["ks"]),
            step=0.1,
            help="Ks beschreibt, wie stark die Strecke auf die Stellgröße reagiert."
        )

        if plant_type == "PT1":
            ts = st.number_input(
                "Ts - Zeitkonstante PT1 [s]",
                min_value=0.1,
                max_value=100.0,
                value=float(defaults["ts"]),
                step=0.1,
                help="Ts beschreibt die Trägheit der PT1-Strecke."
            )

            zeta = defaults["zeta"]
            omega0 = defaults["omega0"]

            st.caption("ζ und ω0 sind für PT1 nicht relevant und werden automatisch intern gesetzt.")

        else:
            zeta = st.number_input(
                "Dämpfung ζ PT2",
                min_value=0.05,
                max_value=5.0,
                value=float(defaults["zeta"]),
                step=0.05,
                help="ζ bestimmt, wie stark die PT2-Strecke schwingt oder gedämpft wird."
            )

            omega0 = st.number_input(
                "Eigenkreisfrequenz ω0 PT2 [rad/s]",
                min_value=0.1,
                max_value=100.0,
                value=float(defaults["omega0"]),
                step=0.1,
                help="ω0 beschreibt die Eigenkreisfrequenz der PT2-Strecke."
            )

            ts = defaults["ts"]

            st.caption("Ts ist für PT2 nicht relevant und wird automatisch intern gesetzt.")


    with st.expander("4. Simulation", expanded=False):

        setpoint = st.number_input(
            "Sollwert w",
            value=float(defaults["setpoint"]),
            step=0.1,
            help="Der Sollwert ist die Führungsgröße, die die Regelgröße erreichen soll."
        )

        t_end = st.number_input(
            "Simulationsdauer [s]",
            min_value=1.0,
            max_value=200.0,
            value=float(defaults["t_end"]),
            step=1.0
        )

        if st.session_state.schwierigkeitsgrad == "Experte":
            dt = st.number_input(
                "Schrittweite dt [s]",
                min_value=0.001,
                max_value=1.0,
                value=float(defaults["dt"]),
                step=0.001,
                format="%.3f",
                help="Kleinere Schrittweiten erhöhen die Genauigkeit, benötigen aber mehr Rechenpunkte."
            )
        else:
            dt = defaults["dt"]
            st.caption(f"Schrittweite dt wird automatisch auf {dt} s gesetzt.")

        if disturbance_position != "Keine Störung":
            disturbance_time = st.number_input(
                "Störung ab Zeitpunkt [s]",
                min_value=0.0,
                max_value=200.0,
                value=float(defaults["disturbance_time"]),
                step=0.5
            )

            disturbance_value = st.number_input(
                "Störgröße d",
                value=float(defaults["disturbance_value"]),
                step=0.1
            )
        else:
            disturbance_time = 0.0
            disturbance_value = 0.0
            st.caption("Keine Störung gewählt. Störzeitpunkt und Störgröße werden automatisch auf 0 gesetzt.")


# ------------------------------------------------------------
# Plausibilitätsprüfung
# ------------------------------------------------------------

if dt >= t_end / 20:
    st.warning(
        "Die Schrittweite dt ist relativ groß. "
        "Für saubere Kurven sollte dt deutlich kleiner als die Simulationsdauer sein."
    )


# ------------------------------------------------------------
# Simulation ausführen
# ------------------------------------------------------------

df = simulate_control_loop(
    controller_type=controller_type,
    plant_type=plant_type,
    kp=kp,
    ki=ki,
    kd=kd,
    ks=ks,
    ts=ts,
    zeta=zeta,
    omega0=omega0,
    setpoint=setpoint,
    t_end=t_end,
    dt=dt,
    disturbance_position=disturbance_position,
    disturbance_time=disturbance_time,
    disturbance_value=disturbance_value,
)


# ------------------------------------------------------------
# Kennwerte berechnen
# ------------------------------------------------------------

final_value, steady_error, overshoot, settling_time = calculate_metrics(df, setpoint)


# ------------------------------------------------------------
# Kennzahlen anzeigen
# ------------------------------------------------------------

col1, col2, col3, col4 = st.columns(4)

col1.metric("Endwert y", f"{final_value:.3f}")
col2.metric("bleibende Abweichung", f"{steady_error:.3f}")
col3.metric("Überschwingen", f"{overshoot:.1f} %")

if settling_time is None:
    col4.metric("Einschwingzeit", "nicht erreicht")
else:
    col4.metric("Einschwingzeit", f"{settling_time:.2f} s")


# ------------------------------------------------------------
# Automatische Auswertung
# ------------------------------------------------------------

st.subheader("Automatische Auswertung")

bewertung = []

if abs(steady_error) > 0.05:
    bewertung.append(
        "Es bleibt eine erkennbare Regelabweichung bestehen. "
        "Das ist typisch für einen reinen P-Regler oder eine zu schwache Reglerauslegung."
    )
else:
    bewertung.append(
        "Die bleibende Regelabweichung ist gering. Der Sollwert wird gut erreicht."
    )

if overshoot > 20:
    bewertung.append(
        "Das Überschwingen ist deutlich. Der Regelkreis ist relativ aggressiv eingestellt."
    )
elif overshoot > 5:
    bewertung.append(
        "Es ist ein moderates Überschwingen erkennbar."
    )
else:
    bewertung.append(
        "Das Überschwingen ist gering oder nicht vorhanden."
    )

if settling_time is None:
    bewertung.append(
        "Die Einschwingzeit wurde innerhalb der Simulationsdauer nicht erreicht. "
        "Die Simulationsdauer könnte zu kurz sein oder der Regelkreis schwingt zu stark."
    )
else:
    bewertung.append(
        f"Der Regelkreis erreicht das Toleranzband nach etwa {settling_time:.2f} s."
    )

if disturbance_position != "Keine Störung":
    bewertung.append(
        f"Die Störung wurde an der Stelle '{disturbance_position}' eingefügt. "
        "Im Zeitverlauf ist erkennbar, wie der Regler auf diese Störung reagiert."
    )

for text in bewertung:
    st.write("- " + text)


# ------------------------------------------------------------
# Regelkreis grafisch anzeigen / Baustein-Builder
# ------------------------------------------------------------

tab_auto, tab_builder = st.tabs(
    [
        "Automatischer Regelkreis",
        "Baustein-Builder"
    ]
)

with tab_auto:
    st.subheader("Vervollständigter Regelkreis")

    st.graphviz_chart(
        blockdiagramm(controller_type, plant_type, disturbance_position),
        use_container_width=True
    )

with tab_builder:
    st.subheader("Regelkreis aus Bausteinen zusammensetzen")

    st.info(
        "Hier kannst du die Bausteine des Regelkreises verschieben und den Aufbau visuell nachvollziehen. "
        "Die Simulation verwendet weiterhin die Parameter aus der Sidebar."
    )

    if "flow_state" not in st.session_state:
        nodes = [
            StreamlitFlowNode(
                id="sollwert",
                pos=(0, 150),
                data={"content": "Sollwert<br>w(t)"},
                node_type="input",
                source_position="right",
                draggable=True
            ),
            StreamlitFlowNode(
                id="summe",
                pos=(220, 150),
                data={"content": "Σ<br>e(t)=w(t)-y(t)"},
                node_type="default",
                source_position="right",
                target_position="left",
                draggable=True
            ),
            StreamlitFlowNode(
                id="regler",
                pos=(460, 150),
                data={"content": f"{controller_type}-Regler<br>u(t)"},
                node_type="default",
                source_position="right",
                target_position="left",
                draggable=True
            ),
            StreamlitFlowNode(
                id="strecke",
                pos=(720, 150),
                data={"content": f"{plant_type}-Strecke<br>y(t)"},
                node_type="default",
                source_position="right",
                target_position="left",
                draggable=True
            ),
            StreamlitFlowNode(
                id="ausgang",
                pos=(980, 150),
                data={"content": "Regelgröße<br>y(t)"},
                node_type="output",
                target_position="left",
                draggable=True
            ),
            StreamlitFlowNode(
                id="rueckfuehrung",
                pos=(460, 350),
                data={"content": "Rückführung<br>-y(t)"},
                node_type="default",
                source_position="left",
                target_position="right",
                draggable=True
            ),
        ]

        edges = [
            StreamlitFlowEdge(
                id="e_soll_summe",
                source="sollwert",
                target="summe",
                animated=True,
                label="w(t)"
            ),
            StreamlitFlowEdge(
                id="e_summe_regler",
                source="summe",
                target="regler",
                animated=True,
                label="e(t)"
            ),
            StreamlitFlowEdge(
                id="e_regler_strecke",
                source="regler",
                target="strecke",
                animated=True,
                label="u(t)"
            ),
            StreamlitFlowEdge(
                id="e_strecke_ausgang",
                source="strecke",
                target="ausgang",
                animated=True,
                label="y(t)"
            ),
            StreamlitFlowEdge(
                id="e_ausgang_rueck",
                source="ausgang",
                target="rueckfuehrung",
                animated=False,
                label="Istwert"
            ),
            StreamlitFlowEdge(
                id="e_rueck_summe",
                source="rueckfuehrung",
                target="summe",
                animated=False,
                label="-y(t)"
            ),
        ]

        if disturbance_position != "Keine Störung":
            nodes.append(
                StreamlitFlowNode(
                    id="stoerung",
                    pos=(720, 20),
                    data={"content": f"Störung<br>d(t)<br>{disturbance_position}"},
                    node_type="default",
                    source_position="bottom",
                    target_position="top",
                    draggable=True
                )
            )

            if disturbance_position == "Vor der Strecke":
                edges.append(
                    StreamlitFlowEdge(
                        id="e_stoerung_strecke",
                        source="stoerung",
                        target="strecke",
                        animated=True,
                        label="d(t)"
                    )
                )

            elif disturbance_position == "Am Ausgang":
                edges.append(
                    StreamlitFlowEdge(
                        id="e_stoerung_ausgang",
                        source="stoerung",
                        target="ausgang",
                        animated=True,
                        label="d(t)"
                    )
                )

        st.session_state.flow_state = StreamlitFlowState(nodes, edges)

    updated_state = streamlit_flow(
        "regelkreis_builder",
        st.session_state.flow_state,
        fit_view=False,
        show_minimap=True,
        show_controls=True,
        allow_new_edges=False,
        animate_new_edges=False,
        height=560
    )

    st.session_state.flow_state = updated_state

    with st.expander("Aktuelle Baustein-Struktur anzeigen"):
        st.write("Nodes:")
        st.write(updated_state.nodes)
        st.write("Verbindungen:")
        st.write(updated_state.edges)


# ------------------------------------------------------------
# Zeitverlauf anzeigen
# ------------------------------------------------------------

st.subheader("Zeitverlauf")

fig, ax = plt.subplots(figsize=(10, 4.8))

ax.plot(
    df["Zeit [s]"],
    df["Sollwert w"],
    linestyle="--",
    label="Sollwert w"
)

ax.plot(
    df["Zeit [s]"],
    df["Regelgröße y"],
    linewidth=2,
    label="Regelgröße y"
)

ax.plot(
    df["Zeit [s]"],
    df["Stellgröße u"],
    alpha=0.8,
    label="Stellgröße u"
)

if disturbance_position != "Keine Störung":
    ax.plot(
        df["Zeit [s]"],
        df["Störung d"],
        linestyle=":",
        label="Störung d"
    )

ax.set_xlabel("Zeit [s]")
ax.set_ylabel("Signalwert")
ax.grid(True, linestyle=":", alpha=0.6)
ax.legend(loc="best")

st.pyplot(fig)


# ------------------------------------------------------------
# Rohdaten anzeigen
# ------------------------------------------------------------

with st.expander("Rohdaten anzeigen"):
    st.dataframe(df, use_container_width=True)


# ------------------------------------------------------------
# Technische Einordnung
# ------------------------------------------------------------

with st.expander("Technische Einordnung"):
    st.markdown(
        f"""
        **Aktueller Aufbau:** {controller_type}-Regler mit {plant_type}-Strecke.

        **Reglerprinzip:**  
        Die Regeldifferenz wird berechnet aus:

        $$
        e(t) = w(t) - y(t)
        $$

        Daraus bildet der Regler die Stellgröße:

        $$
        u(t) = K_p \\cdot e(t) + K_i \\int e(t)dt + K_d \\frac{{de(t)}}{{dt}}
        $$

        Je nach Auswahl werden P-, I- und D-Anteil aktiviert oder deaktiviert.

        **Rückführung:**  
        Die Regelgröße y(t) wird auf den Eingang zurückgeführt und vom Sollwert w(t) abgezogen.

        **Störung:**  
        {disturbance_position}
        """
    )
