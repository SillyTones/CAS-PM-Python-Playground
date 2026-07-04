"""
QM-Tracking System - Enhanced Wizard
====================================
Ein vereinfachter Wizard mit Rest-Anwendung und Dialog.
"""

import streamlit as st
import streamlit_antd_components as sac
from datetime import datetime, date
from enum import Enum, auto

# nice views for nodes: https://stflow.streamlit.app/Static_Flows

# Mitarbeiterlisten
_MITARBEITER_KUNDENDIENST = ['Scherrer Curdin', 'Mettler Walo', 'Grieder Linus', 'Sturzenegger Tarzisius', 'Aellen Pankraz', 'Vogt Beda', 'Marending Gion', 'Piller Hugo', 'Amrein Aldo', 'Weibel Iso', 'Oesch Hansjörg', 'Savary Linus', 'Wenger Tarzisius', 'Schürch Fritz', 'Küpfer Marco', 'Schmutz Valentin', 'Brunschwiler Gion']
_MITARBEITER_HOTLINE = ['Genoud Duri', 'Imhof Domenic', 'Iseli Fritz', 'Delessert Valentin', 'Rossier Gion', 'Kaufmann Elias', 'Chevalley Werner', 'Kellenberger Pankraz', 'Ruckstuhl Orlando', 'Frischknecht Benno', 'Wehrli Ilir', 'Steinmann Livio']
_MITARBEITER_VERKAUF = ['Fivaz Quirin', 'Berthoud Valerio', 'Gehrig Placi', 'Baertschi Cornel', 'Steffen Walo', 'Dähler Jarno', 'Chappuis Nils', 'Ecoffey Flavio', 'Perritaz Klemens', 'Trachsel Ephrem', 'Naef Jodok']
_MITARBEITER_MONTAGE = ['Wüthrich Kaspar', 'Brogli Gieri', 'Zbinden Flurin', 'Knecht Thom', 'Hangartner Jarno', 'Nydegger Ilir', 'Feuz Notker', 'Hirschy Ephrem', 'Stalder Andrin', 'Probst Christof', 'Descloux Nino', 'Thommen Benno', 'Rennhard Ursin', 'Rüegg Livio', 'Sudan Urban', 'Stampfli Pirmin', 'Eichmann Curdin', 'Junod Quirin', 'Waldmeier Kaspar', 'Progin Meinrad', 'Schneeberger Andri', 'Wicht Silvio', 'Portmann Mario', 'Dähler Jarno', 'Wehrli Ilir', 'Steinmann Livio', 'Cathomen Iso', 'Scherrer Werner']
_MITARBEITER_INBETRIEBNAHME = ['Jaton Remo', 'Landolt Marco', 'Christinat Leandro', 'Rickenbacher Hubert', 'Grunder Yves', 'Hasler Domenic', 'Leuenberger Jachen', 'Niederberger Beda', 'Magnenat Remo', 'Salvisberg Christof', 'Herzig Yves']
_MITARBEITER_KONSTRUKTION = ['Repond Meinrad', 'Jost Jachen', 'Schilling Mario', 'Vial Hubert']
_MITARBEITER_VORFUHRUNG = ['Wegmann Elio', 'Rindlisbacher Odilo', 'Senn Andri', 'Bissig Jodok', 'Andermatt Elio', 'Zingg Gieri', 'Gonseth Flurin', 'Brülisauer Thom', 'Wetzel Silas', 'Ebnöther Leandro', 'Tanner Koni', 'Hodel Andrin', 'Zimmerli Urban', 'Yerly Nino', 'Zollinger Aldo', 'Scherrer Werner']
_MITARBEITER_SOFTWARE_ENT = ['Aebischer Silvio', 'Iseli Fritz', 'Trüb Klemens', 'Rennhard Ursin', 'Wanner Odilo', 'Kissling Valerio', 'Tinguely Notker']
_MITARBEITER_ELEKTRO_ENT = ['Marmy Orlando', 'Wiesmann Duri', 'Vionnet Gion', 'Zeller Elias']
_MITARBEITER_ENTWICKLUNGSLEITUNG = ['Blatter Placi']
_MITARBEITER_ENTWICKLUNG_APP_TEST = ['Schneeberger Andri', 'Ebnöther Leandro']
_MITARBEITER_QS = ['Habegger Ursin', 'Iseli Fritz', 'Schoch Hugo']
_MITARBEITER_GESCHAFTSLEITUNG = ['Overney Nils', 'Currat Silas']
_MITARBEITER_IT = ['Gassmann Flavio', 'Etter Koni']
_MITARBEITER_PRODUKTIONSLEITUNG = ['Schoch Hugo']

