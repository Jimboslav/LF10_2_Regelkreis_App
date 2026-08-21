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


# ------------------------------------------------------------
# Robuste Standardwerte für Session-State
# ------------------------------------------------------------
# Diese Werte werden benötigt, wenn der Benutzer z. B. direkt über die
# obere Navigation in den Builder wechselt und anschließend in die
# Simulation zurückkehrt, ohne das Startformular erneut abzusenden.

if "lernziel" not in st.session_state:
    st.session_state.lernziel = "Grundverhalten verstehen"

if "schwierigkeitsgrad" not in st.session_state:
    st.session_state.schwierigkeitsgrad = "Fortgeschritten"

if "controller_type" not in st.session_state:
    st.session_state.controller_type = "PI"

if "plant_type" not in st.session_state:
    st.session_state.plant_type = "PT1"

if "disturbance_position" not in st.session_state:
    st.session_state.disturbance_position = "Keine Störung"

if "defaults" not in st.session_state:
    st.session_state.defaults = get_default_parameters(
        lernziel=st.session_state.lernziel,
        controller_type=st.session_state.controller_type,
        plant_type=st.session_state.plant_type,
        disturbance_position=st.session_state.disturbance_position,
        schwierigkeitsgrad=st.session_state.schwierigkeitsgrad
    )


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

# builder_flow_state wird bewusst erst beim Öffnen des visuellen Builders
# initialisiert, damit streamlit-flow den Zustand persistent halten kann.


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
        "reale_daten_aktiv": True,
        "eingabetiefe": "Einfach",
        # Temperaturstrecke
        "temp_medium": "Wasser",
        "temp_volumen_m3": 1.0,
        "temp_heizleistung_kw": 12.0,
        "temp_umgebung_c": 15.0,
        "temp_soll_c": 55.0,
        "temp_waermeverlust_w_k": 180.0,
        "temp_wirkungsgrad": 0.95,
        "temp_dichte_kg_m3": 998.0,
        "temp_cp_kj_kgk": 4.18,
        # Drehzahlstrecke
        "motor_leistung_kw": 5.5,
        "motor_nenndrehzahl_rpm": 1450.0,
        "motor_soll_rpm": 1200.0,
        "motor_hochlaufzeit_s": 5.0,
        "motor_leitung_m": 50.0,
        "motor_querschnitt_mm2": 2.5,
        "motor_spannung_v": 400.0,
        "motor_wirkungsgrad": 0.88,
        "motor_leistungsfaktor": 0.82,
        "motor_traegheit_kgm2": 0.18,
        "motor_lastmoment_nm": 20.0,
        # Füllstandsstrecke
        "tank_form": "Zylindrisch",
        "tank_volumen_m3": 2.5,
        "tank_hoehe_m": 2.0,
        "tank_zulauf_m3h": 8.0,
        "tank_abfluss_m3h": 3.0,
        "tank_soll_m": 1.4,
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
    u_min=None,
    u_max=None,
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

        previous_integral = integral_error

        if controller_type in ["PI", "PID"]:
            integral_error += error[k] * dt
        else:
            integral_error = 0.0

        i_part = ki * integral_error

        if controller_type == "PID":
            d_part = kd * (error[k] - previous_error) / dt
        else:
            d_part = 0.0

        raw_output = p_part + i_part + d_part
        limited_output = raw_output
        if u_min is not None:
            limited_output = max(float(u_min), limited_output)
        if u_max is not None:
            limited_output = min(float(u_max), limited_output)

        # Einfaches Anti-Windup: Wenn die Begrenzung aktiv ist und der Fehler
        # weiter in die Sättigung treibt, wird der letzte Integrationsschritt verworfen.
        if limited_output != raw_output and controller_type in ["PI", "PID"]:
            drives_further_into_limit = (
                (u_max is not None and raw_output > float(u_max) and error[k] > 0)
                or (u_min is not None and raw_output < float(u_min) and error[k] < 0)
            )
            if drives_further_into_limit:
                integral_error = previous_integral
                i_part = ki * integral_error
                raw_output = p_part + i_part + d_part
                limited_output = raw_output
                if u_min is not None:
                    limited_output = max(float(u_min), limited_output)
                if u_max is not None:
                    limited_output = min(float(u_max), limited_output)

        u_controller[k] = limited_output
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
# Visueller Regelkreis-Builder – interaktiver Engineering-Baukasten
# ------------------------------------------------------------

