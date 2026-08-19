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
# Grundzustand für Navigation
# ------------------------------------------------------------

if "app_started" not in st.session_state:
    st.session_state.app_started = False

if "active_view" not in st.session_state:
    st.session_state.active_view = "simulation"


# ------------------------------------------------------------
# Obere Navigation
# ------------------------------------------------------------

def render_top_navigation():
    """
    Horizontale Arbeitsbereich-Navigation oberhalb der App.
    Diese Navigation wird auf jeder Ansicht angezeigt.
    """

    with st.container(border=True):
        col1, col2, col3, col4 = st.columns([1.2, 1.6, 1.7, 1.5])

        with col1:
            if st.button(
                "Simulation",
                width="stretch",
                type="primary" if st.session_state.active_view == "simulation" else "secondary"
            ):
                st.session_state.app_started = True
                st.session_state.active_view = "simulation"
                st.rerun()

        with col2:
            if st.button(
                "Physikalischer Wirkplan",
                width="stretch",
                type="primary" if st.session_state.active_view == "wirkplan" else "secondary"
            ):
                st.session_state.app_started = True
                st.session_state.active_view = "wirkplan"
                st.rerun()

        with col3:
            if st.button(
                "Visueller Regelkreis-Builder",
                width="stretch",
                type="primary" if st.session_state.active_view == "builder" else "secondary"
            ):
                st.session_state.app_started = True
                st.session_state.active_view = "builder"
                st.rerun()

        with col4:
            if st.button(
                "Startformular neu öffnen",
                width="stretch",
                type="primary" if not st.session_state.app_started else "secondary"
            ):
                st.session_state.app_started = False
                st.session_state.active_view = "start"
                st.rerun()


