"""
QM-Tracking System - Phase -1 (Pre-MVP)
========================================
Minimaler Prototyp ohne Datenbank für schnelles Formular-Testing.
Alle Daten werden in st.session_state gespeichert (gehen beim Neustart verloren).

Flexibles Formular-Design über FORMULAR_CONFIG Dictionary.
"""

import streamlit as st
from datetime import datetime, date
import pandas as pd

# ============================================================================
# KONFIGURATION - HIER ANPASSEN!
# ============================================================================

FORMULAR_CONFIG = {
    "titel": {
        "label": "Titel des Qualitätsmangels",
        "type": "text",
        "required": True,
        "placeholder": "z.B. Fehlerhafte Anzeige im Dashboard",
        "help": "Kurze, prägnante Beschreibung des Problems"
    },
    "beschreibung": {
        "label": "Detaillierte Beschreibung",
        "type": "textarea",
        "required": True,
        "placeholder": "Beschreiben Sie das Problem so detailliert wie möglich...",
        "help": "Was ist passiert? Unter welchen Umständen? Was wurde erwartet?"
    },
    "typ": {
        "label": "Typ",
        "type": "selectbox",
        "required": True,
        "options": ["Hardware", "Software", "Feature Request", "Sonstiges"],
        "help": "Um welche Art von Qualitätsmangel handelt es sich?"
    },
    "kategorie": {
        "label": "Kategorie",
        "type": "selectbox",
        "required": True,
        "options": ["Fehler", "Verbesserung", "Kritischer Mangel", "Sicherheitsproblem", "Dokumentation"],
        "help": "Klassifizierung des Mangels"
    },
    "prioritaet": {
        "label": "Priorität",
        "type": "selectbox",
        "required": False,
        "options": ["Niedrig", "Mittel", "Hoch", "Kritisch"],
        "default": "Mittel",
        "help": "Wie dringend ist die Behebung?"
    },
    "betroffenes_produkt": {
        "label": "Betroffenes Produkt/System",
        "type": "text",
        "required": False,
        "placeholder": "z.B. Dashboard v2.1, Sensor XY-500",
        "help": "Welches Produkt oder System ist betroffen?"
    },
    "version": {
        "label": "Version/Modell",
        "type": "text",
        "required": False,
        "placeholder": "z.B. v2.1.3 oder Modell ABC-123",
        "help": "Software-Version oder Hardware-Modell"
    },
    "abteilung": {
        "label": "Zuständige Abteilung",
        "type": "selectbox",
        "required": False,
        "options": ["", "Entwicklung (HW)", "Entwicklung (SW)", "Qualitätssicherung", "Service", "Support"],
        "help": "An welche Abteilung soll der QM zugewiesen werden?"
    },
    "faellig_am": {
        "label": "Fälligkeitsdatum",
        "type": "date",
        "required": False,
        "help": "Bis wann soll der Mangel behoben sein?"
    }
}

STATUS_OPTIONEN = ["Neu", "In Bearbeitung", "Warten auf Info", "Gelöst", "Geschlossen", "Abgelehnt"]

# ============================================================================
# INITIALISIERUNG
# ============================================================================

def init_session_state():
    """Initialisiert Session State für Datenspeicherung"""
    if 'qm_liste' not in st.session_state:
        st.session_state.qm_liste = []
    
    if 'qm_counter' not in st.session_state:
        st.session_state.qm_counter = 10000
    
    if 'current_view' not in st.session_state:
        st.session_state.current_view = 'uebersicht'
    
    if 'selected_qm_id' not in st.session_state:
        st.session_state.selected_qm_id = None

# ============================================================================
# HELPER FUNKTIONEN
# ============================================================================

def generate_qm_nummer():
    """Generiert eine eindeutige QM-Nummer"""
    jahr = datetime.now().year % 100  # Letzte zwei Ziffern des Jahres
    nummer = st.session_state.qm_counter
    st.session_state.qm_counter += 1
    return f"{jahr}QM{nummer:05d}"