def default_builder_config():
    """Standardwerte für einen neuen visuellen Regelkreis."""
    return {
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


def reset_interactive_builder():
    """Setzt Arbeitsfläche, Parameter und Engineering-Schritt zurück."""
    st.session_state.builder_step = 1
    st.session_state.builder_last_validation = None
    st.session_state.builder_config = default_builder_config()

    if "builder_flow_state" in st.session_state:
        del st.session_state.builder_flow_state

    # Widget-Zustände des Builders entfernen, damit beim Neustart
    # wieder die Standardwerte angezeigt werden.
    for key in list(st.session_state.keys()):
        if key.startswith("ib_"):
            del st.session_state[key]


def make_builder_node(kind: str, config: dict):
    """Erzeugt genau einen regelungstechnischen Baustein."""
    node_specs = {
        "setpoint": {
            "id": "sollwert",
            "pos": (20, 220),
            "content": f"{config.get('setpoint_name', 'Sollwert w(t)')}<br>w = {config.get('setpoint', 1.0)}",
            "node_type": "input",
            "source_position": "right",
            "target_position": None,
        },
        "sum": {
            "id": "vergleich",
            "pos": (210, 220),
            "content": "Vergleichsstelle Σ<br>e = w − y",
            "node_type": "default",
            "source_position": "right",
            "target_position": "left",
        },
        "controller": {
            "id": "regler",
            "pos": (420, 220),
            "content": (
                f"{config.get('controller_type', 'PI')}-Regler<br>"
                f"Kp={config.get('kp', 2.0)}<br>"
                f"Ki={config.get('ki', 0.5)}<br>"
                f"Kd={config.get('kd', 0.0)}"
            ),
            "node_type": "default",
            "source_position": "right",
            "target_position": "left",
        },
        "plant": {
            "id": "strecke",
            "pos": (640, 220),
            "content": (
                f"PT1-Strecke<br>Ks={config.get('ks', 1.0)}<br>Ts={config.get('ts', 2.0)} s"
                if config.get("plant_type", "PT1") == "PT1"
                else (
                    f"PT2-Strecke<br>Ks={config.get('ks', 1.0)}<br>"
                    f"ζ={config.get('zeta', 0.7)}<br>"
                    f"ω0={config.get('omega0', 2.0)} rad/s"
                )
            ),
            "node_type": "default",
            "source_position": "right",
            "target_position": "left",
        },
        "output": {
            "id": "ausgang",
            "pos": (860, 220),
            "content": config.get("output_name", "Regelgröße y(t)"),
            # default statt output, damit der Ausgang auch eine Quelle
            # für die Rückführung besitzen kann.
            "node_type": "default",
            "source_position": "right",
            "target_position": "left",
        },
        "feedback": {
            "id": "rueckfuehrung",
            "pos": (470, 450),
            "content": "Rückführung<br>Istwert y(t)",
            "node_type": "default",
            "source_position": "left",
            "target_position": "right",
        },
        "disturbance": {
            "id": "stoerung",
            "pos": (620, 40),
            "content": (
                f"Störung d(t)<br>d={config.get('disturbance_value', -0.3)}<br>"
                f"ab {config.get('disturbance_time', 8.0)} s"
            ),
            "node_type": "input",
            "source_position": "right",
            "target_position": None,
        },
        "dist_sum": {
            "id": "stoersumme",
            "pos": (650, 220),
            "content": "Stör-Summierstelle Σ",
            "node_type": "default",
            "source_position": "right",
            "target_position": "left",
        },
    }

    spec = node_specs[kind]
    data = {"content": spec["content"], "kind": kind}

    if kind == "controller":
        data.update({
            "controller_type": config.get("controller_type", "PI"),
            "kp": float(config.get("kp", 2.0)),
            "ki": float(config.get("ki", 0.5)),
            "kd": float(config.get("kd", 0.0)),
        })

    elif kind == "plant":
        data.update({
            "plant_type": config.get("plant_type", "PT1"),
            "ks": float(config.get("ks", 1.0)),
            "ts": float(config.get("ts", 2.0)),
            "zeta": float(config.get("zeta", 0.7)),
            "omega0": float(config.get("omega0", 2.0)),
        })

    elif kind == "setpoint":
        data.update({
            "setpoint_name": config.get("setpoint_name", "Sollwert w(t)"),
            "setpoint": float(config.get("setpoint", 1.0)),
        })

    elif kind == "output":
        data.update({"output_name": config.get("output_name", "Regelgröße y(t)")})

    elif kind == "disturbance":
        data.update({
            "disturbance_position": config.get("disturbance_position", "Vor der Strecke"),
            "disturbance_time": float(config.get("disturbance_time", 8.0)),
            "disturbance_value": float(config.get("disturbance_value", -0.3)),
        })

    kwargs = dict(
        id=spec["id"],
        pos=spec["pos"],
        data=data,
        node_type=spec["node_type"],
        source_position=spec["source_position"],
        draggable=True,
    )

    if spec["target_position"] is not None:
        kwargs["target_position"] = spec["target_position"]

    return StreamlitFlowNode(**kwargs)


def init_builder_flow_state():
    """
    Initialisiert die Arbeitsfläche genau einmal.
    streamlit-flow 1.6.x benötigt einen persistenten State im session_state.
    """
    if "builder_flow_state" not in st.session_state:
        st.session_state.builder_flow_state = StreamlitFlowState([], [])


def get_builder_node(kind: str):
    """Liefert den ersten Baustein eines Typs oder None."""
    init_builder_flow_state()
    for node in st.session_state.builder_flow_state.nodes:
        if isinstance(node.data, dict) and node.data.get("kind") == kind:
            return node
    return None


def builder_has_node(kind: str) -> bool:
    return get_builder_node(kind) is not None


def add_builder_node(kind: str):
    """Fügt einen Baustein hinzu, sofern dieser noch nicht existiert."""
    init_builder_flow_state()

    if builder_has_node(kind):
        return False

    node = make_builder_node(kind, st.session_state.builder_config)
    st.session_state.builder_flow_state.nodes.append(node)
    return True


def remove_builder_node(kind: str):
    """Entfernt einen Baustein und alle daran hängenden Verbindungen."""
    init_builder_flow_state()

    ids = {
        node.id
        for node in st.session_state.builder_flow_state.nodes
        if isinstance(node.data, dict) and node.data.get("kind") == kind
    }

    if not ids:
        return

    st.session_state.builder_flow_state.nodes = [
        node for node in st.session_state.builder_flow_state.nodes
        if node.id not in ids
    ]

    st.session_state.builder_flow_state.edges = [
        edge for edge in st.session_state.builder_flow_state.edges
        if edge.source not in ids and edge.target not in ids
    ]


def sync_builder_nodes_from_config():
    """
    Synchronisiert Beschriftungen und Parameter der vorhandenen Bausteine
    mit den aktuellen Engineering-Einstellungen, ohne Positionen zu verändern.
    """
    init_builder_flow_state()
    config = st.session_state.builder_config

    for node in st.session_state.builder_flow_state.nodes:
        kind = node.data.get("kind") if isinstance(node.data, dict) else None

        if kind == "setpoint":
            node.data["setpoint_name"] = config.get("setpoint_name", "Sollwert w(t)")
            node.data["setpoint"] = float(config.get("setpoint", 1.0))
            node.data["content"] = (
                f"{config.get('setpoint_name', 'Sollwert w(t)')}<br>"
                f"w = {config.get('setpoint', 1.0)}"
            )

        elif kind == "output":
            node.data["output_name"] = config.get("output_name", "Regelgröße y(t)")
            node.data["content"] = config.get("output_name", "Regelgröße y(t)")

        elif kind == "controller":
            node.data["controller_type"] = config.get("controller_type", "PI")
            node.data["kp"] = float(config.get("kp", 2.0))
            node.data["ki"] = float(config.get("ki", 0.5))
            node.data["kd"] = float(config.get("kd", 0.0))
            node.data["content"] = (
                f"{config.get('controller_type', 'PI')}-Regler<br>"
                f"Kp={config.get('kp', 2.0)}<br>"
                f"Ki={config.get('ki', 0.5)}<br>"
                f"Kd={config.get('kd', 0.0)}"
            )

        elif kind == "plant":
            node.data["plant_type"] = config.get("plant_type", "PT1")
            node.data["ks"] = float(config.get("ks", 1.0))
            node.data["ts"] = float(config.get("ts", 2.0))
            node.data["zeta"] = float(config.get("zeta", 0.7))
            node.data["omega0"] = float(config.get("omega0", 2.0))

            if config.get("plant_type", "PT1") == "PT1":
                node.data["content"] = (
                    f"PT1-Strecke<br>Ks={config.get('ks', 1.0)}<br>"
                    f"Ts={config.get('ts', 2.0)} s"
                )
            else:
                node.data["content"] = (
                    f"PT2-Strecke<br>Ks={config.get('ks', 1.0)}<br>"
                    f"ζ={config.get('zeta', 0.7)}<br>"
                    f"ω0={config.get('omega0', 2.0)} rad/s"
                )

        elif kind == "disturbance":
            node.data["disturbance_position"] = config.get(
                "disturbance_position", "Vor der Strecke"
            )
            node.data["disturbance_time"] = float(config.get("disturbance_time", 8.0))
            node.data["disturbance_value"] = float(config.get("disturbance_value", -0.3))
            node.data["content"] = (
                f"Störung d(t)<br>d={config.get('disturbance_value', -0.3)}<br>"
                f"ab {config.get('disturbance_time', 8.0)} s"
            )

        elif kind == "dist_sum":
            if config.get("disturbance_position") == "Vor der Strecke":
                node.data["content"] = "Stör-Summierstelle Σ<br>u + d"
            elif config.get("disturbance_position") == "Am Ausgang":
                node.data["content"] = "Stör-Summierstelle Σ<br>y + d"
            else:
                node.data["content"] = "Stör-Summierstelle Σ"


def edge_exists(source: str, target: str) -> bool:
    """Prüft, ob eine gerichtete Verbindung existiert."""
    init_builder_flow_state()
    return any(
        edge.source == source and edge.target == target
        for edge in st.session_state.builder_flow_state.edges
    )


def allowed_builder_connections():
    """
    Liefert die Verbindungen, die von der aktuellen Simulation mathematisch
    unterstützt werden.

    Der Builder bleibt damit interaktiv, aber es können keine Verbindungen
    entstehen, die im hinterlegten Simulationsmodell keine Bedeutung haben.
    """
    config = st.session_state.builder_config
    disturbance_position = config.get("disturbance_position", "Keine Störung")

    allowed = {
        ("sollwert", "vergleich"),
        ("vergleich", "regler"),
        ("ausgang", "rueckfuehrung"),
        ("rueckfuehrung", "vergleich"),
    }

    if disturbance_position == "Keine Störung":
        allowed.update({
            ("regler", "strecke"),
            ("strecke", "ausgang"),
        })

    elif disturbance_position == "Vor der Strecke":
        allowed.update({
            ("regler", "stoersumme"),
            ("stoerung", "stoersumme"),
            ("stoersumme", "strecke"),
            ("strecke", "ausgang"),
        })

    elif disturbance_position == "Am Ausgang":
        allowed.update({
            ("regler", "strecke"),
            ("strecke", "stoersumme"),
            ("stoerung", "stoersumme"),
            ("stoersumme", "ausgang"),
        })

    return allowed


def sanitize_builder_edges():
    """
    Entfernt unzulässige, doppelte oder selbstbezügliche Verbindungen.

    Rückgabewert:
        dict mit Anzahl und Beschreibung der entfernten Verbindungen.
    """
    init_builder_flow_state()

    allowed = allowed_builder_connections()
    original_edges = list(st.session_state.builder_flow_state.edges)

    cleaned_edges = []
    seen_pairs = set()
    removed_invalid = 0
    removed_duplicates = 0
    removed_self = 0

    for edge in original_edges:
        pair = (edge.source, edge.target)

        if edge.source == edge.target:
            removed_self += 1
            continue

        if pair not in allowed:
            removed_invalid += 1
            continue

        if pair in seen_pairs:
            removed_duplicates += 1
            continue

        seen_pairs.add(pair)
        cleaned_edges.append(edge)

    changed = len(cleaned_edges) != len(original_edges)

    if changed:
        st.session_state.builder_flow_state.edges = cleaned_edges

    return {
        "changed": changed,
        "invalid": removed_invalid,
        "duplicates": removed_duplicates,
        "self": removed_self,
        "removed_total": (
            removed_invalid
            + removed_duplicates
            + removed_self
        ),
    }


def selected_builder_edge():
    """Liefert die aktuell angeklickte Verbindung oder None."""
    init_builder_flow_state()

    selected_id = getattr(
        st.session_state.builder_flow_state,
        "selected_id",
        None
    )

    if not selected_id:
        return None

    for edge in st.session_state.builder_flow_state.edges:
        if edge.id == selected_id:
            return edge

    return None


def delete_builder_edge(edge_id: str):
    """Löscht gezielt eine Verbindung anhand ihrer ID."""
    init_builder_flow_state()

    st.session_state.builder_flow_state.edges = [
        edge
        for edge in st.session_state.builder_flow_state.edges
        if edge.id != edge_id
    ]

    try:
        st.session_state.builder_flow_state.selected_id = None
    except Exception:
        pass

    st.session_state.builder_last_validation = None


def validate_interactive_builder():
    """
    Prüft nicht nur Parameter, sondern den tatsächlich auf der Arbeitsfläche
    gezeichneten Signalweg.
    """
    init_builder_flow_state()
    config = st.session_state.builder_config
    errors = []
    warnings = []

    required_kinds = ["setpoint", "sum", "controller", "plant", "output", "feedback"]
    missing = [kind for kind in required_kinds if not builder_has_node(kind)]

    kind_names = {
        "setpoint": "Sollwert",
        "sum": "Vergleichsstelle",
        "controller": "Regler",
        "plant": "Strecke",
        "output": "Regelgröße / Ausgang",
        "feedback": "Rückführung",
    }

    for kind in missing:
        errors.append(f"Baustein fehlt: {kind_names[kind]}.")

    disturbance_position = config.get("disturbance_position", "Keine Störung")

    if disturbance_position != "Keine Störung":
        if not builder_has_node("disturbance"):
            errors.append("Der Störungsbaustein fehlt.")
        if not builder_has_node("dist_sum"):
            errors.append("Die Stör-Summierstelle fehlt.")

    # Nur Verbindungen prüfen, deren benötigte Knoten existieren.
    if not missing:
        base_connections = [
            ("sollwert", "vergleich", "Sollwert → Vergleichsstelle"),
            ("vergleich", "regler", "Vergleichsstelle → Regler"),
            ("ausgang", "rueckfuehrung", "Ausgang → Rückführung"),
            ("rueckfuehrung", "vergleich", "Rückführung → Vergleichsstelle"),
        ]

        if disturbance_position == "Keine Störung":
            base_connections.extend([
                ("regler", "strecke", "Regler → Strecke"),
                ("strecke", "ausgang", "Strecke → Ausgang"),
            ])

        elif disturbance_position == "Vor der Strecke":
            base_connections.extend([
                ("regler", "stoersumme", "Regler → Stör-Summierstelle"),
                ("stoerung", "stoersumme", "Störung → Stör-Summierstelle"),
                ("stoersumme", "strecke", "Stör-Summierstelle → Strecke"),
                ("strecke", "ausgang", "Strecke → Ausgang"),
            ])

        elif disturbance_position == "Am Ausgang":
            base_connections.extend([
                ("regler", "strecke", "Regler → Strecke"),
                ("strecke", "stoersumme", "Strecke → Stör-Summierstelle"),
                ("stoerung", "stoersumme", "Störung → Stör-Summierstelle"),
                ("stoersumme", "ausgang", "Stör-Summierstelle → Ausgang"),
            ])

        for source, target, description in base_connections:
            if not edge_exists(source, target):
                errors.append(f"Verbindung fehlt: {description}.")

    # Parameterprüfung
    if float(config.get("kp", 0.0)) < 0:
        errors.append("Kp darf nicht negativ sein.")

    if config.get("controller_type") in ["PI", "PID"] and float(config.get("ki", 0.0)) <= 0:
        warnings.append(
            "Ki ist 0. Der gewählte Regler besitzt dadurch praktisch keinen wirksamen I-Anteil."
        )

    if config.get("controller_type") == "PID" and float(config.get("kd", 0.0)) <= 0:
        warnings.append(
            "Kd ist 0. Der PID-Regler verhält sich dadurch praktisch wie ein PI-Regler."
        )

    if float(config.get("ks", 0.0)) <= 0:
        errors.append("Ks muss größer als 0 sein.")

    if config.get("plant_type") == "PT1" and float(config.get("ts", 0.0)) <= 0:
        errors.append("Ts muss größer als 0 sein.")

    if config.get("plant_type") == "PT2":
        if float(config.get("zeta", 0.0)) <= 0:
            errors.append("ζ muss größer als 0 sein.")
        if float(config.get("omega0", 0.0)) <= 0:
            errors.append("ω0 muss größer als 0 sein.")

    if float(config.get("dt", 0.0)) <= 0:
        errors.append("dt muss größer als 0 sein.")

    if float(config.get("t_end", 0.0)) <= 0:
        errors.append("Die Simulationsdauer muss größer als 0 sein.")

    if float(config.get("dt", 0.01)) >= float(config.get("t_end", 20.0)) / 20:
        warnings.append(
            "Die Schrittweite dt ist relativ groß. Für eine stabile Darstellung sollte sie deutlich kleiner sein."
        )

    return errors, warnings


def render_builder_step_header(step: int):
    steps = [
        "Aufgabe definieren",
        "Regler einbauen",
        "Strecke einbauen",
        "Rückführung & Störung",
        "Verbinden & prüfen",
    ]

    st.progress(step / len(steps))
    st.caption(
        f"Engineering-Schritt {step} von {len(steps)} · {steps[step - 1]}"
    )


def selected_builder_node():
    """Gibt den aktuell angeklickten Knoten zurück, falls einer ausgewählt ist."""
    init_builder_flow_state()
    selected_id = getattr(st.session_state.builder_flow_state, "selected_id", None)

    if not selected_id:
        return None

    for node in st.session_state.builder_flow_state.nodes:
        if node.id == selected_id:
            return node

    return None


def render_selected_node_editor():
    """
    Kompakter Eigenschaften-Dialog für den auf der Arbeitsfläche
    angeklickten Baustein.
    """
    node = selected_builder_node()

    if node is None:
        return

    kind = node.data.get("kind")
    config = st.session_state.builder_config

    readable = {
        "setpoint": "Sollwert",
        "sum": "Vergleichsstelle",
        "controller": "Regler",
        "plant": "Strecke",
        "output": "Regelgröße",
        "feedback": "Rückführung",
        "disturbance": "Störung",
        "dist_sum": "Stör-Summierstelle",
    }

    with st.expander(
        f"Ausgewählter Baustein: {readable.get(kind, node.id)}",
        expanded=True
    ):
        if kind == "controller":
            controller_type = st.selectbox(
                "Reglertyp",
                ["P", "PI", "PID"],
                index=["P", "PI", "PID"].index(config.get("controller_type", "PI")),
                key="ib_selected_controller"
            )

            kp = st.number_input(
                "Kp",
                min_value=0.0,
                value=float(config.get("kp", 2.0)),
                step=0.1,
                key="ib_selected_kp"
            )

            ki = 0.0
            kd = 0.0

            if controller_type in ["PI", "PID"]:
                ki = st.number_input(
                    "Ki",
                    min_value=0.0,
                    value=float(config.get("ki", 0.5)),
                    step=0.1,
                    key="ib_selected_ki"
                )

            if controller_type == "PID":
                kd = st.number_input(
                    "Kd",
                    min_value=0.0,
                    value=float(config.get("kd", 0.0)),
                    step=0.1,
                    key="ib_selected_kd"
                )

            if st.button("Regler-Eigenschaften übernehmen", key="ib_apply_controller"):
                config["controller_type"] = controller_type
                config["kp"] = kp
                config["ki"] = ki
                config["kd"] = kd
                st.session_state.builder_config = config
                sync_builder_nodes_from_config()
                st.rerun()

        elif kind == "plant":
            plant_type = st.selectbox(
                "Streckentyp",
                ["PT1", "PT2"],
                index=["PT1", "PT2"].index(config.get("plant_type", "PT1")),
                key="ib_selected_plant"
            )

            ks = st.number_input(
                "Ks",
                min_value=0.1,
                value=float(config.get("ks", 1.0)),
                step=0.1,
                key="ib_selected_ks"
            )

            ts = float(config.get("ts", 2.0))
            zeta = float(config.get("zeta", 0.7))
            omega0 = float(config.get("omega0", 2.0))

            if plant_type == "PT1":
                ts = st.number_input(
                    "Ts [s]",
                    min_value=0.1,
                    value=ts,
                    step=0.1,
                    key="ib_selected_ts"
                )
            else:
                zeta = st.number_input(
                    "ζ",
                    min_value=0.05,
                    value=zeta,
                    step=0.05,
                    key="ib_selected_zeta"
                )
                omega0 = st.number_input(
                    "ω0 [rad/s]",
                    min_value=0.1,
                    value=omega0,
                    step=0.1,
                    key="ib_selected_omega0"
                )

            if st.button("Strecken-Eigenschaften übernehmen", key="ib_apply_plant"):
                config["plant_type"] = plant_type
                config["ks"] = ks
                config["ts"] = ts
                config["zeta"] = zeta
                config["omega0"] = omega0
                st.session_state.builder_config = config
                sync_builder_nodes_from_config()
                st.rerun()

        elif kind == "disturbance":
            disturbance_time = st.number_input(
                "Störung ab [s]",
                min_value=0.0,
                value=float(config.get("disturbance_time", 8.0)),
                step=0.5,
                key="ib_selected_dist_time"
            )
            disturbance_value = st.number_input(
                "Störgröße d",
                value=float(config.get("disturbance_value", -0.3)),
                step=0.1,
                key="ib_selected_dist_value"
            )

            if st.button("Störung übernehmen", key="ib_apply_dist"):
                config["disturbance_time"] = disturbance_time
                config["disturbance_value"] = disturbance_value
                st.session_state.builder_config = config
                sync_builder_nodes_from_config()
                st.rerun()

        elif kind == "setpoint":
            setpoint_name = st.text_input(
                "Bezeichnung",
                value=config.get("setpoint_name", "Sollwert w(t)"),
                key="ib_selected_setpoint_name"
            )
            setpoint = st.number_input(
                "Sollwert",
                value=float(config.get("setpoint", 1.0)),
                step=0.1,
                key="ib_selected_setpoint"
            )

            if st.button("Sollwert übernehmen", key="ib_apply_setpoint"):
                config["setpoint_name"] = setpoint_name
                config["setpoint"] = setpoint
                st.session_state.builder_config = config
                sync_builder_nodes_from_config()
                st.rerun()

        elif kind == "output":
            output_name = st.text_input(
                "Bezeichnung der Regelgröße",
                value=config.get("output_name", "Regelgröße y(t)"),
                key="ib_selected_output_name"
            )

            if st.button("Regelgröße übernehmen", key="ib_apply_output"):
                config["output_name"] = output_name
                st.session_state.builder_config = config
                sync_builder_nodes_from_config()
                st.rerun()

        else:
            st.write(node.data.get("content", node.id))
            st.caption(
                "Dieser Baustein besitzt in der aktuellen Simulation keine zusätzlichen numerischen Parameter."
            )


def render_visual_builder():
    """
    Interaktiver, aber bewusst geführter Engineering-Baukasten.

    Links wird immer nur der aktuelle Arbeitsschritt gezeigt.
    Rechts ist die echte Arbeitsfläche: Bausteine verschieben, verbinden,
    anklicken sowie über Kontextmenüs löschen.
    """
    init_builder_flow_state()

    config = st.session_state.builder_config
    step = int(st.session_state.builder_step)

    st.title("Visueller Regelkreis-Builder")
    st.caption(
        "Baue den Regelkreis selbst auf. Die App führt dich dabei Schritt für Schritt durch den "
        "Engineering-Prozess, ohne die Arbeitsfläche mit allen Bausteinen gleichzeitig zu überladen."
    )

    render_builder_step_header(step)

    col_work, col_canvas = st.columns([1, 2.2], gap="large")

    # --------------------------------------------------------
    # Linke Seite: genau ein Engineering-Schritt
    # --------------------------------------------------------
    with col_work:
        if step == 1:
            st.subheader("1. Regelaufgabe")

            st.write(
                "Definiere zuerst Führungs- und Regelgröße. Anschließend legst du die drei "
                "Grundbausteine auf die Arbeitsfläche."
            )

            config["setpoint_name"] = st.text_input(
                "Führungsgröße",
                value=config.get("setpoint_name", "Sollwert w(t)"),
                key="ib_setpoint_name"
            )

            config["output_name"] = st.text_input(
                "Regelgröße",
                value=config.get("output_name", "Regelgröße y(t)"),
                key="ib_output_name"
            )

            config["setpoint"] = st.number_input(
                "Sollwert w",
                value=float(config.get("setpoint", 1.0)),
                step=0.1,
                key="ib_setpoint"
            )

            sync_builder_nodes_from_config()

            st.markdown("**Grundbausteine**")

            if not builder_has_node("setpoint"):
                if st.button("Sollwert hinzufügen", width="stretch"):
                    add_builder_node("setpoint")
                    st.rerun()
            else:
                st.success("Sollwert liegt auf der Arbeitsfläche.")

            if not builder_has_node("sum"):
                if st.button("Vergleichsstelle hinzufügen", width="stretch"):
                    add_builder_node("sum")
                    st.rerun()
            else:
                st.success("Vergleichsstelle liegt auf der Arbeitsfläche.")

            if not builder_has_node("output"):
                if st.button("Ausgang / Regelgröße hinzufügen", width="stretch"):
                    add_builder_node("output")
                    st.rerun()
            else:
                st.success("Ausgang / Regelgröße liegt auf der Arbeitsfläche.")

            with st.expander("Warum diese drei Bausteine?", expanded=False):
                st.write(
                    "Der Sollwert beschreibt das gewünschte Verhalten. An der Vergleichsstelle wird "
                    "Soll- und Istwert verglichen. Die Regelgröße ist die Größe, die tatsächlich geregelt wird."
                )

        elif step == 2:
            st.subheader("2. Regler")

            st.write(
                "Wähle jetzt den Regler und parametriere ihn. Danach wird genau dieser Baustein "
                "auf die Arbeitsfläche gelegt."
            )

            config["controller_type"] = st.radio(
                "Reglertyp",
                ["P", "PI", "PID"],
                index=["P", "PI", "PID"].index(config.get("controller_type", "PI")),
                horizontal=True,
                key="ib_controller_type"
            )

            config["kp"] = st.number_input(
                "Kp",
                min_value=0.0,
                value=float(config.get("kp", 2.0)),
                step=0.1,
                key="ib_kp"
            )

            if config["controller_type"] in ["PI", "PID"]:
                config["ki"] = st.number_input(
                    "Ki",
                    min_value=0.0,
                    value=float(config.get("ki", 0.5)),
                    step=0.1,
                    key="ib_ki"
                )
            else:
                config["ki"] = 0.0

            if config["controller_type"] == "PID":
                config["kd"] = st.number_input(
                    "Kd",
                    min_value=0.0,
                    value=float(config.get("kd", 0.0)),
                    step=0.1,
                    key="ib_kd"
                )
            else:
                config["kd"] = 0.0

            sync_builder_nodes_from_config()

            if not builder_has_node("controller"):
                if st.button(
                    f"{config['controller_type']}-Regler hinzufügen",
                    type="primary",
                    width="stretch"
                ):
                    add_builder_node("controller")
                    st.rerun()
            else:
                st.success("Regler liegt auf der Arbeitsfläche.")
                st.caption(
                    "Du kannst den Regler anklicken, um seine Eigenschaften später erneut zu bearbeiten."
                )

            with st.expander("Auswahlhilfe", expanded=False):
                st.markdown(
                    """
                    **P:** einfache, schnelle Reaktion; bleibende Regelabweichung möglich.  
                    **PI:** beseitigt typischerweise die bleibende Regelabweichung.  
                    **PID:** ergänzt einen D-Anteil zur Beeinflussung schneller Änderungen und des Überschwingens.
                    """
                )

        elif step == 3:
            st.subheader("3. Strecke")

            st.write(
                "Modelliere nun das dynamische Verhalten der Anlage als PT1- oder PT2-Strecke."
            )

            config["plant_type"] = st.radio(
                "Streckentyp",
                ["PT1", "PT2"],
                index=["PT1", "PT2"].index(config.get("plant_type", "PT1")),
                horizontal=True,
                key="ib_plant_type"
            )

            config["ks"] = st.number_input(
                "Ks – Streckenverstärkung",
                min_value=0.1,
                value=float(config.get("ks", 1.0)),
                step=0.1,
                key="ib_ks"
            )

            if config["plant_type"] == "PT1":
                config["ts"] = st.number_input(
                    "Ts – Zeitkonstante [s]",
                    min_value=0.1,
                    value=float(config.get("ts", 2.0)),
                    step=0.1,
                    key="ib_ts"
                )
            else:
                config["zeta"] = st.number_input(
                    "ζ – Dämpfung",
                    min_value=0.05,
                    value=float(config.get("zeta", 0.7)),
                    step=0.05,
                    key="ib_zeta"
                )

                config["omega0"] = st.number_input(
                    "ω0 – Eigenkreisfrequenz [rad/s]",
                    min_value=0.1,
                    value=float(config.get("omega0", 2.0)),
                    step=0.1,
                    key="ib_omega0"
                )

            sync_builder_nodes_from_config()

            if not builder_has_node("plant"):
                if st.button(
                    f"{config['plant_type']}-Strecke hinzufügen",
                    type="primary",
                    width="stretch"
                ):
                    add_builder_node("plant")
                    st.rerun()
            else:
                st.success("Strecke liegt auf der Arbeitsfläche.")

            with st.expander("Auswahlhilfe", expanded=False):
                st.markdown(
                    """
                    **PT1:** typische träge Ausgleichsstrecke.  
                    **PT2:** System zweiter Ordnung; Dämpfung und Schwingverhalten können eine Rolle spielen.
                    """
                )

        elif step == 4:
            st.subheader("4. Rückführung und Störung")

            st.write(
                "Schließe den Regelkreis über die Rückführung. Eine Störung ist optional und wird nur "
                "eingeblendet, wenn du sie wirklich untersuchen möchtest."
            )

            if not builder_has_node("feedback"):
                if st.button("Rückführung hinzufügen", type="primary", width="stretch"):
                    add_builder_node("feedback")
                    st.rerun()
            else:
                st.success("Rückführung liegt auf der Arbeitsfläche.")

            st.divider()

            config["disturbance_position"] = st.selectbox(
                "Störung",
                ["Keine Störung", "Vor der Strecke", "Am Ausgang"],
                index=["Keine Störung", "Vor der Strecke", "Am Ausgang"].index(
                    config.get("disturbance_position", "Keine Störung")
                ),
                key="ib_disturbance_position"
            )

            if config["disturbance_position"] == "Keine Störung":
                # Bereits vorhandene Störbausteine bewusst entfernen.
                if builder_has_node("disturbance") or builder_has_node("dist_sum"):
                    if st.button("Störungsbausteine entfernen", width="stretch"):
                        remove_builder_node("disturbance")
                        remove_builder_node("dist_sum")
                        st.rerun()
                else:
                    st.caption("Es wird nur das Führungsverhalten untersucht.")

            else:
                config["disturbance_time"] = st.number_input(
                    "Störung ab [s]",
                    min_value=0.0,
                    value=float(config.get("disturbance_time", 8.0)),
                    step=0.5,
                    key="ib_disturbance_time"
                )

                config["disturbance_value"] = st.number_input(
                    "Störgröße d",
                    value=float(config.get("disturbance_value", -0.3)),
                    step=0.1,
                    key="ib_disturbance_value"
                )

                sync_builder_nodes_from_config()

                if not builder_has_node("disturbance"):
                    if st.button("Störungsbaustein hinzufügen", width="stretch"):
                        add_builder_node("disturbance")
                        st.rerun()
                else:
                    st.success("Störung liegt auf der Arbeitsfläche.")

                if not builder_has_node("dist_sum"):
                    if st.button("Stör-Summierstelle hinzufügen", width="stretch"):
                        add_builder_node("dist_sum")
                        st.rerun()
                else:
                    st.success("Stör-Summierstelle liegt auf der Arbeitsfläche.")

            with st.expander("Engineering-Hinweis", expanded=False):
                st.markdown(
                    """
                    **Vor der Strecke:** typischer Last- oder Prozesseinfluss auf den Streckeneingang.  
                    **Am Ausgang:** direkte Störung der Regelgröße.  
                    Die Störung wird über eine eigene Summierstelle in den Signalweg eingebracht.
                    """
                )

        else:
            st.subheader("5. Verbinden und prüfen")

            st.write(
                "Jetzt ist die Arbeitsfläche entscheidend: Ziehe die Verbindungen zwischen den Anschlusspunkten "
                "der Bausteine. Die App prüft anschließend genau den gezeichneten Signalweg."
            )

            config["t_end"] = st.number_input(
                "Simulationsdauer [s]",
                min_value=1.0,
                max_value=200.0,
                value=float(config.get("t_end", 20.0)),
                step=1.0,
                key="ib_t_end"
            )

            config["dt"] = st.number_input(
                "Schrittweite dt [s]",
                min_value=0.001,
                max_value=1.0,
                value=float(config.get("dt", 0.01)),
                step=0.001,
                format="%.3f",
                key="ib_dt"
            )

            st.info(
                "Verbindungen werden auf der Arbeitsfläche durch Ziehen vom Ausgang eines Bausteins "
                "zum Eingang des nächsten Bausteins erzeugt. Nicht unterstützte oder doppelte "
                "Verbindungen werden automatisch wieder entfernt."
            )

            if st.button("Regelkreis prüfen", type="primary", width="stretch"):
                errors, warnings = validate_interactive_builder()
                st.session_state.builder_last_validation = {
                    "errors": errors,
                    "warnings": warnings
                }

            result = st.session_state.builder_last_validation

            if result is not None:
                if result["errors"]:
                    st.error("Der gezeichnete Regelkreis ist noch nicht vollständig.")
                    for item in result["errors"]:
                        st.write(f"- {item}")
                else:
                    st.success("Der gezeichnete Regelkreis ist vollständig und simulationsfähig.")

                for item in result["warnings"]:
                    st.warning(item)

                if not result["errors"]:
                    if st.button(
                        "Gezeichneten Regelkreis in Simulation übernehmen",
                        type="primary",
                        width="stretch"
                    ):
                        st.session_state.controller_type = config["controller_type"]
                        st.session_state.plant_type = config["plant_type"]
                        st.session_state.disturbance_position = config["disturbance_position"]

                        # Falls der Builder direkt geöffnet wurde, ohne das
                        # Startformular erneut auszufüllen, bleiben diese
                        # beiden Steuerwerte trotzdem definiert.
                        if "lernziel" not in st.session_state:
                            st.session_state.lernziel = "Grundverhalten verstehen"

                        if "schwierigkeitsgrad" not in st.session_state:
                            st.session_state.schwierigkeitsgrad = "Fortgeschritten"

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

            with st.expander("Soll-Verbindungen anzeigen", expanded=False):
                if config.get("disturbance_position") == "Keine Störung":
                    st.markdown(
                        """
                        1. Sollwert → Vergleichsstelle  
                        2. Vergleichsstelle → Regler  
                        3. Regler → Strecke  
                        4. Strecke → Regelgröße  
                        5. Regelgröße → Rückführung  
                        6. Rückführung → Vergleichsstelle
                        """
                    )
                elif config.get("disturbance_position") == "Vor der Strecke":
                    st.markdown(
                        """
                        1. Sollwert → Vergleichsstelle  
                        2. Vergleichsstelle → Regler  
                        3. Regler → Stör-Summierstelle  
                        4. Störung → Stör-Summierstelle  
                        5. Stör-Summierstelle → Strecke  
                        6. Strecke → Regelgröße  
                        7. Regelgröße → Rückführung  
                        8. Rückführung → Vergleichsstelle
                        """
                    )
                else:
                    st.markdown(
                        """
                        1. Sollwert → Vergleichsstelle  
                        2. Vergleichsstelle → Regler  
                        3. Regler → Strecke  
                        4. Strecke → Stör-Summierstelle  
                        5. Störung → Stör-Summierstelle  
                        6. Stör-Summierstelle → Regelgröße  
                        7. Regelgröße → Rückführung  
                        8. Rückführung → Vergleichsstelle
                        """
                    )

        st.session_state.builder_config = config
        sync_builder_nodes_from_config()

        # Kompakter Editor erscheint nur, wenn auf der Arbeitsfläche
        # wirklich ein Baustein angeklickt wurde.
        render_selected_node_editor()

        # ----------------------------------------------------
        # Schritt-Navigation
        # ----------------------------------------------------
        st.divider()
        back_col, next_col = st.columns(2)

        with back_col:
            if step > 1:
                if st.button("Zurück", width="stretch", key="ib_back"):
                    st.session_state.builder_step = step - 1
                    st.session_state.builder_last_validation = None
                    st.rerun()

        with next_col:
            if step < 5:
                step_ready = True

                if step == 1:
                    step_ready = (
                        builder_has_node("setpoint")
                        and builder_has_node("sum")
                        and builder_has_node("output")
                    )
                elif step == 2:
                    step_ready = builder_has_node("controller")
                elif step == 3:
                    step_ready = builder_has_node("plant")
                elif step == 4:
                    step_ready = builder_has_node("feedback")
                    if config.get("disturbance_position") != "Keine Störung":
                        step_ready = (
                            step_ready
                            and builder_has_node("disturbance")
                            and builder_has_node("dist_sum")
                        )

                if st.button(
                    "Weiter",
                    type="primary",
                    width="stretch",
                    key="ib_next",
                    disabled=not step_ready
                ):
                    st.session_state.builder_step = step + 1
                    st.session_state.builder_last_validation = None
                    st.rerun()

        if st.button("Arbeitsfläche leeren / neu beginnen", width="stretch", key="ib_reset"):
            reset_interactive_builder()
            st.rerun()

    # --------------------------------------------------------
    # Rechte Seite: echte interaktive Arbeitsfläche
    # --------------------------------------------------------
    with col_canvas:
        st.subheader("Arbeitsfläche")

        st.caption(
            "Bausteine verschieben · zulässige Anschlüsse verbinden · Verbindung anklicken und mit ✂ löschen · "
            "Rechtsklick auf Baustein oder Verbindung für das Kontextmenü."
        )

        st.caption(
            "Der Ausgang / die Regelgröße befindet sich rechts am Ende der Hauptkette. "
            "Mit dem Fit-View-Steuerelement kannst du jederzeit alle Bausteine wieder ins Bild holen."
        )

        st.session_state.builder_flow_state = streamlit_flow(
            "interactive_engineering_builder",
            st.session_state.builder_flow_state,
            fit_view=True,
            height=650,
            show_minimap=False,
            show_controls=True,
            hide_watermark=True,
            allow_new_edges=True,
            enable_node_menu=True,
            enable_edge_menu=True,
            enable_pane_menu=False,
            get_node_on_click=True,
            get_edge_on_click=True,
            min_zoom=0.2
        )

        # ----------------------------------------------------
        # Verbindungen fachlich begrenzen
        # ----------------------------------------------------
        cleanup = sanitize_builder_edges()

        if cleanup["changed"]:
            parts = []

            if cleanup["invalid"]:
                parts.append(
                    f"{cleanup['invalid']} fachlich nicht unterstützte"
                )

            if cleanup["duplicates"]:
                parts.append(
                    f"{cleanup['duplicates']} doppelte"
                )

            if cleanup["self"]:
                parts.append(
                    f"{cleanup['self']} selbstbezügliche"
                )

            st.session_state.builder_connection_notice = (
                ", ".join(parts)
                + " Verbindung(en) wurden automatisch entfernt."
            )

            # Der bereinigte Python-State wird damit sofort wieder in die
            # Flow-Komponente synchronisiert.
            st.rerun()

        if "builder_connection_notice" in st.session_state:
            st.warning(st.session_state.builder_connection_notice)
            del st.session_state.builder_connection_notice

        # ----------------------------------------------------
        # Verbindung gezielt löschen
        # ----------------------------------------------------
        selected_edge = selected_builder_edge()

        tool_col1, tool_col2 = st.columns([1.3, 2.7])

        with tool_col1:
            if selected_edge is not None:
                if st.button(
                    "✂ Verbindung löschen",
                    type="secondary",
                    width="stretch",
                    key="ib_delete_selected_edge"
                ):
                    delete_builder_edge(selected_edge.id)
                    st.rerun()
            else:
                st.button(
                    "✂ Verbindung löschen",
                    width="stretch",
                    disabled=True,
                    key="ib_delete_selected_edge_disabled"
                )

        with tool_col2:
            if selected_edge is not None:
                st.info(
                    f"Ausgewählt: {selected_edge.source} → {selected_edge.target}"
                )
            else:
                st.caption(
                    "Zum Löschen zuerst eine Verbindung anklicken. Alternativ: "
                    "Rechtsklick auf eine Verbindung und im Kontextmenü löschen."
                )

        # Änderungen aus der UI (Verschieben, neue Kanten, Löschen)
        # liegen jetzt wieder in builder_flow_state vor.
        node_count = len(st.session_state.builder_flow_state.nodes)
        edge_count = len(st.session_state.builder_flow_state.edges)

        status1, status2, status3 = st.columns(3)
        status1.metric("Bausteine", node_count)
        status2.metric("Verbindungen", edge_count)
        status3.metric("Schritt", f"{step}/5")

        if step < 5:
            hints = {
                1: "Lege zuerst Sollwert, Vergleichsstelle und Regelgröße auf die Fläche.",
                2: "Füge den Regler hinzu. Du kannst vorhandene Bausteine bereits passend anordnen.",
                3: "Füge die Strecke hinzu. Die Signalrichtung soll später von links nach rechts laufen.",
                4: "Ergänze Rückführung und optional die Störung.",
            }
            st.info(hints[step])
        else:
            st.success(
                "Die Arbeitsfläche ist jetzt der maßgebende Aufbau. "
                "Verbinde die Bausteine und prüfe anschließend den Regelkreis links."
            )


# ------------------------------------------------------------
# Physikalischer Wirkplan-Builder
# ------------------------------------------------------------

def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, float(value)))