class RECHTE(Enum):
    ANSICHT = auto()
    ERFASSEN = auto()
    BEARBEITEN = auto()
    ZUWEISEN = auto()
    STATISTIK = auto()
    SUPERUSER = auto()

class ABTEILUNGEN(Enum):
    KUNDENDIENST = {"name": "Kundendienst", "Mitarbeiter": _MITARBEITER_KUNDENDIENST, "Rechte": {RECHTE.ERFASSEN}}
    HOTLINE = {"name": "Hotline", "Mitarbeiter": _MITARBEITER_HOTLINE, "Rechte": {RECHTE.ERFASSEN}}
    VERKAUF = {"name": "Verkauf", "Mitarbeiter": _MITARBEITER_VERKAUF, "Rechte": {RECHTE.ERFASSEN}}
    MONTAGE = {"name": "Montage", "Mitarbeiter": _MITARBEITER_MONTAGE, "Rechte": {RECHTE.ERFASSEN}}
    INBETRIEBNAHME = {"name": "Inbetriebnahme", "Mitarbeiter": _MITARBEITER_INBETRIEBNAHME, "Rechte": {RECHTE.ERFASSEN}}
    KONSTRUKTION = {"name": "Konstruktion", "Mitarbeiter": _MITARBEITER_KONSTRUKTION, "Rechte": {RECHTE.ERFASSEN, RECHTE.BEARBEITEN}}
    VORFÜHRUNG = {"name": "Vorführung", "Mitarbeiter": _MITARBEITER_VORFUHRUNG, "Rechte": {RECHTE.ERFASSEN}}
    SOFTWARE_ENTWICKLUNG = {"name": "Softwareentwicklung", "Mitarbeiter": _MITARBEITER_SOFTWARE_ENT, "Rechte": {RECHTE.ERFASSEN, RECHTE.BEARBEITEN}}
    ELEKTRO_ENTWICKLUNG = {"name": "Elektroentwicklung", "Mitarbeiter": _MITARBEITER_ELEKTRO_ENT, "Rechte": {RECHTE.ERFASSEN, RECHTE.BEARBEITEN}}
    ENTWICKLUNGSLEITUNG = {"name": "Entwicklungsleitung", "Mitarbeiter": _MITARBEITER_ENTWICKLUNGSLEITUNG, "Rechte": {RECHTE.ERFASSEN, RECHTE.BEARBEITEN, RECHTE.ZUWEISEN}}
    ENTWICKLUNG_APPLIKATION_TEST = {"name": "Entwicklung Anwendungstest", "Mitarbeiter": _MITARBEITER_ENTWICKLUNG_APP_TEST, "Rechte": {RECHTE.ERFASSEN, RECHTE.BEARBEITEN}}
    QS = {"name": "Qualitätssicherung", "Mitarbeiter": _MITARBEITER_QS, "Rechte": {RECHTE.ERFASSEN, RECHTE.BEARBEITEN,RECHTE.ZUWEISEN, RECHTE.STATISTIK}}
    GESCHAFTSLEITUNG = {"name": "Geschäftsleitung", "Mitarbeiter": _MITARBEITER_GESCHAFTSLEITUNG, "Rechte": {RECHTE.ERFASSEN, RECHTE.BEARBEITEN, RECHTE.ZUWEISEN, RECHTE.STATISTIK, RECHTE.SUPERUSER}}
    IT = {"name": "Informatik", "Mitarbeiter": _MITARBEITER_IT, "Rechte": {RECHTE.ERFASSEN, RECHTE.BEARBEITEN, RECHTE.ZUWEISEN, RECHTE.STATISTIK, RECHTE.SUPERUSER}}
    PRODUKTIONSLEITUNG = {"name": "Produktionsleitung", "Mitarbeiter": _MITARBEITER_PRODUKTIONSLEITUNG, "Rechte": {RECHTE.ERFASSEN,RECHTE.STATISTIK}}

WIZARD_STEPS = {
    1: {"titel": "Grunddaten", "icon": "📝", "felder": ["titel", "beschreibung", "typ"]},
    2: {"titel": "Klassifikation", "icon": "🏷️", "felder": ["kategorie", "prioritaet"]},
    3: {"titel": "Details", "icon": "🔧", "felder": ["betroffenes_produkt", "version", "standort"]},
    4: {"titel": "Zuweisung", "icon": "👥", "felder": ["abteilung", "zugewiesen_an", "faellig_am"]},
    5: {"titel": "Zusammenfassung", "icon": "✅", "felder": []}
}