render_top_navigation()

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

    if plant_type == "PT1":
        defaults["ts"] = 2.0
        defaults["zeta"] = 0.7
        defaults["omega0"] = 2.0

    elif plant_type == "PT2":
        defaults["ts"] = 2.0
        defaults["zeta"] = 0.6
        defaults["omega0"] = 2.0

    if disturbance_position == "Keine Störung":
        defaults["disturbance_time"] = 0.0
        defaults["disturbance_value"] = 0.0

    elif disturbance_position in ["Vor der Strecke", "Am Ausgang"]:
        defaults["disturbance_time"] = 8.0
        defaults["disturbance_value"] = -0.3

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

    if schwierigkeitsgrad == "Einsteiger":
        defaults["dt"] = 0.01

    elif schwierigkeitsgrad == "Fortgeschritten":
        defaults["dt"] = 0.005

    elif schwierigkeitsgrad == "Experte":
        defaults["dt"] = 0.002

    return defaults


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
            ],
            help=(
                "Das Lernziel legt fest, worauf die App den Schwerpunkt setzt: "
                "Grundverhalten, Störverhalten oder gezielte Regleroptimierung."
            )
        )

        with st.expander("Hilfe: Was bedeuten die Lernziele?", expanded=False):
            st.markdown(
                """
                **Grundverhalten verstehen**  
                Die App zeigt das grundsätzliche Verhalten eines geschlossenen Regelkreises.  
                Du erkennst, wie Sollwert, Regelgröße, Regeldifferenz, Regler, Strecke und Rückführung zusammenwirken.

                **Störverhalten untersuchen**  
                Die App legt den Schwerpunkt auf Störungen.  
                Du kannst erkennen, wie der Regelkreis auf eine Störung reagiert und ob der Regler diese wieder ausregelt.

                **Regler optimieren**  
                Die App ist stärker auf Parametervergleich ausgelegt.  
                Du kannst untersuchen, wie sich Kp, Ki und Kd auf Überschwingen, Einschwingzeit und bleibende Regelabweichung auswirken.
                """
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
            horizontal=True,
            help=(
                "Der Modus steuert, wie viele technische Einstellmöglichkeiten sichtbar sind "
                "und welche Werte die App automatisch vorbelegt."
            )
        )

        with st.expander("Hilfe: Was bedeuten die Modi?", expanded=False):
            st.markdown(
                """
                **Einsteiger**  
                Die App übernimmt viele technische Werte automatisch.  
                Geeignet, wenn du erstmal das Prinzip des Regelkreises verstehen möchtest.

                **Fortgeschritten**  
                Die App rechnet mit feineren Standardwerten und eignet sich besser zum Vergleichen von Regelverhalten.  
                Die Bedienung bleibt aber weiterhin geführt.

                **Experte**  
                Du bekommst zusätzliche technische Einstellmöglichkeiten, zum Beispiel die Simulations-Schrittweite `dt`.  
                Dieser Modus ist sinnvoll, wenn du gezielt Parameter untersuchen möchtest.
                """
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

        st.session_state.builder_config = defaults.copy()
        st.session_state.builder_config["controller_type"] = controller_type
        st.session_state.builder_config["plant_type"] = plant_type
        st.session_state.builder_config["disturbance_position"] = disturbance_position

        st.session_state.active_view = "simulation"

        st.rerun()

    st.stop()


# ------------------------------------------------------------
# Grundzustände
# ------------------------------------------------------------


if "builder_config" not in st.session_state:
    st.session_state.builder_config = {
        "controller_type": st.session_state.get("controller_type", "PI"),
        "plant_type": st.session_state.get("plant_type", "PT1"),
        "disturbance_position": st.session_state.get("disturbance_position", "Keine Störung"),
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

if "builder_step" not in st.session_state:
    st.session_state.builder_step = 1

if "builder_last_validation" not in st.session_state:
    st.session_state.builder_last_validation = None


if "wirkplan_config" not in st.session_state:
    st.session_state.wirkplan_config = {
        "prozessart": "Temperaturregelung",
        "stellgroesse": "Heizleistung P [W]",
        "prozessglied": "thermische Strecke / Raum",
        "speicher": "thermische Masse",
        "regelgroesse": "Temperatur T [°C]",
        "stoergroesse": "Außentemperatur / Fremdwärme",
        "traegheit": "träge",
        "ueberschwingen_zulaessig": "Nein",
        "bleibende_abweichung_erlaubt": "Nein",
        "stoerungen_relevant": "Ja",
    }


# ------------------------------------------------------------
# Hilfsfunktionen Simulation
# ------------------------------------------------------------

def blockdiagramm(controller_type: str, plant_type: str, disturbance_position: str) -> str:
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
    t = np.arange(0.0, t_end + dt, dt)

    y_plant = np.zeros_like(t)
    y_out = np.zeros_like(t)
    u_controller = np.zeros_like(t)
    error = np.zeros_like(t)
    disturbance = np.zeros_like(t)

    integral_error = 0.0
    previous_error = 0.0
    velocity = 0.0

    for k in range(1, len(t)):

        if t[k] >= disturbance_time:
            disturbance[k] = disturbance_value
        else:
            disturbance[k] = 0.0

        error[k] = setpoint - y_out[k - 1]

        p_part = kp * error[k]

        if controller_type in ["PI", "PID"]:
            integral_error += error[k] * dt
        else:
            integral_error = 0.0

        i_part = ki * integral_error

        if controller_type == "PID":
            d_part = kd * (error[k] - previous_error) / dt
        else:
            d_part = 0.0

        u_controller[k] = p_part + i_part + d_part
        previous_error = error[k]

        if disturbance_position == "Vor der Strecke":
            u_effective = u_controller[k] + disturbance[k]
            output_disturbance = 0.0

        elif disturbance_position == "Am Ausgang":
            u_effective = u_controller[k]
            output_disturbance = disturbance[k]

        else:
            u_effective = u_controller[k]
            output_disturbance = 0.0

        if plant_type == "PT1":
            dy = (ks * u_effective - y_plant[k - 1]) / ts
            y_plant[k] = y_plant[k - 1] + dy * dt

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
# Visueller Regelkreis-Builder – geführter Engineering-Prozess
# ------------------------------------------------------------

def reset_guided_builder():
    """Setzt den geführten Regelkreis-Builder auf einen sauberen Startzustand zurück."""
    for key in list(st.session_state.keys()):
        if key.startswith("guided_"):
            del st.session_state[key]

    st.session_state.builder_step = 1
    st.session_state.builder_last_validation = None
    st.session_state.builder_config = {
        "controller_type": "PI",
        "plant_type": "PT1",
        "disturbance_position": "Keine Störung",
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
        "setpoint_name": "Sollwert w(t)",
        "output_name": "Regelgröße y(t)",
    }


def validate_guided_builder(config: dict):
    """Prüft den im Builder erzeugten Regelkreis auf Vollständigkeit und sinnvolle Parameter."""
    errors = []
    warnings = []

    if config.get("controller_type") not in ["P", "PI", "PID"]:
        errors.append("Es wurde kein gültiger Reglertyp gewählt.")

    if config.get("plant_type") not in ["PT1", "PT2"]:
        errors.append("Es wurde kein gültiger Streckentyp gewählt.")

    if float(config.get("kp", 0.0)) < 0:
        errors.append("Kp darf nicht negativ sein.")

    if config.get("controller_type") in ["PI", "PID"] and float(config.get("ki", 0.0)) <= 0:
        warnings.append("Der I-Anteil ist 0. Der gewählte Regler verhält sich dadurch ohne wirksamen Integralanteil.")

    if config.get("controller_type") == "PID" and float(config.get("kd", 0.0)) <= 0:
        warnings.append("Der D-Anteil ist 0. Der PID-Regler verhält sich dadurch praktisch wie ein PI-Regler.")

    if float(config.get("ks", 0.0)) <= 0:
        errors.append("Die Streckenverstärkung Ks muss größer als 0 sein.")

    if config.get("plant_type") == "PT1" and float(config.get("ts", 0.0)) <= 0:
        errors.append("Die Zeitkonstante Ts der PT1-Strecke muss größer als 0 sein.")

    if config.get("plant_type") == "PT2":
        if float(config.get("zeta", 0.0)) <= 0:
            errors.append("Die Dämpfung ζ der PT2-Strecke muss größer als 0 sein.")
        if float(config.get("omega0", 0.0)) <= 0:
            errors.append("Die Eigenkreisfrequenz ω0 muss größer als 0 sein.")

    if float(config.get("t_end", 0.0)) <= 0:
        errors.append("Die Simulationsdauer muss größer als 0 sein.")

    if float(config.get("dt", 0.0)) <= 0:
        errors.append("Die Schrittweite dt muss größer als 0 sein.")
    elif float(config.get("dt", 0.0)) >= float(config.get("t_end", 1.0)) / 20:
        warnings.append("Die Schrittweite dt ist relativ groß. Für eine saubere Simulation sollte sie deutlich kleiner sein.")

    if config.get("disturbance_position") != "Keine Störung":
        if float(config.get("disturbance_time", 0.0)) >= float(config.get("t_end", 0.0)):
            warnings.append("Die Störung liegt außerhalb oder genau am Ende der Simulationszeit und wird kaum sichtbar sein.")

    return errors, warnings


def build_guided_flow(config: dict, step: int):
    """
    Erzeugt den visuellen Regelkreis schrittweise.
    Je weiter der Engineering-Prozess fortgeschritten ist, desto mehr Bausteine werden eingeblendet.
    """
    nodes = []
    edges = []

    # Schritt 1: Regelaufgabe
    nodes.append(
        StreamlitFlowNode(
            id="sollwert",
            pos=(0, 190),
            data={"content": f"{config.get('setpoint_name', 'Sollwert w(t)')}<br>w = {config.get('setpoint', 1.0)}"},
            node_type="input",
            source_position="right",
            draggable=True
        )
    )

    if step == 1:
        nodes.append(
            StreamlitFlowNode(
                id="ziel",
                pos=(760, 190),
                data={"content": f"Zielgröße<br>{config.get('output_name', 'Regelgröße y(t)')}"},
                node_type="output",
                target_position="left",
                draggable=True
            )
        )
        return StreamlitFlowState(nodes, edges)

    # Schritt 2: Vergleichsstelle + Regler
    nodes.extend([
        StreamlitFlowNode(
            id="summe",
            pos=(210, 190),
            data={"content": "Vergleichsstelle Σ<br>e = w - y"},
            node_type="default",
            source_position="right",
            target_position="left",
            draggable=True
        ),
        StreamlitFlowNode(
            id="regler",
            pos=(450, 190),
            data={
                "content": (
                    f"{config.get('controller_type', 'PI')}-Regler<br>"
                    f"Kp={config.get('kp', 2.0)}<br>"
                    f"Ki={config.get('ki', 0.0)}<br>"
                    f"Kd={config.get('kd', 0.0)}"
                )
            },
            node_type="default",
            source_position="right",
            target_position="left",
            draggable=True
        ),
    ])

    edges.extend([
        StreamlitFlowEdge(id="b1", source="sollwert", target="summe", animated=True, label="w"),
        StreamlitFlowEdge(id="b2", source="summe", target="regler", animated=True, label="e"),
    ])

    if step == 2:
        return StreamlitFlowState(nodes, edges)

    # Schritt 3: Strecke
    plant_type = config.get("plant_type", "PT1")
    if plant_type == "PT1":
        plant_text = f"PT1-Strecke<br>Ks={config.get('ks', 1.0)}<br>Ts={config.get('ts', 2.0)} s"
    else:
        plant_text = (
            f"PT2-Strecke<br>Ks={config.get('ks', 1.0)}<br>"
            f"ζ={config.get('zeta', 0.7)}<br>ω0={config.get('omega0', 2.0)} rad/s"
        )

    nodes.append(
        StreamlitFlowNode(
            id="strecke",
            pos=(720, 190),
            data={"content": plant_text},
            node_type="default",
            source_position="right",
            target_position="left",
            draggable=True
        )
    )

    edges.append(
        StreamlitFlowEdge(id="b3", source="regler", target="strecke", animated=True, label="u")
    )

    if step == 3:
        return StreamlitFlowState(nodes, edges)

    # Schritt 4 und 5: Ausgang + Rückführung + optionale Störung
    nodes.extend([
        StreamlitFlowNode(
            id="ausgang",
            pos=(1010, 190),
            data={"content": f"{config.get('output_name', 'Regelgröße y(t)')}"},
            node_type="output",
            target_position="left",
            draggable=True
        ),
        StreamlitFlowNode(
            id="rueck",
            pos=(500, 410),
            data={"content": "Rückführung<br>Istwert y(t)"},
            node_type="default",
            source_position="left",
            target_position="right",
            draggable=True
        ),
    ])

    edges.extend([
        StreamlitFlowEdge(id="b4", source="strecke", target="ausgang", animated=True, label="y"),
        StreamlitFlowEdge(id="b5", source="ausgang", target="rueck", animated=False, label="Istwert"),
        StreamlitFlowEdge(id="b6", source="rueck", target="summe", animated=False, label="-y"),
    ])

    disturbance_position = config.get("disturbance_position", "Keine Störung")

    if disturbance_position == "Vor der Strecke":
        # Regler -> Strecke wird durch zusätzliche Summierstelle ersetzt
        edges = [edge for edge in edges if edge.id != "b3"]
        nodes.extend([
            StreamlitFlowNode(
                id="stoerung",
                pos=(610, 25),
                data={
                    "content": (
                        f"Störung d(t)<br>d={config.get('disturbance_value', -0.3)}<br>"
                        f"ab {config.get('disturbance_time', 8.0)} s"
                    )
                },
                node_type="input",
                source_position="right",
                draggable=True
            ),
            StreamlitFlowNode(
                id="summe_stoerung",
                pos=(620, 190),
                data={"content": "Σ<br>u + d"},
                node_type="default",
                source_position="right",
                target_position="left",
                draggable=True
            ),
        ])
        edges.extend([
            StreamlitFlowEdge(id="b7", source="regler", target="summe_stoerung", animated=True, label="u"),
            StreamlitFlowEdge(id="b8", source="stoerung", target="summe_stoerung", animated=True, label="d"),
            StreamlitFlowEdge(id="b9", source="summe_stoerung", target="strecke", animated=True, label="u+d"),
        ])

    elif disturbance_position == "Am Ausgang":
        edges = [edge for edge in edges if edge.id != "b4"]
        nodes.extend([
            StreamlitFlowNode(
                id="stoerung",
                pos=(890, 25),
                data={
                    "content": (
                        f"Störung d(t)<br>d={config.get('disturbance_value', -0.3)}<br>"
                        f"ab {config.get('disturbance_time', 8.0)} s"
                    )
                },
                node_type="input",
                source_position="right",
                draggable=True
            ),
            StreamlitFlowNode(
                id="summe_ausgang",
                pos=(900, 190),
                data={"content": "Σ<br>y + d"},
                node_type="default",
                source_position="right",
                target_position="left",
                draggable=True
            ),
        ])
        edges.extend([
            StreamlitFlowEdge(id="b10", source="strecke", target="summe_ausgang", animated=True, label="y"),
            StreamlitFlowEdge(id="b11", source="stoerung", target="summe_ausgang", animated=True, label="d"),
            StreamlitFlowEdge(id="b12", source="summe_ausgang", target="ausgang", animated=True, label="y+d"),
        ])

    return StreamlitFlowState(nodes, edges)


def render_builder_step_header(step: int):
    steps = [
        "Regelaufgabe",
        "Regler",
        "Strecke",
        "Rückführung & Störung",
        "Prüfen & übernehmen",
    ]
    st.progress(step / len(steps))
    st.caption(f"Engineering-Schritt {step} von {len(steps)} · {steps[step - 1]}")


def render_visual_builder():
    """
    Geführter visueller Regelkreis-Builder.
    Die Oberfläche zeigt immer nur die Angaben, die im aktuellen Engineering-Schritt benötigt werden.
    """
    config = st.session_state.builder_config
    step = int(st.session_state.builder_step)

    st.title("Visueller Regelkreis-Builder")
    st.caption(
        "Der Baukasten führt dich Schritt für Schritt vom Regelungsziel bis zum geprüften geschlossenen Regelkreis. "
        "Die Arbeitsfläche wächst dabei mit – so bleibt der Aufbau übersichtlich."
    )

    render_builder_step_header(step)

    col_work, col_canvas = st.columns([1, 2.15], gap="large")

    with col_work:
        # ----------------------------------------------------
        # Schritt 1: Regelaufgabe
        # ----------------------------------------------------
        if step == 1:
            st.subheader("1. Regelaufgabe festlegen")
            st.write(
                "Bevor ein Regler gewählt wird, wird festgelegt, **welche Größe auf welchen Sollwert geregelt werden soll**."
            )

            config["setpoint_name"] = st.text_input(
                "Bezeichnung der Führungsgröße",
                value=config.get("setpoint_name", "Sollwert w(t)"),
                key="guided_setpoint_name",
                help="Zum Beispiel: Solltemperatur, Solldrehzahl oder Sollfüllstand."
            )

            config["output_name"] = st.text_input(
                "Bezeichnung der Regelgröße",
                value=config.get("output_name", "Regelgröße y(t)"),
                key="guided_output_name",
                help="Die physikalische Größe, die dem Sollwert folgen soll."
            )

            config["setpoint"] = st.number_input(
                "Sollwert w",
                value=float(config.get("setpoint", 1.0)),
                step=0.1,
                key="guided_setpoint",
                help="Für die normierte Simulation kann 1,0 verwendet werden."
            )

            with st.expander("Warum beginnt der Engineering-Prozess hier?", expanded=False):
                st.write(
                    "Eine Regelung wird aus der gewünschten Aufgabe heraus entwickelt. Erst wenn Führungsgröße und "
                    "Regelgröße bekannt sind, ist klar, was der Regler später erreichen soll."
                )

        # ----------------------------------------------------
        # Schritt 2: Regler
        # ----------------------------------------------------
        elif step == 2:
            st.subheader("2. Regler auswählen")
            st.write("Wähle den Reglerbaustein. Es werden nur die zu diesem Regler gehörenden Parameter eingeblendet.")

            config["controller_type"] = st.radio(
                "Reglerbaustein",
                ["P", "PI", "PID"],
                index=["P", "PI", "PID"].index(config.get("controller_type", "PI")),
                horizontal=True,
                key="guided_controller_type"
            )

            config["kp"] = st.number_input(
                "Kp – Proportionalverstärkung",
                min_value=0.0,
                max_value=100.0,
                value=float(config.get("kp", 2.0)),
                step=0.1,
                key="guided_kp",
                help="Bestimmt die unmittelbare Reaktion des Reglers auf die Regeldifferenz."
            )

            if config["controller_type"] in ["PI", "PID"]:
                config["ki"] = st.number_input(
                    "Ki – Integralverstärkung",
                    min_value=0.0,
                    max_value=100.0,
                    value=float(config.get("ki", 0.5)),
                    step=0.1,
                    key="guided_ki",
                    help="Hilft dabei, eine bleibende Regelabweichung abzubauen."
                )
            else:
                config["ki"] = 0.0

            if config["controller_type"] == "PID":
                config["kd"] = st.number_input(
                    "Kd – Differentialverstärkung",
                    min_value=0.0,
                    max_value=100.0,
                    value=float(config.get("kd", 0.2)),
                    step=0.1,
                    key="guided_kd",
                    help="Reagiert auf schnelle Änderungen und kann Überschwingen dämpfen."
                )
            else:
                config["kd"] = 0.0

            with st.expander("Auswahlhilfe P / PI / PID", expanded=False):
                st.markdown(
                    """
                    **P:** einfach und schnell, kann aber eine bleibende Regelabweichung hinterlassen.  
                    **PI:** sehr häufig in der Prozess- und Gebäudeautomation; beseitigt stationäre Abweichungen.  
                    **PID:** zusätzliche D-Wirkung für dynamische oder schwingfähige Systeme.
                    """
                )

        # ----------------------------------------------------
        # Schritt 3: Strecke
        # ----------------------------------------------------
        elif step == 3:
            st.subheader("3. Regelstrecke modellieren")
            st.write("Jetzt wird das dynamische Verhalten der Strecke als regelungstechnischer Baustein beschrieben.")

            config["plant_type"] = st.radio(
                "Streckenbaustein",
                ["PT1", "PT2"],
                index=["PT1", "PT2"].index(config.get("plant_type", "PT1")),
                horizontal=True,
                key="guided_plant_type"
            )

            config["ks"] = st.number_input(
                "Ks – Streckenverstärkung",
                min_value=0.1,
                max_value=100.0,
                value=float(config.get("ks", 1.0)),
                step=0.1,
                key="guided_ks"
            )

            if config["plant_type"] == "PT1":
                config["ts"] = st.number_input(
                    "Ts – Zeitkonstante [s]",
                    min_value=0.1,
                    max_value=100.0,
                    value=float(config.get("ts", 2.0)),
                    step=0.1,
                    key="guided_ts",
                    help="Je größer Ts ist, desto träger reagiert die PT1-Strecke."
                )
                config["zeta"] = 0.7
                config["omega0"] = 2.0
            else:
                config["zeta"] = st.number_input(
                    "ζ – Dämpfung",
                    min_value=0.05,
                    max_value=5.0,
                    value=float(config.get("zeta", 0.7)),
                    step=0.05,
                    key="guided_zeta"
                )
                config["omega0"] = st.number_input(
                    "ω0 – Eigenkreisfrequenz [rad/s]",
                    min_value=0.1,
                    max_value=100.0,
                    value=float(config.get("omega0", 2.0)),
                    step=0.1,
                    key="guided_omega0"
                )
                config["ts"] = 2.0

            with st.expander("Auswahlhilfe PT1 / PT2", expanded=False):
                st.markdown(
                    """
                    **PT1:** typische träge Ausgleichsstrecke, z. B. viele Temperatur-, Druck- oder Drehzahlprozesse.  
                    **PT2:** geeignet für Systeme zweiter Ordnung, bei denen Dämpfung und Schwingverhalten eine Rolle spielen.
                    """
                )

        # ----------------------------------------------------
        # Schritt 4: Rückführung & Störung
        # ----------------------------------------------------
        elif step == 4:
            st.subheader("4. Regelkreis schließen")
            st.write(
                "Die Regelgröße wird als Istwert zurückgeführt. Optional kannst du jetzt einen Störeinfluss ergänzen."
            )

            st.success("Rückführung: y(t) wird automatisch negativ auf die Vergleichsstelle zurückgeführt.")

            config["disturbance_position"] = st.selectbox(
                "Störungsbaustein",
                ["Keine Störung", "Vor der Strecke", "Am Ausgang"],
                index=["Keine Störung", "Vor der Strecke", "Am Ausgang"].index(
                    config.get("disturbance_position", "Keine Störung")
                ),
                key="guided_disturbance_position"
            )

            if config["disturbance_position"] != "Keine Störung":
                config["disturbance_time"] = st.number_input(
                    "Störung ab [s]",
                    min_value=0.0,
                    max_value=200.0,
                    value=float(config.get("disturbance_time", 8.0)),
                    step=0.5,
                    key="guided_disturbance_time"
                )
                config["disturbance_value"] = st.number_input(
                    "Störgröße d",
                    value=float(config.get("disturbance_value", -0.3)),
                    step=0.1,
                    key="guided_disturbance_value"
                )
            else:
                config["disturbance_time"] = 0.0
                config["disturbance_value"] = 0.0

            with st.expander("Wo kann eine Störung wirken?", expanded=False):
                st.markdown(
                    """
                    **Vor der Strecke:** typische Last- oder Prozesseinwirkung auf den Streckeneingang.  
                    **Am Ausgang:** direkte Beeinflussung der Regelgröße.  
                    Ohne Störung wird zunächst nur das Führungsverhalten untersucht.
                    """
                )

        # ----------------------------------------------------
        # Schritt 5: Prüfung & Simulation
        # ----------------------------------------------------
        else:
            st.subheader("5. Aufbau prüfen und übernehmen")
            st.write("Zum Abschluss werden Simulationsparameter festgelegt und der entstandene Regelkreis automatisch geprüft.")

            config["t_end"] = st.number_input(
                "Simulationsdauer [s]",
                min_value=1.0,
                max_value=200.0,
                value=float(config.get("t_end", 20.0)),
                step=1.0,
                key="guided_t_end"
            )

            config["dt"] = st.number_input(
                "Schrittweite dt [s]",
                min_value=0.001,
                max_value=1.0,
                value=float(config.get("dt", 0.01)),
                step=0.001,
                format="%.3f",
                key="guided_dt"
            )

            errors, warnings = validate_guided_builder(config)
            st.session_state.builder_last_validation = {"errors": errors, "warnings": warnings}

            if errors:
                st.error("Der Regelkreis ist noch nicht simulationsfähig.")
                for item in errors:
                    st.write(f"- {item}")
            else:
                st.success("Regelkreis vollständig und simulationsfähig.")

            for item in warnings:
                st.warning(item)

            with st.expander("Zusammenfassung des Engineering-Aufbaus", expanded=True):
                st.write(f"**Führungsgröße:** {config.get('setpoint_name', 'Sollwert w(t)')} = {config.get('setpoint', 1.0)}")
                st.write(f"**Regelgröße:** {config.get('output_name', 'Regelgröße y(t)')}")
                st.write(f"**Regler:** {config.get('controller_type')} · Kp={config.get('kp')} · Ki={config.get('ki')} · Kd={config.get('kd')}")
                if config.get("plant_type") == "PT1":
                    st.write(f"**Strecke:** PT1 · Ks={config.get('ks')} · Ts={config.get('ts')} s")
                else:
                    st.write(f"**Strecke:** PT2 · Ks={config.get('ks')} · ζ={config.get('zeta')} · ω0={config.get('omega0')} rad/s")
                st.write(f"**Störung:** {config.get('disturbance_position')}")

            if not errors:
                if st.button("Regelkreis in Simulation übernehmen", type="primary", width="stretch"):
                    st.session_state.controller_type = config["controller_type"]
                    st.session_state.plant_type = config["plant_type"]
                    st.session_state.disturbance_position = config["disturbance_position"]
                    st.session_state.defaults = {
                        "kp": float(config["kp"]),
                        "ki": float(config["ki"]),
                        "kd": float(config["kd"]),
                        "ks": float(config["ks"]),
                        "ts": float(config["ts"]),
                        "zeta": float(config["zeta"]),
                        "omega0": float(config["omega0"]),
                        "setpoint": float(config["setpoint"]),
                        "t_end": float(config["t_end"]),
                        "dt": float(config["dt"]),
                        "disturbance_time": float(config["disturbance_time"]),
                        "disturbance_value": float(config["disturbance_value"]),
                    }
                    st.session_state.builder_config = config.copy()
                    st.session_state.active_view = "simulation"
                    st.rerun()

        st.session_state.builder_config = config

        # ----------------------------------------------------
        # Schritt-Navigation
        # ----------------------------------------------------
        st.divider()
        nav_back, nav_next = st.columns(2)

        with nav_back:
            if step > 1:
                if st.button("Zurück", width="stretch"):
                    st.session_state.builder_step = step - 1
                    st.rerun()

        with nav_next:
            if step < 5:
                if st.button("Weiter", type="primary", width="stretch"):
                    st.session_state.builder_step = step + 1
                    st.rerun()

        if st.button("Neuen Aufbau starten", width="stretch"):
            reset_guided_builder()
            st.rerun()

    with col_canvas:
        st.subheader("Arbeitsfläche")

        flow_state = build_guided_flow(config, step)

        streamlit_flow(
            "guided_visual_builder_flow",
            flow_state,
            fit_view=False,
            show_minimap=False,
            show_controls=True,
            allow_new_edges=False,
            animate_new_edges=False,
            height=610
        )

        st.caption(
            "Die Bausteine können auf der Arbeitsfläche verschoben werden. "
            "Neue Elemente erscheinen jeweils dann, wenn sie im Engineering-Prozess benötigt werden."
        )

        if step < 5:
            next_text = {
                1: "Als Nächstes wird der Reglerbaustein ausgewählt.",
                2: "Als Nächstes wird die dynamische Strecke modelliert.",
                3: "Als Nächstes wird der Regelkreis geschlossen und optional eine Störung ergänzt.",
                4: "Als Nächstes wird der fertige Aufbau geprüft und in die Simulation übernommen.",
            }
            st.info(next_text[step])

# ------------------------------------------------------------
# Physikalischer Wirkplan-Builder
# ------------------------------------------------------------

def derive_controller_from_wirkplan(config: dict):
    prozessart = config["prozessart"]
    traegheit = config["traegheit"]
    ueberschwingen_zulaessig = config["ueberschwingen_zulaessig"]
    bleibende_abweichung_erlaubt = config["bleibende_abweichung_erlaubt"]
    stoerungen_relevant = config["stoerungen_relevant"]

    result = {
        "controller_type": "PI",
        "plant_type": "PT1",
        "kp": 2.0,
        "ki": 0.4,
        "kd": 0.0,
        "ks": 1.0,
        "ts": 3.0,
        "zeta": 0.7,
        "omega0": 2.0,
        "setpoint": 1.0,
        "t_end": 25.0,
        "dt": 0.01,
        "disturbance_time": 10.0,
        "disturbance_value": -0.3,
        "disturbance_position": "Keine Störung",
        "begruendung": [],
    }

    if prozessart == "Temperaturregelung":
        result["plant_type"] = "PT1"
        result["controller_type"] = "PI"
        result["kp"] = 1.8
        result["ki"] = 0.25
        result["kd"] = 0.0
        result["ts"] = 8.0
        result["t_end"] = 50.0
        result["begruendung"].append(
            "Temperaturstrecken sind meistens träge PT1-ähnliche Strecken mit thermischer Speichermasse."
        )
        result["begruendung"].append(
            "Ein PI-Regler ist sinnvoll, weil ein reiner P-Regler häufig eine bleibende Temperaturabweichung hinterlässt."
        )

    elif prozessart == "Drehzahlregelung":
        result["plant_type"] = "PT1"
        result["controller_type"] = "PI"
        result["kp"] = 2.5
        result["ki"] = 0.7
        result["kd"] = 0.0
        result["ts"] = 2.0
        result["t_end"] = 20.0
        result["begruendung"].append(
            "Drehzahlstrecken besitzen mechanische Trägheit und lassen sich vereinfacht oft als PT1-Strecke betrachten."
        )
        result["begruendung"].append(
            "Ein PI-Regler reduziert die bleibende Drehzahlabweichung bei Laständerungen."
        )

    elif prozessart == "Füllstandsregelung":
        result["plant_type"] = "PT1"
        result["controller_type"] = "PI"
        result["kp"] = 1.5
        result["ki"] = 0.25
        result["kd"] = 0.0
        result["ts"] = 10.0
        result["t_end"] = 60.0
        result["begruendung"].append(
            "Füllstandsprozesse reagieren meist träge und besitzen ein speicherndes Verhalten."
        )
        result["begruendung"].append(
            "Ein PI-Regler ist geeignet, um den Füllstand trotz Zu- oder Abflussstörungen auf Sollwert zu bringen."
        )

    elif prozessart == "Druckregelung":
        result["plant_type"] = "PT1"
        result["controller_type"] = "PI"
        result["kp"] = 2.0
        result["ki"] = 0.5
        result["kd"] = 0.0
        result["ts"] = 3.0
        result["t_end"] = 25.0
        result["begruendung"].append(
            "Druckregelungen verhalten sich häufig wie mittelträge PT1-Strecken."
        )
        result["begruendung"].append(
            "Ein PI-Regler kann stationäre Druckabweichungen infolge von Verbrauch oder Leckage ausregeln."
        )

    elif prozessart == "Durchflussregelung":
        result["plant_type"] = "PT1"
        result["controller_type"] = "P"
        result["kp"] = 1.5
        result["ki"] = 0.0
        result["kd"] = 0.0
        result["ts"] = 1.0
        result["t_end"] = 12.0
        result["begruendung"].append(
            "Durchflussstrecken sind oft vergleichsweise schnell."
        )
        result["begruendung"].append(
            "Für einfache Betrachtungen kann ein P-Regler ausreichend sein; bei stationärer Abweichung ist PI sinnvoll."
        )

    elif prozessart == "Position / Mechanik":
        result["plant_type"] = "PT2"
        result["controller_type"] = "PID"
        result["kp"] = 3.0
        result["ki"] = 0.4
        result["kd"] = 0.4
        result["zeta"] = 0.55
        result["omega0"] = 2.2
        result["t_end"] = 20.0
        result["begruendung"].append(
            "Mechanische Positionssysteme können schwingfähig sein und werden deshalb vereinfacht als PT2-Strecke abgebildet."
        )
        result["begruendung"].append(
            "Ein PID-Regler kann Überschwingen dämpfen und gleichzeitig stationäre Abweichungen verringern."
        )

    if traegheit == "sehr träge":
        result["ts"] *= 1.8
        result["t_end"] *= 1.5
        result["kp"] *= 0.8
        result["ki"] *= 0.7
        result["begruendung"].append(
            "Da der Prozess als sehr träge bewertet wurde, werden die Startparameter vorsichtiger gewählt."
        )

    elif traegheit == "schnell":
        result["ts"] *= 0.5
        result["t_end"] *= 0.7
        result["kp"] *= 1.2
        result["ki"] *= 1.1
        result["begruendung"].append(
            "Da der Prozess als schnell bewertet wurde, wird eine kürzere Zeitkonstante angesetzt."
        )

    if bleibende_abweichung_erlaubt == "Nein":
        if result["controller_type"] == "P":
            result["controller_type"] = "PI"
            result["ki"] = 0.35
        result["begruendung"].append(
            "Da keine bleibende Regelabweichung erlaubt ist, wird mindestens ein PI-Regler empfohlen."
        )

    if ueberschwingen_zulaessig == "Nein":
        result["kp"] *= 0.8
        result["ki"] *= 0.8
        if result["controller_type"] == "PID":
            result["kd"] *= 1.2
        result["begruendung"].append(
            "Da Überschwingen nicht zulässig ist, werden die Reglerparameter defensiver gewählt."
        )

    if stoerungen_relevant == "Ja":
        result["disturbance_position"] = "Vor der Strecke"
        result["disturbance_time"] = min(10.0, result["t_end"] / 2)
        result["disturbance_value"] = -0.3
        result["begruendung"].append(
            "Da relevante Störungen auftreten, wird eine Laststörung vor der Strecke für die Simulation vorgeschlagen."
        )
    else:
        result["disturbance_position"] = "Keine Störung"
        result["disturbance_time"] = 0.0
        result["disturbance_value"] = 0.0

    result["kp"] = round(float(result["kp"]), 3)
    result["ki"] = round(float(result["ki"]), 3)
    result["kd"] = round(float(result["kd"]), 3)
    result["ts"] = round(float(result["ts"]), 3)
    result["t_end"] = round(float(result["t_end"]), 3)

    return result


def build_wirkplan_flow(config: dict):
    nodes = [
        StreamlitFlowNode(
            id="stellgroesse",
            pos=(0, 180),
            data={"content": f"Stellgröße<br>{config['stellgroesse']}"},
            node_type="input",
            source_position="right",
            draggable=True
        ),
        StreamlitFlowNode(
            id="prozessglied",
            pos=(280, 180),
            data={"content": f"Prozessglied<br>{config['prozessglied']}"},
            node_type="default",
            source_position="right",
            target_position="left",
            draggable=True
        ),
        StreamlitFlowNode(
            id="speicher",
            pos=(580, 180),
            data={"content": f"Speicher / Trägheit<br>{config['speicher']}"},
            node_type="default",
            source_position="right",
            target_position="left",
            draggable=True
        ),
        StreamlitFlowNode(
            id="regelgroesse",
            pos=(880, 180),
            data={"content": f"Regelgröße<br>{config['regelgroesse']}"},
            node_type="output",
            target_position="left",
            draggable=True
        ),
    ]

    edges = [
        StreamlitFlowEdge(
            id="w1",
            source="stellgroesse",
            target="prozessglied",
            animated=True,
            label="wirkt auf"
        ),
        StreamlitFlowEdge(
            id="w2",
            source="prozessglied",
            target="speicher",
            animated=True,
            label="Energie / Stoff"
        ),
        StreamlitFlowEdge(
            id="w3",
            source="speicher",
            target="regelgroesse",
            animated=True,
            label="Messgröße"
        ),
    ]

    if config["stoerungen_relevant"] == "Ja":
        nodes.append(
            StreamlitFlowNode(
                id="stoerung",
                pos=(580, 30),
                data={"content": f"Störgröße<br>{config['stoergroesse']}"},
                node_type="input",
                source_position="right",
                draggable=True
            )
        )

        edges.append(
            StreamlitFlowEdge(
                id="w4",
                source="stoerung",
                target="speicher",
                animated=True,
                label="Störeinfluss"
            )
        )

    return StreamlitFlowState(nodes, edges)


def update_wirkplan_defaults_for_process(config: dict):
    """Aktualisiert Prozess-Presets und synchronisiert zugleich die sichtbaren Widgets."""
    prozessart = config["prozessart"]

    presets = {
        "Temperaturregelung": {
            "stellgroesse": "Heizleistung P [W]",
            "prozessglied": "Heizkörper / Wärmeerzeuger",
            "speicher": "thermische Masse des Raums",
            "regelgroesse": "Raumtemperatur T [°C]",
            "stoergroesse": "Außentemperatur / geöffnete Tür",
            "traegheit": "sehr träge",
            "ueberschwingen_zulaessig": "Nein",
            "bleibende_abweichung_erlaubt": "Nein",
            "stoerungen_relevant": "Ja",
        },
        "Drehzahlregelung": {
            "stellgroesse": "Motorspannung U [V]",
            "prozessglied": "Motor / Umrichter",
            "speicher": "mechanische Trägheit J",
            "regelgroesse": "Drehzahl n [1/min]",
            "stoergroesse": "Lastmoment M_L",
            "traegheit": "mittel",
            "ueberschwingen_zulaessig": "Ja",
            "bleibende_abweichung_erlaubt": "Nein",
            "stoerungen_relevant": "Ja",
        },
        "Füllstandsregelung": {
            "stellgroesse": "Ventilöffnung [%]",
            "prozessglied": "Zulaufventil / Pumpe",
            "speicher": "Behältervolumen",
            "regelgroesse": "Füllstand h [m]",
            "stoergroesse": "Abfluss / Verbrauch",
            "traegheit": "sehr träge",
            "ueberschwingen_zulaessig": "Nein",
            "bleibende_abweichung_erlaubt": "Nein",
            "stoerungen_relevant": "Ja",
        },
        "Druckregelung": {
            "stellgroesse": "Pumpendrehzahl / Ventilstellung",
            "prozessglied": "Pumpe / Rohrnetz",
            "speicher": "Kompressibilität / Leitungsvolumen",
            "regelgroesse": "Druck p [bar]",
            "stoergroesse": "Verbrauch / Leckage",
            "traegheit": "mittel",
            "ueberschwingen_zulaessig": "Nein",
            "bleibende_abweichung_erlaubt": "Nein",
            "stoerungen_relevant": "Ja",
        },
        "Durchflussregelung": {
            "stellgroesse": "Ventilöffnung [%]",
            "prozessglied": "Ventil / Rohrstrecke",
            "speicher": "geringe Prozessspeicherung",
            "regelgroesse": "Durchfluss q [m³/h]",
            "stoergroesse": "Vordruckschwankung",
            "traegheit": "schnell",
            "ueberschwingen_zulaessig": "Ja",
            "bleibende_abweichung_erlaubt": "Ja",
            "stoerungen_relevant": "Nein",
        },
        "Position / Mechanik": {
            "stellgroesse": "Motorspannung / Stellmoment",
            "prozessglied": "Antrieb / Mechanik",
            "speicher": "Masse, Feder, Trägheit",
            "regelgroesse": "Position x [mm]",
            "stoergroesse": "Lastkraft / Reibung",
            "traegheit": "mittel",
            "ueberschwingen_zulaessig": "Nein",
            "bleibende_abweichung_erlaubt": "Nein",
            "stoerungen_relevant": "Ja",
        },
    }

    if prozessart in presets:
        widget_keys = {
            "stellgroesse": "wirkplan_stellgroesse",
            "prozessglied": "wirkplan_prozessglied",
            "speicher": "wirkplan_speicher",
            "regelgroesse": "wirkplan_regelgroesse",
            "stoergroesse": "wirkplan_stoergroesse",
            "traegheit": "wirkplan_traegheit",
            "ueberschwingen_zulaessig": "wirkplan_ueberschwingen",
            "bleibende_abweichung_erlaubt": "wirkplan_abweichung",
            "stoerungen_relevant": "wirkplan_stoerungen",
        }

        for key, value in presets[prozessart].items():
            config[key] = value
            widget_key = widget_keys.get(key)
            if widget_key is not None:
                st.session_state[widget_key] = value

    return config


def render_wirkplan_builder():
    st.title("Physikalischer Wirkplan-Builder")

    st.caption(
        "Hier startest du nicht mit Regler und Strecke, sondern mit physikalischen Größen. "
        "Aus dem Wirkplan leitet die App ein geeignetes Streckenmodell und einen Startregler ab."
    )

    config = st.session_state.wirkplan_config

    col_left, col_right = st.columns([1, 2])

    with col_left:
        st.subheader("Physikalische Angaben")

        alte_prozessart = config["prozessart"]

        config["prozessart"] = st.selectbox(
            "Prozessart",
            [
                "Temperaturregelung",
                "Drehzahlregelung",
                "Füllstandsregelung",
                "Druckregelung",
                "Durchflussregelung",
                "Position / Mechanik"
            ],
            index=[
                "Temperaturregelung",
                "Drehzahlregelung",
                "Füllstandsregelung",
                "Druckregelung",
                "Durchflussregelung",
                "Position / Mechanik"
            ].index(config["prozessart"]),
            key="wirkplan_prozessart"
        )

        if config["prozessart"] != alte_prozessart:
            config = update_wirkplan_defaults_for_process(config)
            st.session_state.wirkplan_config = config
            st.rerun()

        with st.expander("1. Physikalische Wirkungskette", expanded=True):
            config["stellgroesse"] = st.text_input(
                "Stellgröße",
                value=config["stellgroesse"],
                key="wirkplan_stellgroesse"
            )

            config["prozessglied"] = st.text_input(
                "Prozessglied",
                value=config["prozessglied"],
                key="wirkplan_prozessglied"
            )

            config["speicher"] = st.text_input(
                "Speicher / Trägheit",
                value=config["speicher"],
                key="wirkplan_speicher"
            )

            config["regelgroesse"] = st.text_input(
                "Regelgröße",
                value=config["regelgroesse"],
                key="wirkplan_regelgroesse"
            )

        with st.expander("2. Verhalten des Prozesses", expanded=True):
            config["traegheit"] = st.selectbox(
                "Wie träge ist der Prozess?",
                ["schnell", "mittel", "träge", "sehr träge"],
                index=["schnell", "mittel", "träge", "sehr träge"].index(config["traegheit"]),
                key="wirkplan_traegheit"
            )

            config["ueberschwingen_zulaessig"] = st.selectbox(
                "Ist Überschwingen zulässig?",
                ["Ja", "Nein"],
                index=["Ja", "Nein"].index(config["ueberschwingen_zulaessig"]),
                key="wirkplan_ueberschwingen"
            )

            config["bleibende_abweichung_erlaubt"] = st.selectbox(
                "Ist eine bleibende Regelabweichung erlaubt?",
                ["Ja", "Nein"],
                index=["Ja", "Nein"].index(config["bleibende_abweichung_erlaubt"]),
                key="wirkplan_abweichung"
            )

        with st.expander("3. Störeinflüsse", expanded=True):
            config["stoerungen_relevant"] = st.selectbox(
                "Gibt es relevante Störungen?",
                ["Ja", "Nein"],
                index=["Ja", "Nein"].index(config["stoerungen_relevant"]),
                key="wirkplan_stoerungen"
            )

            if config["stoerungen_relevant"] == "Ja":
                config["stoergroesse"] = st.text_input(
                    "Störgröße",
                    value=config["stoergroesse"],
                    key="wirkplan_stoergroesse"
                )
            else:
                config["stoergroesse"] = "keine relevante Störung"

        st.session_state.wirkplan_config = config

        derived = derive_controller_from_wirkplan(config)

        st.divider()

        st.subheader("Abgeleiteter Regler")

        st.write(f"**Empfohlene Strecke:** {derived['plant_type']}")
        st.write(f"**Empfohlener Regler:** {derived['controller_type']}")

        st.write("**Startparameter:**")
        st.write(f"- Kp = {derived['kp']}")
        st.write(f"- Ki = {derived['ki']}")
        st.write(f"- Kd = {derived['kd']}")
        st.write(f"- Ks = {derived['ks']}")
        st.write(f"- Ts = {derived['ts']}")
        st.write(f"- ζ = {derived['zeta']}")
        st.write(f"- ω0 = {derived['omega0']}")

        if st.button("Wirkplan übernehmen und Simulation berechnen", type="primary"):
            st.session_state.controller_type = derived["controller_type"]
            st.session_state.plant_type = derived["plant_type"]
            st.session_state.disturbance_position = derived["disturbance_position"]

            st.session_state.defaults = {
                "kp": derived["kp"],
                "ki": derived["ki"],
                "kd": derived["kd"],
                "ks": derived["ks"],
                "ts": derived["ts"],
                "zeta": derived["zeta"],
                "omega0": derived["omega0"],
                "setpoint": derived["setpoint"],
                "t_end": derived["t_end"],
                "dt": derived["dt"],
                "disturbance_time": derived["disturbance_time"],
                "disturbance_value": derived["disturbance_value"],
            }

            st.session_state.builder_config = st.session_state.defaults.copy()
            st.session_state.builder_config["controller_type"] = derived["controller_type"]
            st.session_state.builder_config["plant_type"] = derived["plant_type"]
            st.session_state.builder_config["disturbance_position"] = derived["disturbance_position"]

            st.session_state.active_view = "simulation"
            st.rerun()

    with col_right:
        st.subheader("Grafischer Wirkplan")

        flow_state = build_wirkplan_flow(config)

        streamlit_flow(
            "wirkplan_flow",
            flow_state,
            fit_view=False,
            show_minimap=True,
            show_controls=True,
            allow_new_edges=False,
            animate_new_edges=False,
            height=500
        )

        derived = derive_controller_from_wirkplan(config)

        st.subheader("Begründung der Ableitung")

        for begruendung in derived["begruendung"]:
            st.write("- " + begruendung)

        with st.expander("Aktueller Wirkplan-Datensatz"):
            st.json(config)

        with st.expander("Abgeleitete Simulationsdaten"):
            st.json(derived)


# ------------------------------------------------------------
# Ansichten abfangen
# ------------------------------------------------------------

if st.session_state.active_view == "builder":
    render_visual_builder()
    st.stop()

if st.session_state.active_view == "wirkplan":
    render_wirkplan_builder()
    st.stop()


# ------------------------------------------------------------
# Oberfläche Simulation
# ------------------------------------------------------------

st.title("Regelkreis-Labor")

st.caption(
    "Interaktive Simulation eines geschlossenen Regelkreises mit Regler, "
    "Strecke, Rückführung und optionaler Störung."
)


# ------------------------------------------------------------
# Sidebar nur mit vier Optionsgruppen
# ------------------------------------------------------------

defaults = st.session_state.defaults

with st.sidebar:

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
# Automatisches Blockschaltbild
# ------------------------------------------------------------

st.subheader("Vervollständigter Regelkreis")

st.graphviz_chart(
    blockdiagramm(controller_type, plant_type, disturbance_position),
    width="stretch"
)


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
    st.dataframe(df, width="stretch")


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