def create_qm(formular_daten):
    """Erstellt einen neuen QM-Eintrag"""
    qm = {
        'qm_id': len(st.session_state.qm_liste) + 1,
        'qm_nummer': generate_qm_nummer(),
        'erstellt_am': datetime.now(),
        'status': 'Neu',
        'ersteller': 'Test User',  # In echter Version: aktueller User
        'history': [
            {
                'timestamp': datetime.now(),
                'typ': 'erstellt',
                'user': 'Test User',
                'details': 'QM wurde erstellt'
            }
        ],
        'kommentare': [],
        **formular_daten
    }
    
    st.session_state.qm_liste.append(qm)
    return qm

def add_history_entry(qm, typ, details, alter_wert=None, neuer_wert=None):
    """Fügt einen History-Eintrag zu einem QM hinzu"""
    entry = {
        'timestamp': datetime.now(),
        'typ': typ,
        'user': 'Test User',  # In echter Version: aktueller User
        'details': details,
        'alter_wert': alter_wert,
        'neuer_wert': neuer_wert
    }
    qm['history'].append(entry)

def get_qm_by_id(qm_id):
    """Holt einen QM-Eintrag anhand der ID"""
    for qm in st.session_state.qm_liste:
        if qm['qm_id'] == qm_id:
            return qm
    return None

# ============================================================================
# FORMULAR-RENDERING
# ============================================================================

def render_formular_field(field_name, field_config):
    """Rendert ein einzelnes Formular-Feld basierend auf der Konfiguration"""
    label = field_config['label']
    required = field_config.get('required', False)
    help_text = field_config.get('help', None)
    
    # Label mit Pflichtfeld-Markierung
    if required:
        label = f"{label} *"
    
    field_type = field_config['type']
    
    if field_type == 'text':
        return st.text_input(
            label,
            placeholder=field_config.get('placeholder', ''),
            help=help_text
        )
    
    elif field_type == 'textarea':
        return st.text_area(
            label,
            placeholder=field_config.get('placeholder', ''),
            help=help_text,
            height=150
        )
    
    elif field_type == 'selectbox':
        options = field_config.get('options', [])
        default = field_config.get('default')
        index = 0
        if default and default in options:
            index = options.index(default)
        
        return st.selectbox(
            label,
            options,
            index=index,
            help=help_text
        )
    
    elif field_type == 'date':
        return st.date_input(
            label,
            value=None,
            help=help_text
        )
    
    return None

# ============================================================================
# VIEWS
# ============================================================================
@st.dialog("📝 Neuen Qualitätsmangel erfassen",width="medium")
def view_formular():
    """QM-Erfassungsformular"""    
    with st.form("qm_formular", clear_on_submit=True):
        formular_daten = {}
        
        # Rendere alle Formular-Felder basierend auf Config
        for field_name, field_config in FORMULAR_CONFIG.items():
            value = render_formular_field(field_name, field_config)
            formular_daten[field_name] = value
        
        col1, col2 = st.columns([1, 4])
        with col1:
            submit = st.form_submit_button("✅ QM Erfassen", use_container_width=True)
        with col2:
            st.caption("* Pflichtfelder")
        
        if submit:
            # Validierung: Prüfe Pflichtfelder
            fehler = []
            for field_name, field_config in FORMULAR_CONFIG.items():
                if field_config.get('required', False):
                    value = formular_daten[field_name]
                    if not value or (isinstance(value, str) and value.strip() == ""):
                        fehler.append(field_config['label'])
            
            if fehler:
                st.error(f"⚠️ Bitte füllen Sie folgende Pflichtfelder aus: {', '.join(fehler)}")
            else:
                qm = create_qm(formular_daten)
                st.success(f"✅ Qualitätsmangel **{qm['qm_nummer']}** wurde erfolgreich erfasst!")
                st.balloons()
                
                # Info-Box mit QM-Details
                with st.expander("📋 Erfasste Daten", expanded=True):
                    st.write(f"**QM-Nummer:** {qm['qm_nummer']}")
                    st.write(f"**Titel:** {qm['titel']}")
                    st.write(f"**Status:** {qm['status']}")
                    st.write(f"**Priorität:** {qm.get('prioritaet', 'Nicht angegeben')}")