FORMULAR_CONFIG = {
    "titel": {
        "label": "Titel des Qualitätsmangels",
        "type": "text",
        "required": True,
        "placeholder": "z.B. Fehlerhafte Anzeige im Dashboard"
    },
    "beschreibung": {
        "label": "Beschreibung",
        "type": "textarea",
        "required": True,
        "placeholder": "Beschreiben Sie das Problem..."
    },
    "typ": {
        "label": "Typ",
        "type": "selectbox",
        "required": True,
        "options": ["Hardware", "Software", "Feature Request", "Anleitung", "Sonstiges"]
    },
    "kategorie": {
        "label": "Kategorie",
        "type": "selectbox",
        "required": True,
        "options": ["Fehler", "Verbesserung", "Kritischer Mangel", "Sicherheitsproblem", "Dokumentation", "Kundenwunsch"]
    },
    "prioritaet": {
        "label": "Priorität",
        "type": "selectbox",
        "required": False,
        "options": ["Niedrig", "Mittel", "Hoch", "Kritisch"],
        "default": "Mittel"
    },
    "betroffenes_produkt": {
        "label": "Betroffenes Produkt/System",
        "type": "text",
        "required": False,
        "placeholder": "z.B. Dashboard v2.1"
    },
    "version": {
        "label": "Version/Modell",
        "type": "text",
        "required": False,
        "placeholder": "z.B. v2.1.3"
    },
    "standort": {
        "label": "Standort/Kunde",
        "type": "text",
        "required": False,
        "placeholder": "z.B. Kunde XY"
    },
    "abteilung": {
        "label": "Zuständige Abteilung",
        "type": "selectbox",
        "required": False,
        "options": [abteilung.value["name"] for abteilung in ABTEILUNGEN]
    },
    "zugewiesen_an": {
        "label": "Zugewiesen an (Person)",
        "type": "text",
        "required": False,
        "placeholder": "Name der zuständigen Person"
    },
    "faellig_am": {
        "label": "Fälligkeitsdatum",
        "type": "date",
        "required": False
    }
}

PROZESS_STATUS ={
        "Erfasst": {"beschreibung": "QM wurde erfasst", "naechster_status": "In Prüfung"},
        "In Prüfung": {"beschreibung": "QM wird geprüft", "naechster_status": "Priorisiert & Zugewiesen"},
        "Priorisiert & Zugewiesen": {"beschreibung": "QM ist zugewiesen", "naechster_status": "In Bearbeitung"},
        "In Bearbeitung": {"beschreibung": "QM in Bearbeitung", "naechster_status": "Gelöst"},
        "Gelöst": {"beschreibung": "QM wurde gelöst", "naechster_status": None},
        "Abgelehnt": {"beschreibung": "QM wurde abgelehnt", "naechster_status": None}
    }


def init_session_state():
    if "qm_liste" not in st.session_state:
        st.session_state.qm_liste = []
    if "qm_counter" not in st.session_state:
        st.session_state.qm_counter = 10000
    if "current_view" not in st.session_state:
        st.session_state.current_view = "uebersicht"
    if "selected_qm_id" not in st.session_state:
        st.session_state.selected_qm_id = None
    if "wizard_step" not in st.session_state:
        st.session_state.wizard_step = 1
    if "wizard_data" not in st.session_state:
        st.session_state.wizard_data = {}
    if "show_wizard" not in st.session_state:
        st.session_state.show_wizard = False
    if "wizard_error" not in st.session_state:
        st.session_state.wizard_error = ""


def generate_qm_nummer():
    jahr = datetime.now().year
    nummer = st.session_state.qm_counter
    st.session_state.qm_counter += 1
    return f"{jahr}QM{nummer:05d}"


def create_qm(formular_daten):
    qm = {
        "qm_id": len(st.session_state.qm_liste) + 1,
        "qm_nummer": generate_qm_nummer(),
        "erstellt_am": datetime.now(),
        "status": "Neu",
        "prozess_status": "Neu",
        "ersteller": "Test User",
        "history": [
            {
                "timestamp": datetime.now(),
                "typ": "erstellt",
                "user": "Test User",
                "details": "QM wurde erstellt",
                "status": "Neu"
            }
        ],
        "kommentare": [],
        **formular_daten
    }
    st.session_state.qm_liste.append(qm)
    return qm


def add_history_entry(qm, typ, details, alter_wert=None, neuer_wert=None):
    qm["history"].append({
        "timestamp": datetime.now(),
        "typ": typ,
        "user": "Test User",
        "details": details,
        "alter_wert": alter_wert,
        "neuer_wert": neuer_wert,
        "status": qm.get("prozess_status", qm.get("status", "Unbekannt"))
    })


