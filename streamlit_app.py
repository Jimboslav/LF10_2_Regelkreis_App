import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Regelkreis-Labor", layout="wide")

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

    # Grundwerte
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
        defaults["zeta"] = 0.7       # nicht relevant, aber intern gefüllt
        defaults["omega0"] = 2.0     # nicht relevant, aber intern gefüllt

    elif plant_type == "PT2":
        defaults["ts"] = 2.0         # nicht relevant, aber intern gefüllt
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
    """Erzeugt ein DOT-Diagramm für st.graphviz_chart."""
    disturbance_label = "Störung d(t)"

    if disturbance_position == "Keine Störung":
        disturbance_part = ""
        input_to_plant = "regler -> strecke"
        output_label = "strecke -> ausgang"

    elif disturbance_position == "Vor der Strecke":
        disturbance_part = f'''
        dist [label="{disturbance_label}", shape=ellipse, style=dashed];
        summ2 [label="Σ", shape=circle];
        regler -> summ2;
        dist -> summ2;
        summ2 -> strecke;
        '''
        input_to_plant = ""
        output_label = "strecke -> ausgang"

    else:
        disturbance_part = f'''
        dist [label="{disturbance_label}", shape=ellipse, style=dashed];
        summ3 [label="Σ", shape=circle];
        strecke -> summ3;
        dist -> summ3;
        summ3 -> ausgang;
        '''
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
    """Numerische Simulation eines geschlossenen Regelkreises.

    PT1: T_s * dy/dt + y = K_s * u
    PT2: y'' + 2*zeta*omega0*y' + omega0^2*y = K_s*omega0^2*u
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
    """Berechnet einfache Kennwerte aus der Simulation."""

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
# Oberfläche
# ------------------------------------------------------------

st.title("Regelkreis-Labor")

st.caption(
    "Interaktive Simulation eines geschlossenen Regelkreises mit Regler, "
    "Strecke, Rückführung und optionaler Störung."
)


# ------------------------------------------------------------
# Sidebar: Eingaben
# ------------------------------------------------------------

with st.sidebar:
    st.header("1. Regelkreis aufbauen")

    controller_type = st.selectbox(
        "Reglertyp",
        ["P", "PI", "PID"],
        index=1
    )

    plant_type = st.selectbox(
        "Streckentyp",
        ["PT1", "PT2"],
        index=0
    )

    disturbance_position = st.selectbox(
        "Störung platzieren",
        ["Keine Störung", "Vor der Strecke", "Am Ausgang"],
        index=0
    )

    st.header("2. Reglerparameter")

    kp = st.number_input(
        "Kp - Proportionalverstärkung",
        min_value=0.0,
        max_value=100.0,
        value=2.0,
        step=0.1
    )

    ki = st.number_input(
        "Ki - Integralverstärkung",
        min_value=0.0,
        max_value=100.0,
        value=0.5,
        step=0.1,
        disabled=controller_type == "P"
    )

    kd = st.number_input(
        "Kd - Differentialverstärkung",
        min_value=0.0,
        max_value=100.0,
        value=0.0,
        step=0.1,
        disabled=controller_type != "PID"
    )

    st.header("3. Streckenparameter")

    ks = st.number_input(
        "Ks - Streckenverstärkung",
        min_value=0.1,
        max_value=100.0,
        value=1.0,
        step=0.1
    )

    ts = st.number_input(
        "Ts - Zeitkonstante PT1 [s]",
        min_value=0.1,
        max_value=100.0,
        value=2.0,
        step=0.1,
        disabled=plant_type != "PT1"
    )

    zeta = st.number_input(
        "Dämpfung ζ PT2",
        min_value=0.05,
        max_value=5.0,
        value=0.7,
        step=0.05,
        disabled=plant_type != "PT2"
    )

    omega0 = st.number_input(
        "Eigenkreisfrequenz ω0 PT2 [rad/s]",
        min_value=0.1,
        max_value=100.0,
        value=2.0,
        step=0.1,
        disabled=plant_type != "PT2"
    )

    st.header("4. Simulation")

    setpoint = st.number_input(
        "Sollwert w",
        value=1.0,
        step=0.1
    )

    t_end = st.number_input(
        "Simulationsdauer [s]",
        min_value=1.0,
        max_value=200.0,
        value=20.0,
        step=1.0
    )

    dt = st.number_input(
        "Schrittweite dt [s]",
        min_value=0.001,
        max_value=1.0,
        value=0.01,
        step=0.001,
        format="%.3f"
    )

    disturbance_time = st.number_input(
        "Störung ab Zeitpunkt [s]",
        min_value=0.0,
        max_value=200.0,
        value=8.0,
        step=0.5,
        disabled=disturbance_position == "Keine Störung"
    )

    disturbance_value = st.number_input(
        "Störgröße d",
        value=-0.3,
        step=0.1,
        disabled=disturbance_position == "Keine Störung"
    )


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
# Regelkreis grafisch anzeigen
# ------------------------------------------------------------

st.subheader("Vervollständigter Regelkreis")

st.graphviz_chart(
    blockdiagramm(controller_type, plant_type, disturbance_position),
    use_container_width=True
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