def ensure_real_process_defaults(config: dict):
    """Ergänzt neue Felder auch in bereits laufenden Streamlit-Sitzungen."""
    defaults = {
        "reale_daten_aktiv": True,
        "eingabetiefe": "Einfach",
        "temp_medium": "Wasser",
        "temp_volumen_m3": 1.0,
        "temp_heizleistung_kw": 12.0,
        "temp_umgebung_c": 15.0,
        "temp_soll_c": 55.0,
        "temp_waermeverlust_w_k": 180.0,
        "temp_wirkungsgrad": 0.95,
        "temp_dichte_kg_m3": 998.0,
        "temp_cp_kj_kgk": 4.18,
        "motor_leistung_kw": 5.5,
        "motor_nenndrehzahl_rpm": 1450.0,
        "motor_soll_rpm": 1200.0,
        "motor_hochlaufzeit_s": 5.0,
        "motor_leitung_m": 50.0,
        "motor_querschnitt_mm2": 2.5,
        "motor_spannung_v": 400.0,
        "motor_wirkungsgrad": 0.88,
        "motor_leistungsfaktor": 0.82,
        "motor_traegheit_kgm2": 0.18,
        "motor_lastmoment_nm": 20.0,
        "tank_form": "Zylindrisch",
        "tank_volumen_m3": 2.5,
        "tank_hoehe_m": 2.0,
        "tank_zulauf_m3h": 8.0,
        "tank_abfluss_m3h": 3.0,
        "tank_soll_m": 1.4,
    }
    for key, value in defaults.items():
        config.setdefault(key, value)
    return config