def get_qm_by_id(qm_id):
    for qm in st.session_state.qm_liste:
        if qm["qm_id"] == qm_id:
            return qm
    return None


def render_wizard_progress():
    current_step = st.session_state.wizard_step
    items = [
        sac.StepsItem(
            title=step_info["icon"],
            subtitle=step_info["titel"]
        )
        for step_info in WIZARD_STEPS.values()
    ]
    selected = sac.steps(
        items=items,
        size="sm",
        index=current_step - 1,
        return_index=True,
        key="wizard_steps"
    )
    if selected is not None and selected != current_step - 1:
        st.session_state.wizard_step = selected + 1
    st.divider()


def render_formular_field(field_name, field_config, default_value=None):
    label = field_config["label"]
    if field_config.get("required", False):
        label = f"{label} *"

    if default_value is None:
        default_value = st.session_state.wizard_data.get(field_name, "")

    if field_config["type"] == "text":
        return st.text_input(
            label,
            value=default_value,
            placeholder=field_config.get("placeholder", "")
        )
    if field_config["type"] == "textarea":
        return st.text_area(
            label,
            value=default_value,
            placeholder=field_config.get("placeholder", ""),
            height=150
        )
    if field_config["type"] == "selectbox":
        options = field_config.get("options", [])
        default_index = 0
        if default_value in options:
            default_index = options.index(default_value)
        elif field_config.get("default") in options:
            default_index = options.index(field_config.get("default"))
        return st.selectbox(
            label,
            options,
            index=default_index
        )
    if field_config["type"] == "date":
        return st.date_input(
            label,
            value=default_value if isinstance(default_value, date) else date.today()
        )
    return None




@st.dialog("Neuen Qualitätsmangel erfassen", width="large", on_dismiss="rerun")
def view_wizard():
    render_wizard_progress()
    current_step = st.session_state.wizard_step
    if current_step < 5:
        st.subheader(f"{WIZARD_STEPS[current_step]['icon']} {WIZARD_STEPS[current_step]['titel']}")
        for field_name in WIZARD_STEPS[current_step]["felder"]:
            field_config = FORMULAR_CONFIG[field_name]
            value = render_formular_field(field_name, field_config)
            st.session_state.wizard_data[field_name] = value
    else:
        st.subheader(f"{WIZARD_STEPS[5]['icon']} {WIZARD_STEPS[5]['titel']}")
        st.markdown("### Bitte überprüfen Sie Ihre Eingaben:")
        for step_id in range(1, 5):
            st.markdown(f"**{WIZARD_STEPS[step_id]['titel']}**")
            for field_name in WIZARD_STEPS[step_id]["felder"]:
                value = st.session_state.wizard_data.get(field_name, "-")
                st.write(f"- {FORMULAR_CONFIG[field_name]['label']}: {value}")

    if st.session_state.wizard_error:
        st.error(st.session_state.wizard_error)

    st.divider()
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if current_step > 1 and st.button("⬅️ Zurück", use_container_width=True):
            st.session_state.wizard_step -= 1
            st.session_state.wizard_error = ""
            st.rerun()
    with col3:
        if current_step < 5 and st.button("Weiter ➡️", use_container_width=True):
            fehlende_felder = []
            for field_name in WIZARD_STEPS[current_step]["felder"]:
                config = FORMULAR_CONFIG[field_name]
                value = st.session_state.wizard_data.get(field_name)
                if config.get("required") and not value:
                    fehlende_felder.append(config["label"])
            if fehlende_felder:
                st.session_state.wizard_error = "Bitte füllen Sie folgende Pflichtfelder aus: " + ", ".join(fehlende_felder)
            else:
                st.session_state.wizard_step += 1
                st.session_state.wizard_error = ""
                st.rerun()
        elif current_step == 5 and st.button("✅ QM Erfassen", type="primary", use_container_width=True):
            qm = create_qm(st.session_state.wizard_data)
            st.success(f"✅ Qualitätsmangel {qm['qm_nummer']} wurde erfasst")
            st.session_state.show_wizard = False
            st.session_state.wizard_step = 1
            st.session_state.wizard_data = {}
            st.session_state.wizard_error = ""
            st.session_state.selected_qm_id = qm["qm_id"]
            st.session_state.current_view = "details"
            st.rerun()
    with col2:
        if st.button("❌ Abbrechen", use_container_width=True):
            st.session_state.show_wizard = False
            st.session_state.wizard_step = 1
            st.session_state.wizard_data = {}
            st.session_state.wizard_error = ""
            st.session_state.current_view = "uebersicht"
            st.rerun()