def view_uebersicht():
    """Übersicht aller QMs"""
    st.header("📊 Qualitätsmängel - Übersicht")
    
    if not st.session_state.qm_liste:
        st.info("ℹ️ Noch keine Qualitätsmängel erfasst. Nutzen Sie das Formular, um einen neuen QM zu erstellen.")
        return
    
    # Filter-Optionen
    col1, col2, col3 = st.columns(3)
    
    with col1:
        filter_status = st.multiselect(
            "Status filtern",
            STATUS_OPTIONEN,
            default=STATUS_OPTIONEN
        )
    
    with col2:
        alle_typen = list(set([qm.get('typ', 'Unbekannt') for qm in st.session_state.qm_liste]))
        filter_typ = st.multiselect(
            "Typ filtern",
            alle_typen,
            default=alle_typen
        )
    
    with col3:
        alle_prioritaeten = list(set([qm.get('prioritaet', 'Nicht angegeben') for qm in st.session_state.qm_liste]))
        filter_prioritaet = st.multiselect(
            "Priorität filtern",
            alle_prioritaeten,
            default=alle_prioritaeten
        )
    
    # Gefilterte Liste
    gefilterte_qms = [
        qm for qm in st.session_state.qm_liste
        if qm['status'] in filter_status
        and qm.get('typ', 'Unbekannt') in filter_typ
        and qm.get('prioritaet', 'Nicht angegeben') in filter_prioritaet
    ]
    
    st.write(f"**Angezeigt:** {len(gefilterte_qms)} von {len(st.session_state.qm_liste)} QMs")
    
    # Tabelle erstellen
    if gefilterte_qms:
        df_data = []
        for qm in gefilterte_qms:
            df_data.append({
                'QM-Nr': qm['qm_nummer'],
                'Titel': qm['titel'],
                'Typ': qm.get('typ', '-'),
                'Status': qm['status'],
                'Priorität': qm.get('prioritaet', '-'),
                'Erstellt am': qm['erstellt_am'].strftime('%d.%m.%Y %H:%M'),
                'Abteilung': qm.get('abteilung', '-')
            })
        
        df = pd.DataFrame(df_data)
        
        # Interaktive Tabelle mit Auswahl
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )
        
        # QM auswählen für Details
        st.divider()
        qm_nummern = [qm['qm_nummer'] for qm in gefilterte_qms]
        selected_qm_nummer = st.selectbox(
            "QM auswählen für Details:",
            [''] + qm_nummern,
            format_func=lambda x: "-- Bitte wählen --" if x == '' else x
        )
        
        if selected_qm_nummer:
            selected_qm = next(qm for qm in st.session_state.qm_liste if qm['qm_nummer'] == selected_qm_nummer)
            if st.button("📄 Details anzeigen", use_container_width=True):
                st.session_state.selected_qm_id = selected_qm['qm_id']
                st.session_state.current_view = 'details'
                st.rerun()
    else:
        st.warning("⚠️ Keine QMs entsprechen den ausgewählten Filtern.")