def calculate_real_process_data(config: dict):
    """Berechnet aus realen Anlagendaten ein nachvollziehbares PT1-Ersatzmodell."""
    prozessart = config["prozessart"]
    result = {
        "active": bool(config.get("reale_daten_aktiv", True)),
        "supported": prozessart in {
            "Temperaturregelung", "Drehzahlregelung", "Füllstandsregelung"
        },
        "metrics": [],
        "warnings": [],
        "node_details": {},
        "begruendung": [],
    }

    if not result["active"] or not result["supported"]:
        return result

    if prozessart == "Temperaturregelung":
        medium = config.get("temp_medium", "Wasser")
        stoffwerte = {
            "Wasser": (998.0, 4.18),
            "Luft": (1.204, 1.005),
        }
        if medium in stoffwerte:
            dichte, cp = stoffwerte[medium]
        else:
            dichte = max(float(config.get("temp_dichte_kg_m3", 998.0)), 0.001)
            cp = max(float(config.get("temp_cp_kj_kgk", 4.18)), 0.001)

        volumen = max(float(config.get("temp_volumen_m3", 1.0)), 0.001)
        heizleistung_kw = max(float(config.get("temp_heizleistung_kw", 12.0)), 0.001)
        wirkungsgrad = _clamp(config.get("temp_wirkungsgrad", 0.95), 0.01, 1.0)
        waermeverlust = max(float(config.get("temp_waermeverlust_w_k", 180.0)), 0.1)
        umgebung = float(config.get("temp_umgebung_c", 15.0))
        solltemperatur = float(config.get("temp_soll_c", 55.0))

        masse = volumen * dichte
        waermekapazitaet_j_k = masse * cp * 1000.0
        wirksame_heizleistung_w = heizleistung_kw * 1000.0 * wirkungsgrad
        zeitkonstante_s = waermekapazitaet_j_k / waermeverlust
        max_delta_t = wirksame_heizleistung_w / waermeverlust
        soll_delta_t = max(0.1, solltemperatur - umgebung)
        anfangssteigung_k_min = wirksame_heizleistung_w / waermekapazitaet_j_k * 60.0

        if soll_delta_t > max_delta_t:
            result["warnings"].append(
                "Die gewünschte Temperatur ist mit der eingetragenen Heizleistung und "
                "dem Wärmeverlust im stationären Zustand nicht erreichbar."
            )
        if medium == "Luft":
            result["warnings"].append(
                "Bei Räumen speichert nicht nur die Luft Wärme. Für ein genaueres Modell "
                "müssen Wände, Einrichtung und Gebäudemasse als äquivalente Masse ergänzt werden."
            )

        result.update({
            "ks": max_delta_t / 100.0,
            "ts": _clamp(zeitkonstante_s, 0.1, 500000.0),
            "setpoint": soll_delta_t,
            "t_end": _clamp(5.0 * zeitkonstante_s, 30.0, 1000000.0),
            "disturbance_value": -10.0,
            "input_unit": "% Heizleistung",
            "output_unit": "K Temperaturerhöhung",
            "model_note": (
                "Die Simulation regelt die Temperaturerhöhung ΔT gegenüber der "
                f"Umgebungstemperatur {umgebung:.1f} °C."
            ),
        })
        result["metrics"] = [
            ("Masse", f"{masse:.1f} kg"),
            ("Wärmekapazität", f"{waermekapazitaet_j_k / 1e6:.2f} MJ/K"),
            ("Zeitkonstante", f"{zeitkonstante_s / 60.0:.1f} min"),
            ("Anfangssteigung", f"{anfangssteigung_k_min:.3f} K/min"),
            ("max. ΔT", f"{max_delta_t:.1f} K"),
            ("Sollwert ΔT", f"{soll_delta_t:.1f} K"),
        ]
        result["node_details"] = {
            "stellgroesse": f"Heizung {heizleistung_kw:.1f} kW",
            "prozessglied": f"{medium}, η = {wirkungsgrad * 100:.0f} %",
            "speicher": f"{volumen:.2f} m³ / {masse:.0f} kg",
            "regelgroesse": f"{solltemperatur:.1f} °C (ΔT {soll_delta_t:.1f} K)",
        }
        result["begruendung"].append(
            "Die thermische Zeitkonstante folgt aus Wärmekapazität geteilt durch Wärmeverlustkoeffizient."
        )

    elif prozessart == "Drehzahlregelung":
        leistung_kw = max(float(config.get("motor_leistung_kw", 5.5)), 0.01)
        nenndrehzahl = max(float(config.get("motor_nenndrehzahl_rpm", 1450.0)), 1.0)
        solldrehzahl = _clamp(config.get("motor_soll_rpm", 1200.0), 0.0, nenndrehzahl)
        hochlaufzeit = max(float(config.get("motor_hochlaufzeit_s", 5.0)), 0.1)
        leitung = max(float(config.get("motor_leitung_m", 50.0)), 0.0)
        querschnitt = max(float(config.get("motor_querschnitt_mm2", 2.5)), 0.1)
        spannung = max(float(config.get("motor_spannung_v", 400.0)), 1.0)
        wirkungsgrad = _clamp(config.get("motor_wirkungsgrad", 0.88), 0.1, 1.0)
        cos_phi = _clamp(config.get("motor_leistungsfaktor", 0.82), 0.1, 1.0)
        traegheit = max(float(config.get("motor_traegheit_kgm2", 0.18)), 0.0001)
        lastmoment = max(float(config.get("motor_lastmoment_nm", 20.0)), 0.0)

        nennmoment = 9550.0 * leistung_kw / nenndrehzahl
        nennstrom = leistung_kw * 1000.0 / (
            np.sqrt(3.0) * spannung * wirkungsgrad * cos_phi
        )
        spannungsfall = np.sqrt(3.0) * nennstrom * 0.0178 * leitung / querschnitt
        spannungsfall_prozent = spannungsfall / spannung * 100.0
        motorspannung = max(spannung - spannungsfall, 0.0)
        momentfaktor = (motorspannung / spannung) ** 2
        verfuegbares_moment = nennmoment * momentfaktor
        beschleunigungsmoment = verfuegbares_moment - lastmoment
        omega_n = 2.0 * np.pi * nenndrehzahl / 60.0

        if beschleunigungsmoment > 0:
            mechanische_hochlaufzeit = traegheit * omega_n / beschleunigungsmoment
        else:
            mechanische_hochlaufzeit = hochlaufzeit
            result["warnings"].append(
                "Das berechnete Motormoment ist nicht größer als das Lastmoment. "
                "Ein sicherer Hochlauf ist mit diesen Angaben nicht nachgewiesen."
            )
        if spannungsfall_prozent > 3.0:
            result["warnings"].append(
                f"Der überschlägige Spannungsfall beträgt {spannungsfall_prozent:.1f} %. "
                "Leitung, Verlegeart, Schutzorgan und Anlaufstrom müssen genauer geprüft werden."
            )

        pt1_zeit = max(hochlaufzeit, mechanische_hochlaufzeit) / 3.0
        result.update({
            "ks": nenndrehzahl / 100.0,
            "ts": _clamp(pt1_zeit, 0.1, 500000.0),
            "setpoint": solldrehzahl,
            "t_end": max(20.0, 6.0 * pt1_zeit),
            "disturbance_value": -10.0,
            "input_unit": "% Ansteuerung",
            "output_unit": "1/min",
            "model_note": (
                "Der Spannungsfall ist eine überschlägige Drehstromberechnung. "
                "Bei Frequenzumrichterbetrieb sind zusätzlich Herstellerangaben zu Motorkabel, "
                "Filter und EMV zu beachten."
            ),
        })
        result["metrics"] = [
            ("Nennmoment", f"{nennmoment:.1f} Nm"),
            ("Nennstrom ca.", f"{nennstrom:.1f} A"),
            ("Spannungsfall", f"{spannungsfall:.1f} V / {spannungsfall_prozent:.1f} %"),
            ("Moment an Leitung", f"{verfuegbares_moment:.1f} Nm"),
            ("mechan. Hochlauf", f"{mechanische_hochlaufzeit:.2f} s"),
            ("PT1-Zeitkonstante", f"{pt1_zeit:.2f} s"),
        ]
        result["node_details"] = {
            "stellgroesse": f"0–100 % / {spannung:.0f} V",
            "prozessglied": f"Motor {leistung_kw:.1f} kW, Leitung {leitung:.0f} m",
            "speicher": f"J = {traegheit:.3f} kg·m²",
            "regelgroesse": f"Soll {solldrehzahl:.0f} 1/min",
        }
        result["begruendung"].append(
            "Das Motormoment wird aus Leistung und Nenndrehzahl berechnet; die längere aus vorgegebener und mechanischer Hochlaufzeit bestimmt das PT1-Ersatzmodell."
        )

    elif prozessart == "Füllstandsregelung":
        volumen = max(float(config.get("tank_volumen_m3", 2.5)), 0.001)
        hoehe = max(float(config.get("tank_hoehe_m", 2.0)), 0.01)
        zulauf = max(float(config.get("tank_zulauf_m3h", 8.0)), 0.001)
        abfluss = max(float(config.get("tank_abfluss_m3h", 3.0)), 0.0)
        soll = _clamp(config.get("tank_soll_m", 1.4), 0.0, hoehe)
        querschnitt = volumen / hoehe
        netto_zulauf = zulauf - abfluss

        if netto_zulauf > 0:
            vollfuellzeit_s = volumen / netto_zulauf * 3600.0
            sollzeit_s = querschnitt * soll / netto_zulauf * 3600.0
        else:
            vollfuellzeit_s = volumen / zulauf * 3600.0
            sollzeit_s = querschnitt * soll / zulauf * 3600.0
            result["warnings"].append(
                "Der maximale Zulauf ist nicht größer als der Abfluss. Der Sollfüllstand kann bei konstantem Abfluss nicht erreicht werden."
            )

        pt1_zeit = max(vollfuellzeit_s / 3.0, 0.1)
        if config.get("tank_form") == "Zylindrisch":
            durchmesser = 2.0 * np.sqrt(querschnitt / np.pi)
            geometrie = f"Ø {durchmesser:.2f} m"
        else:
            durchmesser = None
            geometrie = f"A = {querschnitt:.2f} m²"

        result.update({
            "ks": hoehe / 100.0,
            "ts": _clamp(pt1_zeit, 0.1, 500000.0),
            "setpoint": soll,
            "t_end": _clamp(max(60.0, 5.0 * pt1_zeit), 60.0, 1000000.0),
            "disturbance_value": -10.0 if abfluss > 0 else -5.0,
            "input_unit": "% Zulauf",
            "output_unit": "m Füllstand",
            "model_note": (
                "Ein Behälter ist physikalisch eine integrierende Strecke. Für das vorhandene "
                "Regelkreis-Labor wird daraus zunächst ein PT1-Ersatzmodell gebildet."
            ),
        })
        result["metrics"] = [
            ("Querschnitt", f"{querschnitt:.3f} m²"),
            ("Geometrie", geometrie),
            ("Nettozulauf", f"{netto_zulauf:.2f} m³/h"),
            ("Zeit bis Soll", f"{sollzeit_s / 60.0:.1f} min"),
            ("Zeit bis voll", f"{vollfuellzeit_s / 60.0:.1f} min"),
            ("PT1-Ersatzzeit", f"{pt1_zeit / 60.0:.1f} min"),
        ]
        result["node_details"] = {
            "stellgroesse": f"Zulauf bis {zulauf:.1f} m³/h",
            "prozessglied": f"Pumpe / Ventil, Abfluss {abfluss:.1f} m³/h",
            "speicher": f"{volumen:.2f} m³ / {hoehe:.2f} m",
            "regelgroesse": f"Soll {soll:.2f} m",
        }
        result["begruendung"].append(
            "Querschnitt, Nettozulauf und Zielhöhe bestimmen die reale Füllzeit; daraus wird ein PT1-Ersatzmodell für die vorhandene Simulation abgeleitet."
        )

    if "ks" in result:
        # Einfache, robuste IMC-nahe Startauslegung für ein PT1-Modell ohne Totzeit.
        result["kp"] = _clamp(2.0 / max(result["ks"], 0.001), 0.001, 100.0)
        result["ki"] = _clamp(result["kp"] / max(result["ts"], 0.1), 0.0, 100.0)
        result["dt"] = _clamp(result["t_end"] / 5000.0, 0.01, 60.0)
        result["u_min"] = 0.0
        result["u_max"] = 100.0

    return result


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

    physical = calculate_real_process_data(config)
    result["physical"] = physical

    uses_real_model = physical.get("active") and physical.get("supported") and "ks" in physical

    if uses_real_model:
        result["plant_type"] = "PT1"
        result["controller_type"] = "PI"
        result["kp"] = physical["kp"]
        result["ki"] = physical["ki"]
        result["kd"] = 0.0
        result["ks"] = physical["ks"]
        result["ts"] = physical["ts"]
        result["setpoint"] = physical["setpoint"]
        result["t_end"] = physical["t_end"]
        result["dt"] = physical["dt"]
        result["disturbance_value"] = physical["disturbance_value"]
        result["begruendung"].extend(physical["begruendung"])
        result["begruendung"].append(
            "Strecken- und Reglerparameter werden aus den realen Anlagendaten statt nur aus einer qualitativen Einschätzung gebildet."
        )

    if not uses_real_model and traegheit == "sehr träge":
        result["ts"] *= 1.8
        result["t_end"] *= 1.5
        result["kp"] *= 0.8
        result["ki"] *= 0.7
        result["begruendung"].append(
            "Da der Prozess als sehr träge bewertet wurde, werden die Startparameter vorsichtiger gewählt."
        )

    elif not uses_real_model and traegheit == "schnell":
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
        if uses_real_model:
            result["disturbance_time"] = result["t_end"] / 2
        else:
            result["disturbance_time"] = min(10.0, result["t_end"] / 2)
        if not uses_real_model:
            result["disturbance_value"] = -0.3
        result["begruendung"].append(
            "Da relevante Störungen auftreten, wird eine Laststörung vor der Strecke für die Simulation vorgeschlagen."
        )
    else:
        result["disturbance_position"] = "Keine Störung"
        result["disturbance_time"] = 0.0
        result["disturbance_value"] = 0.0

    result["kp"] = round(float(result["kp"]), 3)
    result["ki"] = round(float(result["ki"]), 8)
    result["kd"] = round(float(result["kd"]), 3)
    result["ks"] = round(float(result["ks"]), 6)
    result["ts"] = round(float(result["ts"]), 3)
    result["t_end"] = round(float(result["t_end"]), 3)
    result["dt"] = round(float(result["dt"]), 4)
    result["setpoint"] = round(float(result["setpoint"]), 4)
    result["disturbance_time"] = round(float(result["disturbance_time"]), 3)
    result["disturbance_value"] = round(float(result["disturbance_value"]), 4)

    return result