def render_prozess_status(qm):
    aktueller_status = qm.get("prozess_status", qm.get("status", "Neu"))
    status_info = {
        "Neu": {"farbe": "#FF6B6B", "icon": "🆕", "beschreibung": "QM wurde erfasst"},
        "In Prüfung": {"farbe": "#4ECDC4", "icon": "🔍", "beschreibung": "QM wird geprüft"},
        "Priorisiert & Zugewiesen": {"farbe": "#95E1D3", "icon": "📋", "beschreibung": "QM ist zugewiesen"},
        "In Bearbeitung": {"farbe": "#F38181", "icon": "⚙️", "beschreibung": "QM in Bearbeitung"},
        "Gelöst": {"farbe": "#95E1D3", "icon": "✅", "beschreibung": "QM wurde gelöst"},
        "Abgelehnt": {"farbe": "#C0C0C0", "icon": "❌", "beschreibung": "QM wurde abgelehnt"}
    }.get(aktueller_status, {"farbe": "#A8E6CF", "icon": "📌", "beschreibung": aktueller_status})

    st.markdown(
        f"""
        <div style='background-color: {status_info['farbe']}; padding: 15px; border-radius: 10px; text-align: center;'>
            <h2 style='margin: 0; color: white;'>{status_info['icon']} {aktueller_status}</h2>
            <p style='margin: 5px 0 0 0; color: white; font-size: 14px;'>{status_info['beschreibung']}</p>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_prozess_timeline_visual(qm):
    st.subheader("📅 Timeline")
    if not qm.get("history"):
        st.info("Keine Historie vorhanden.")
        return
    for entry in qm["history"]:
        zeit = entry["timestamp"].strftime("%d.%m.%Y %H:%M")
        st.markdown(f"**{zeit}** – {entry['details']}")


def view_uebersicht():
    st.header("📊 Qualitätsmängel - Übersicht")
    if st.button("➕ Neuen QM erfassen", type="primary", use_container_width=True):
        st.session_state.show_wizard = True
        st.session_state.wizard_step = 1
        st.session_state.wizard_data = {}
        st.session_state.wizard_error = ""

    if not st.session_state.qm_liste:
        st.info("Noch keine Qualitätsmängel erfasst.")
        return

    for qm in st.session_state.qm_liste:
        status = qm.get("prozess_status", qm.get("status", "Neu"))
        st.markdown(f"### {qm['qm_nummer']} – {qm['titel']} ({status})")
        st.write(f"Erstellt am: {qm['erstellt_am'].strftime('%d.%m.%Y %H:%M')}")
        if st.button("👁️ Details", key=f"view_{qm['qm_id']}", use_container_width=True):
            st.session_state.selected_qm_id = qm['qm_id']
            st.session_state.current_view = "details"
        st.divider()


def view_details():
    qm = get_qm_by_id(st.session_state.selected_qm_id)
    if not qm:
        st.warning("Kein QM ausgewählt.")
        if st.button("← Zurück zur Übersicht"):
            st.session_state.current_view = "uebersicht"
        return

    st.header(f"📄 {qm['qm_nummer']}: {qm['titel']}")
    if st.button("← Zurück zur Übersicht", use_container_width=True):
        st.session_state.current_view = "uebersicht"
        st.session_state.selected_qm_id = None

    st.markdown(f"**Status:** {qm.get('prozess_status', qm.get('status'))}")
    st.markdown(f"**Kategorie:** {qm.get('kategorie', '-')}")
    st.markdown(f"**Priorität:** {qm.get('prioritaet', '-')}")
    st.markdown(f"**Beschreibung:** {qm.get('beschreibung', '-')}")
    st.divider()
    render_prozess_status(qm)
    st.divider()
    render_prozess_timeline_visual(qm)


def main():
    st.set_page_config(page_title="QM-Tracking System", page_icon="📋", layout="wide")
    init_session_state()

    with st.sidebar:
        st.title("📋 QM-Tracking")
        if st.button("📊 Übersicht", use_container_width=True, disabled=st.session_state.current_view == "uebersicht"):
            st.session_state.current_view = "uebersicht"
            st.session_state.selected_qm_id = None
            st.session_state.show_wizard = False
        st.divider()

    if st.session_state.show_wizard:
        view_wizard()
    elif st.session_state.current_view == "uebersicht":
        view_uebersicht()
    elif st.session_state.current_view == "details":
        view_details()


if __name__ == "__main__":
    main()