def view_details():
    """Detail-Ansicht eines QMs mit Timeline"""
    if not st.session_state.selected_qm_id:
        st.warning("⚠️ Kein QM ausgewählt.")
        if st.button("← Zurück zur Übersicht"):
            st.session_state.current_view = 'uebersicht'
            st.rerun()
        return
    
    qm = get_qm_by_id(st.session_state.selected_qm_id)
    
    if not qm:
        st.error("⚠️ QM nicht gefunden.")
        return
    
    # Header
    col1, col2 = st.columns([3, 1])
    with col1:
        st.header(f"📄 {qm['qm_nummer']}: {qm['titel']}")
    with col2:
        if st.button("← Zurück", use_container_width=True):
            st.session_state.current_view = 'uebersicht'
            st.session_state.selected_qm_id = None
            st.rerun()
    
    # Tabs für verschiedene Bereiche
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Details", "🔄 Bearbeiten", "💬 Kommentare", "📅 Timeline"])
    
    # TAB 1: Details
    with tab1:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Stammdaten")
            st.write(f"**QM-Nummer:** {qm['qm_nummer']}")
            st.write(f"**Status:** {qm['status']}")
            st.write(f"**Priorität:** {qm.get('prioritaet', 'Nicht angegeben')}")
            st.write(f"**Typ:** {qm.get('typ', '-')}")
            st.write(f"**Kategorie:** {qm.get('kategorie', '-')}")
            st.write(f"**Erstellt am:** {qm['erstellt_am'].strftime('%d.%m.%Y %H:%M')}")
            st.write(f"**Ersteller:** {qm['ersteller']}")
        
        with col2:
            st.subheader("Zusatzinformationen")
            st.write(f"**Abteilung:** {qm.get('abteilung', 'Nicht zugewiesen')}")
            st.write(f"**Betroffenes Produkt:** {qm.get('betroffenes_produkt', '-')}")
            st.write(f"**Version/Modell:** {qm.get('version', '-')}")
            if qm.get('faellig_am'):
                st.write(f"**Fällig am:** {qm['faellig_am']}")
        
        st.divider()
        st.subheader("Beschreibung")
        st.write(qm.get('beschreibung', 'Keine Beschreibung vorhanden'))
    
    # TAB 2: Bearbeiten
    with tab2:
        st.subheader("🔄 QM bearbeiten")
        
        col1, col2 = st.columns(2)
        
        with col1:
            neuer_status = st.selectbox(
                "Status ändern",
                STATUS_OPTIONEN,
                index=STATUS_OPTIONEN.index(qm['status'])
            )
        
        with col2:
            prioritaeten = ["Niedrig", "Mittel", "Hoch", "Kritisch"]
            aktuelle_prio = qm.get('prioritaet', 'Mittel')
            neue_prioritaet = st.selectbox(
                "Priorität ändern",
                prioritaeten,
                index=prioritaeten.index(aktuelle_prio)
            )
        
        neue_abteilung = st.selectbox(
            "Abteilung zuweisen",
            ["", "Entwicklung (HW)", "Entwicklung (SW)", "Qualitätssicherung", "Service", "Support"],
            index=0 if not qm.get('abteilung') else ["", "Entwicklung (HW)", "Entwicklung (SW)", "Qualitätssicherung", "Service", "Support"].index(qm.get('abteilung'))
        )
        
        if st.button("💾 Änderungen speichern", use_container_width=True):
            aenderungen = []
            
            # Status geändert?
            if neuer_status != qm['status']:
                add_history_entry(qm, 'status_geaendert', f"Status geändert von '{qm['status']}' auf '{neuer_status}'", qm['status'], neuer_status)
                qm['status'] = neuer_status
                aenderungen.append("Status")
            
            # Priorität geändert?
            if neue_prioritaet != qm.get('prioritaet'):
                add_history_entry(qm, 'prioritaet_geaendert', f"Priorität geändert von '{qm.get('prioritaet')}' auf '{neue_prioritaet}'", qm.get('prioritaet'), neue_prioritaet)
                qm['prioritaet'] = neue_prioritaet
                aenderungen.append("Priorität")
            
            # Abteilung geändert?
            if neue_abteilung != qm.get('abteilung'):
                add_history_entry(qm, 'zugewiesen', f"Zugewiesen an Abteilung '{neue_abteilung}'", qm.get('abteilung'), neue_abteilung)
                qm['abteilung'] = neue_abteilung
                aenderungen.append("Abteilung")
            
            if aenderungen:
                st.success(f"✅ Änderungen gespeichert: {', '.join(aenderungen)}")
                st.rerun()
            else:
                st.info("ℹ️ Keine Änderungen vorgenommen.")
    
    # TAB 3: Kommentare
    with tab3:
        st.subheader("💬 Kommentare & Diskussion")
        
        # Neuen Kommentar hinzufügen
        with st.form(f"kommentar_form_{qm['qm_id']}", clear_on_submit=True):
            kommentar_text = st.text_area(
                "Neuer Kommentar",
                placeholder="Schreiben Sie hier Ihren Kommentar...",
                height=100
            )
            submit_kommentar = st.form_submit_button("📤 Kommentar hinzufügen")
            
            if submit_kommentar and kommentar_text.strip():
                kommentar = {
                    'timestamp': datetime.now(),
                    'user': 'Test User',
                    'text': kommentar_text
                }
                qm['kommentare'].append(kommentar)
                add_history_entry(qm, 'kommentar', f"Kommentar hinzugefügt")
                st.success("✅ Kommentar hinzugefügt!")
                st.rerun()
        
        # Alle Kommentare anzeigen
        st.divider()
        if qm['kommentare']:
            for i, kommentar in enumerate(reversed(qm['kommentare'])):
                with st.container():
                    st.caption(f"**{kommentar['user']}** • {kommentar['timestamp'].strftime('%d.%m.%Y %H:%M')}")
                    st.write(kommentar['text'])
                    if i < len(qm['kommentare']) - 1:
                        st.divider()
        else:
            st.info("ℹ️ Noch keine Kommentare vorhanden.")
    
    # TAB 4: Timeline
    with tab4:
        st.subheader("📅 Timeline & Änderungshistorie")
        
        if qm['history']:
            for entry in reversed(qm['history']):
                timestamp_str = entry['timestamp'].strftime('%d.%m.%Y %H:%M')
                
                # Icon basierend auf Typ
                icon_map = {
                    'erstellt': '🆕',
                    'status_geaendert': '🔄',
                    'prioritaet_geaendert': '⚡',
                    'zugewiesen': '👤',
                    'kommentar': '💬'
                }
                icon = icon_map.get(entry['typ'], '📌')
                
                # Timeline-Entry
                col1, col2 = st.columns([1, 5])
                with col1:
                    st.caption(timestamp_str)
                with col2:
                    st.markdown(f"{icon} **{entry['user']}** • {entry['details']}")
                    
                    # Zeige alte/neue Werte wenn vorhanden
                    if entry.get('alter_wert') and entry.get('neuer_wert'):
                        st.caption(f"   `{entry['alter_wert']}` → `{entry['neuer_wert']}`")
                
                st.divider()
        else:
            st.info("ℹ️ Keine Historie vorhanden.")