def build_wirkplan_flow(config: dict):
    physical = calculate_real_process_data(config)
    details = physical.get("node_details", {})

    def node_content(title: str, config_value: str, detail_key: str) -> str:
        detail = details.get(detail_key)
        if detail:
            return f"{title}<br>{config_value}<br><b>{detail}</b>"
        return f"{title}<br>{config_value}"

    nodes = [
        StreamlitFlowNode(
            id="stellgroesse",
            pos=(0, 180),
            data={"content": node_content("Stellgröße", config["stellgroesse"], "stellgroesse")},
            node_type="input",
            source_position="right",
            draggable=True
        ),
        StreamlitFlowNode(
            id="prozessglied",
            pos=(280, 180),
            data={"content": node_content("Prozessglied", config["prozessglied"], "prozessglied")},
            node_type="default",
            source_position="right",
            target_position="left",
            draggable=True
        ),
        StreamlitFlowNode(
            id="speicher",
            pos=(580, 180),
            data={"content": node_content("Speicher / Trägheit", config["speicher"], "speicher")},
            node_type="default",
            source_position="right",
            target_position="left",
            draggable=True
        ),
        StreamlitFlowNode(
            id="regelgroesse",
            pos=(880, 180),
            data={"content": node_content("Regelgröße", config["regelgroesse"], "regelgroesse")},
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


def render_real_process_inputs(config: dict):
    """Zeigt nur die zur Prozessart und Eingabetiefe passenden realen Anlagendaten."""
    config["reale_daten_aktiv"] = st.checkbox(
        "Reale Anlagendaten für die Berechnung verwenden",
        value=bool(config.get("reale_daten_aktiv", True)),
        key="wirkplan_reale_daten_aktiv",
    )

    if not config["reale_daten_aktiv"]:
        st.caption("Die App verwendet wieder die qualitativen Prozess-Presets.")
        return config

    config["eingabetiefe"] = st.selectbox(
        "Eingabetiefe",
        ["Einfach", "Erweitert", "Experte"],
        index=["Einfach", "Erweitert", "Experte"].index(
            config.get("eingabetiefe", "Einfach")
        ),
        key="wirkplan_eingabetiefe",
        help="Ausgeblendete Detailwerte bleiben als gekennzeichnete Standardannahmen aktiv.",
    )
    tiefe = config["eingabetiefe"]
    prozessart = config["prozessart"]

    if prozessart not in {
        "Temperaturregelung", "Drehzahlregelung", "Füllstandsregelung"
    }:
        st.info(
            "Reale Berechnungsmodelle sind in dieser ersten Ausbaustufe für Temperatur, "
            "Drehzahl und Füllstand verfügbar. Diese Prozessart verwendet weiterhin das Preset."
        )
        return config

    def number(key, label, minimum, step, help_text=None, fmt=None):
        kwargs = {
            "label": label,
            "min_value": float(minimum),
            "value": float(config[key]),
            "step": float(step),
            "key": f"wirkplan_{key}",
            "help": help_text,
        }
        if fmt is not None:
            kwargs["format"] = fmt
        config[key] = st.number_input(**kwargs)

    if prozessart == "Temperaturregelung":
        config["temp_medium"] = st.selectbox(
            "Medium",
            ["Wasser", "Luft", "Benutzerdefiniert"],
            index=["Wasser", "Luft", "Benutzerdefiniert"].index(
                config.get("temp_medium", "Wasser")
            ),
            key="wirkplan_temp_medium",
        )
        number("temp_volumen_m3", "Volumen [m³]", 0.001, 0.1, fmt="%.3f")
        number("temp_heizleistung_kw", "Heizleistung [kW]", 0.001, 0.5, fmt="%.3f")
        number("temp_umgebung_c", "Umgebungstemperatur [°C]", -100.0, 1.0)
        number("temp_soll_c", "Solltemperatur [°C]", -100.0, 1.0)

        if tiefe in ["Erweitert", "Experte"]:
            number(
                "temp_waermeverlust_w_k",
                "Wärmeverlustkoeffizient [W/K]",
                0.1,
                10.0,
                "Wärmeleistung, die je Kelvin Temperaturdifferenz an die Umgebung verloren geht.",
            )
        else:
            st.caption(
                f"Annahme: Wärmeverlustkoeffizient {config['temp_waermeverlust_w_k']:.0f} W/K."
            )

        if tiefe == "Experte":
            number("temp_wirkungsgrad", "Wirkungsgrad [0–1]", 0.01, 0.01, fmt="%.2f")
            if config["temp_medium"] == "Benutzerdefiniert":
                number("temp_dichte_kg_m3", "Dichte [kg/m³]", 0.001, 1.0, fmt="%.3f")
                number(
                    "temp_cp_kj_kgk",
                    "spezifische Wärmekapazität [kJ/(kg·K)]",
                    0.001,
                    0.01,
                    fmt="%.3f",
                )
        else:
            st.caption(f"Annahme: thermischer Wirkungsgrad {config['temp_wirkungsgrad'] * 100:.0f} %.")

    elif prozessart == "Drehzahlregelung":
        number("motor_leistung_kw", "Motorleistung [kW]", 0.01, 0.1)
        number("motor_nenndrehzahl_rpm", "Nenndrehzahl [1/min]", 1.0, 10.0)
        number("motor_soll_rpm", "Solldrehzahl [1/min]", 0.0, 10.0)
        number("motor_hochlaufzeit_s", "vorgegebene Hochlaufzeit [s]", 0.1, 0.5)

        if tiefe in ["Erweitert", "Experte"]:
            number("motor_leitung_m", "Motorleitung – einfache Länge [m]", 0.0, 5.0)
            number("motor_querschnitt_mm2", "Leiterquerschnitt [mm²]", 0.1, 0.5)
        else:
            st.caption(
                f"Annahme: {config['motor_leitung_m']:.0f} m Motorleitung mit "
                f"{config['motor_querschnitt_mm2']:.1f} mm² Cu."
            )

        if tiefe == "Experte":
            number("motor_spannung_v", "Drehspannung [V]", 1.0, 10.0)
            number("motor_wirkungsgrad", "Wirkungsgrad η [0–1]", 0.1, 0.01, fmt="%.2f")
            number("motor_leistungsfaktor", "Leistungsfaktor cos φ [0–1]", 0.1, 0.01, fmt="%.2f")
            number("motor_traegheit_kgm2", "Gesamtträgheitsmoment J [kg·m²]", 0.0001, 0.01, fmt="%.4f")
            number("motor_lastmoment_nm", "Lastmoment [Nm]", 0.0, 1.0)
        else:
            st.caption(
                f"Annahmen: η {config['motor_wirkungsgrad']:.2f}, cos φ "
                f"{config['motor_leistungsfaktor']:.2f}, J {config['motor_traegheit_kgm2']:.3f} kg·m², "
                f"Lastmoment {config['motor_lastmoment_nm']:.1f} Nm."
            )

    elif prozessart == "Füllstandsregelung":
        number("tank_volumen_m3", "Behältervolumen [m³]", 0.001, 0.1, fmt="%.3f")
        number("tank_hoehe_m", "maximale Füllhöhe [m]", 0.01, 0.1)
        number("tank_zulauf_m3h", "maximaler Zulauf [m³/h]", 0.001, 0.5, fmt="%.3f")
        number("tank_soll_m", "Sollfüllstand [m]", 0.0, 0.1)

        if tiefe in ["Erweitert", "Experte"]:
            config["tank_form"] = st.selectbox(
                "Behälterform",
                ["Zylindrisch", "Rechteckig"],
                index=["Zylindrisch", "Rechteckig"].index(
                    config.get("tank_form", "Zylindrisch")
                ),
                key="wirkplan_tank_form",
            )
            number("tank_abfluss_m3h", "konstanter Abfluss [m³/h]", 0.0, 0.5)
        else:
            st.caption(
                f"Annahme: {config['tank_form'].lower()}er Behälter und "
                f"{config['tank_abfluss_m3h']:.1f} m³/h konstanter Abfluss."
            )

        if tiefe == "Experte":
            st.caption(
                "Das Modell verwendet aktuell einen konstanten Querschnitt und konstanten Abfluss. "
                "Ein höhenabhängiger freier Auslauf folgt in einer späteren Ausbaustufe."
            )

    return config


def render_wirkplan_builder():
    st.title("Physikalischer Wirkplan-Builder")

    st.caption(
        "Hier startest du nicht mit Regler und Strecke, sondern mit physikalischen Größen. "
        "Aus dem Wirkplan leitet die App ein geeignetes Streckenmodell und einen Startregler ab."
    )

    config = ensure_real_process_defaults(st.session_state.wirkplan_config)

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

        with st.expander("2. Reale Anlagendaten", expanded=True):
            config = render_real_process_inputs(config)

        with st.expander("3. Verhalten des Prozesses", expanded=False):
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

        with st.expander("4. Störeinflüsse", expanded=False):
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
        physical = derived.get("physical", {})

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

            if "lernziel" not in st.session_state:
                st.session_state.lernziel = "Grundverhalten verstehen"

            if "schwierigkeitsgrad" not in st.session_state:
                st.session_state.schwierigkeitsgrad = "Fortgeschritten"

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
                "u_min": physical.get("u_min") if physical.get("active") else None,
                "u_max": physical.get("u_max") if physical.get("active") else None,
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
        physical = derived.get("physical", {})

        if physical.get("active") and physical.get("supported"):
            st.subheader("Berechnete Anlagenkennwerte")
            metrics = physical.get("metrics", [])
            for start in range(0, len(metrics), 3):
                columns = st.columns(3)
                for column, (label, value) in zip(columns, metrics[start:start + 3]):
                    column.metric(label, value)

            if physical.get("model_note"):
                st.info(physical["model_note"])

            for warning in physical.get("warnings", []):
                st.warning(warning)

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
                step=0.001,
                format="%.6f",
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
            min_value=0.000001,
            max_value=100.0,
            value=float(defaults["ks"]),
            step=0.01,
            format="%.6f",
            help="Ks beschreibt, wie stark die Strecke auf die Stellgröße reagiert."
        )

        if defaults.get("u_min") is not None and defaults.get("u_max") is not None:
            st.caption(
                f"Reales Stellglied aktiv: Stellgröße wird auf "
                f"{defaults['u_min']:.0f} bis {defaults['u_max']:.0f} % begrenzt."
            )

        if plant_type == "PT1":
            ts = st.number_input(
                "Ts - Zeitkonstante PT1 [s]",
                min_value=0.1,
                max_value=500000.0,
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
            max_value=1000000.0,
            value=float(defaults["t_end"]),
            step=1.0
        )

        if st.session_state.get("schwierigkeitsgrad", "Fortgeschritten") == "Experte":
            dt = st.number_input(
                "Schrittweite dt [s]",
                min_value=0.001,
                max_value=60.0,
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
                max_value=float(max(200.0, t_end)),
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
    u_min=defaults.get("u_min"),
    u_max=defaults.get("u_max"),
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