# ============================================================================
# MAIN APP
# ============================================================================

def main():
    st.set_page_config(
        page_title="QM-Tracking System",
        page_icon="📋",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    init_session_state()
    
    # Sidebar Navigation
    with st.sidebar:
        st.title("📋 QM-Tracking")
        st.caption("Phase -1: Pre-MVP (In-Memory)")
        
        st.divider()
        
        if st.button("📝 QM Erfassen", use_container_width=True):
            st.session_state.current_view = 'formular'
            st.rerun()
        
        if st.button("📊 Übersicht", use_container_width=True):
            st.session_state.current_view = 'uebersicht'
            st.session_state.selected_qm_id = None
            st.rerun()
        
        st.divider()
        
        # Statistiken
        st.subheader("📈 Statistiken")
        st.metric("Gesamt QMs", len(st.session_state.qm_liste))
        
        if st.session_state.qm_liste:
            status_counts = {}
            for qm in st.session_state.qm_liste:
                status = qm['status']
                status_counts[status] = status_counts.get(status, 0) + 1
            
            for status, count in status_counts.items():
                st.metric(status, count)
        
        st.divider()
        
        # Info-Bereich
        with st.expander("ℹ️ Hinweise"):
            st.caption("**Pre-MVP Version**")
            st.caption("• Keine Datenbank")
            st.caption("• Daten nur im RAM")
            st.caption("• Geht beim Neustart verloren")
            st.caption("• Perfekt zum Formular-Testen!")
        
        # Reset-Button
        if st.button("🗑️ Alle Daten löschen", use_container_width=True):
            if st.session_state.qm_liste:
                st.session_state.qm_liste = []
                st.session_state.qm_counter = 1
                st.success("✅ Alle Daten gelöscht!")
                st.rerun()
    
    # Main Content
    if st.session_state.current_view == 'formular':
        view_formular()
    elif st.session_state.current_view == 'uebersicht':
        view_uebersicht()
    elif st.session_state.current_view == 'details':
        view_details()

if __name__ == "__main__":
    main()
