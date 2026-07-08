"""
QM-App
======
QM-Tracking auf Basis von qm_model.QualitaetsMangel: Login mit Berechtigung je
Abteilung, ein Planner-artiges Board mit Karten je Status, ein persönliches
Bucket mit offenen QMs zum Übernehmen, und ein Detail-Dialog pro QM.
"""

import statistics
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date, datetime, timedelta
from enum import Enum, auto

from qm_model import (
    QualitaetsMangel, QMStatus, VALID_TRANSITIONS, HistoryEntryType,
    HAUPTKATEGORIEN, WUNSCH_ODER_MANGEL_OPTIONEN, SERIE_ODER_EINZELFALL_OPTIONEN,
    MINOR_MAJOR_OPTIONEN,
)
from qm_data_reader import load_qm_data

# Mitarbeiterlisten (fiktiv, bewusst kurz gehalten - nur Beispiele)
_MITARBEITER_KUNDENDIENST = ['Schilling Curdin', 'Mettler Walo']
_MITARBEITER_HOTLINE = ['Iseli Fritz', 'Scherrer Duri']
_MITARBEITER_VERKAUF = ['Gonseth Quirin', 'Berthoud Valerio']
_MITARBEITER_MONTAGE = ['Vial Kaspar', 'Knecht Thom']
_MITARBEITER_INBETRIEBNAHME = ['Fivaz Remo', 'Landolt Marco']
_MITARBEITER_KONSTRUKTION = ['Sturzenegger Meinrad', 'Hirschy Mario']
_MITARBEITER_VORFUHRUNG = ['Zbinden Elio', 'Jaton Jodok']
_MITARBEITER_SOFTWARE_ENT = ['Iseli Fritz', 'Aebischer Silvio', 'Wicht Klemens']
_MITARBEITER_ELEKTRO_ENT = ['Nydegger Orlando', 'Vionnet Pankraz']
_MITARBEITER_ENTWICKLUNGSLEITUNG = ['Chappuis Placi']
_MITARBEITER_ENTWICKLUNG_APP_TEST = ['Wanner Andri', 'Ruckstuhl Leandro']
_MITARBEITER_QS = ['Naef Ursin', 'Iseli Fritz', 'Schoch Jodok']
_MITARBEITER_GESCHAFTSLEITUNG = ['Piller Nils', 'Thommen Silas']
_MITARBEITER_IT = ['Gassmann Flavio', 'Etter Kuere']
_MITARBEITER_PRODUKTIONSLEITUNG = ['Schoch Jodok']


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
    VORFUEHRUNG = {"name": "Vorführung", "Mitarbeiter": _MITARBEITER_VORFUHRUNG, "Rechte": {RECHTE.ERFASSEN}}
    SOFTWARE_ENTWICKLUNG = {"name": "Softwareentwicklung", "Mitarbeiter": _MITARBEITER_SOFTWARE_ENT, "Rechte": {RECHTE.ERFASSEN, RECHTE.BEARBEITEN}}
    ELEKTRO_ENTWICKLUNG = {"name": "Elektroentwicklung", "Mitarbeiter": _MITARBEITER_ELEKTRO_ENT, "Rechte": {RECHTE.ERFASSEN, RECHTE.BEARBEITEN}}
    ENTWICKLUNGSLEITUNG = {"name": "Entwicklungsleitung", "Mitarbeiter": _MITARBEITER_ENTWICKLUNGSLEITUNG, "Rechte": {RECHTE.ERFASSEN, RECHTE.BEARBEITEN, RECHTE.ZUWEISEN, RECHTE.STATISTIK}}
    ENTWICKLUNG_APPLIKATION_TEST = {"name": "Entwicklung Anwendungstest", "Mitarbeiter": _MITARBEITER_ENTWICKLUNG_APP_TEST, "Rechte": {RECHTE.ERFASSEN, RECHTE.BEARBEITEN}}
    QS = {"name": "Qualitätssicherung", "Mitarbeiter": _MITARBEITER_QS, "Rechte": {RECHTE.ERFASSEN, RECHTE.BEARBEITEN, RECHTE.ZUWEISEN, RECHTE.STATISTIK}}
    GESCHAFTSLEITUNG = {"name": "Geschäftsleitung", "Mitarbeiter": _MITARBEITER_GESCHAFTSLEITUNG, "Rechte": {RECHTE.ERFASSEN, RECHTE.BEARBEITEN, RECHTE.ZUWEISEN, RECHTE.STATISTIK, RECHTE.SUPERUSER}}
    IT = {"name": "Informatik", "Mitarbeiter": _MITARBEITER_IT, "Rechte": {RECHTE.ERFASSEN, RECHTE.BEARBEITEN, RECHTE.ZUWEISEN, RECHTE.STATISTIK, RECHTE.SUPERUSER}}
    PRODUKTIONSLEITUNG = {"name": "Produktionsleitung", "Mitarbeiter": _MITARBEITER_PRODUKTIONSLEITUNG, "Rechte": {RECHTE.ERFASSEN, RECHTE.STATISTIK}}


# Ordnet die beim Erfassen gewählte Hauptkategorie der fachlich zuständigen Abteilung zu
# (Grundlage für "Mein Bucket").
KATEGORIE_ABTEILUNG = {
    "Software": ABTEILUNGEN.SOFTWARE_ENTWICKLUNG,
    "Mechanik": ABTEILUNGEN.KONSTRUKTION,
    "Elektro": ABTEILUNGEN.ELEKTRO_ENTWICKLUNG,
    "Organisatorisch": ABTEILUNGEN.QS,
    "Qualität": ABTEILUNGEN.QS,
    "Applikation": ABTEILUNGEN.ENTWICKLUNG_APPLIKATION_TEST,
}

STATUS_ICON = {
    QMStatus.NEU.value: "🆕",
    QMStatus.IN_PRUEFUNG.value: "🔍",
    QMStatus.ZUGEWIESEN.value: "👤",
    QMStatus.IN_BEARBEITUNG.value: "🔧",
    QMStatus.PAUSIERT.value: "⏸️",
    QMStatus.BEHOBEN.value: "🔨",
    QMStatus.ABGESCHLOSSEN.value: "✅",
    QMStatus.WIEDEREROEFFNET.value: "🔄",
    QMStatus.ABGEBROCHEN.value: "❌",
}
PRIORITAET_FARBE = {"Niedrig": "gray", "Mittel": "blue", "Hoch": "orange", "Kritisch": "red"}

# Icon je History-Eintragstyp, für die Verlaufs-Timeline.
VERLAUF_ICON = {
    "erstellt": "🆕",
    "status_geaendert": "➡️",
    "zugewiesen": "👤",
    "kommentar": "💬",
    "bearbeitet": "✏️",
    "pausiert": "⏸️",
    "fortgesetzt": "▶️",
    "wiedereroeffnet": "🔄",
    "abgebrochen": "❌",
}

# Hauptpfad ohne Nebenzustände/Schlaufen - für die kompakte Übersicht in der Detailansicht.
PROZESS_HAUPTPFAD = [
    QMStatus.NEU.value, QMStatus.IN_PRUEFUNG.value, QMStatus.ZUGEWIESEN.value,
    QMStatus.IN_BEARBEITUNG.value, QMStatus.BEHOBEN.value, QMStatus.ABGESCHLOSSEN.value,
]
HAUPTPFAD_KANTEN = set(zip(PROZESS_HAUPTPFAD, PROZESS_HAUPTPFAD[1:]))
HAUPTPFAD_ANZEIGE_STATUS = {
    QMStatus.PAUSIERT.value: QMStatus.IN_BEARBEITUNG.value,
    QMStatus.WIEDEREROEFFNET.value: QMStatus.IN_PRUEFUNG.value,
}

# Felder je Prozessschritt - gleichzeitig die editierbaren Felder solange der QM in
# diesem Status ist, UND die Gruppen für die "Alle Angaben"-Ansicht.
STATUS_FELDER = {
    QMStatus.NEU.value: [
        "titel", "beschreibung", "hauptkategorie", "wunsch_oder_mangel", "sicherheitsrelevant",
        "erfasser_kuerzel", "erfasser_abteilung", "involvierte",
        "ist_software", "plc", "plc_version", "nc", "nc_version", "mcm",
        "maschinentyp", "serie_oder_einzelfall",
        "kundenrueckmeldung_noetig", "ticket_nr_intern", "kontaktperson_servicetechniker",
    ],
    QMStatus.IN_PRUEFUNG.value: ["minor_major", "prioritaet", "termin_geplante_umsetzung"],
    QMStatus.ZUGEWIESEN.value: ["zugewiesen_an", "abteilung", "faellig_am"],
    QMStatus.IN_BEARBEITUNG.value: ["bearbeitung_extern", "ticket_nr_extern", "korrespondenz_extern", "statuseintraege_vorhanden", "anleitung_link"],
    QMStatus.BEHOBEN.value: ["software_referenz_release", "hardware_aenderungsindex"],
}

# Felder, die erst erscheinen, wenn ihr Auslöser-Feld True ist (z.B. PLC Version nur,
# wenn PLC angekreuzt ist). Der Auslöser muss in der jeweiligen Feldliste vorher stehen.
FELD_ABHAENGIGKEIT = {
    "plc": "ist_software",
    "nc": "ist_software",
    "mcm": "ist_software",
    "plc_version": "plc",
    "nc_version": "nc",
    "ticket_nr_intern": "kundenrueckmeldung_noetig",
    "kontaktperson_servicetechniker": "kundenrueckmeldung_noetig",
    "ticket_nr_extern": "bearbeitung_extern",
    "korrespondenz_extern": "bearbeitung_extern",
}

# Werden nie als Eingabefeld angezeigt, sondern automatisch aus den Login-Infos gesetzt.
AUTOMATISCHE_FELDER = {"erfasser_kuerzel", "erfasser_abteilung"}

TERMINAL_STATUS = {QMStatus.BEHOBEN.value, QMStatus.ABGESCHLOSSEN.value, QMStatus.ABGEBROCHEN.value}

ABTEILUNGSNAMEN = [a.value["name"] for a in ABTEILUNGEN]

FORMULAR_CONFIG = {
    "titel": {"label": "Titel", "type": "text", "required": True, "placeholder": "z.B. Fehlerhafte Anzeige im Dashboard"},
    "beschreibung": {"label": "Mangelbeschreibung", "type": "textarea", "required": True, "placeholder": "Was ist das Problem?"},
    "hauptkategorie": {"label": "Hauptkategorie", "type": "selectbox", "required": True, "options": HAUPTKATEGORIEN},
    "wunsch_oder_mangel": {"label": "Wunsch oder Mangel", "type": "selectbox", "options": WUNSCH_ODER_MANGEL_OPTIONEN},
    "sicherheitsrelevant": {"label": "Sicherheitsrelevant", "type": "checkbox"},
    "erfasser_kuerzel": {"label": "Erfasser Kürzel", "type": "text"},
    "erfasser_abteilung": {"label": "Erfasser Abteilung", "type": "selectbox", "options": ABTEILUNGSNAMEN},
    "involvierte": {"label": "Involvierte (besprochen mit)", "type": "text"},
    "ist_software": {"label": "Software betroffen?", "type": "checkbox"},
    "plc": {"label": "PLC betroffen?", "type": "checkbox"},
    "plc_version": {"label": "PLC Version", "type": "text"},
    "nc": {"label": "NC betroffen?", "type": "checkbox"},
    "nc_version": {"label": "NC Version", "type": "text"},
    "mcm": {"label": "MCM betroffen?", "type": "checkbox"},
    "maschinentyp": {"label": "Maschinentyp", "type": "text"},
    "serie_oder_einzelfall": {"label": "Serie oder Einzelfall", "type": "selectbox", "options": SERIE_ODER_EINZELFALL_OPTIONEN},
    "kundenrueckmeldung_noetig": {"label": "Kundenrückmeldung nötig?", "type": "checkbox"},
    "ticket_nr_intern": {"label": "Ticket Nr. (intern)", "type": "text"},
    "kontaktperson_servicetechniker": {"label": "Kontaktperson/Servicetechniker", "type": "text"},
    "minor_major": {"label": "Minor / Major", "type": "selectbox", "options": MINOR_MAJOR_OPTIONEN},
    "prioritaet": {"label": "Priorität", "type": "selectbox", "options": ["Niedrig", "Mittel", "Hoch", "Kritisch"]},
    "termin_geplante_umsetzung": {"label": "Termin geplante Umsetzung", "type": "date"},
    "zugewiesen_an": {"label": "Zugewiesen an", "type": "text"},
    "abteilung": {"label": "Zuständige Abteilung", "type": "text"},
    "faellig_am": {"label": "Fällig am", "type": "date"},
    "bearbeitung_extern": {"label": "Bearbeitung extern?", "type": "checkbox"},
    "ticket_nr_extern": {"label": "Ticket Nr. (extern)", "type": "text"},
    "korrespondenz_extern": {"label": "Korrespondenz", "type": "textarea"},
    "statuseintraege_vorhanden": {"label": "Statuseinträge vorhanden?", "type": "checkbox"},
    "anleitung_link": {"label": "Anleitung (Link)", "type": "text"},
    "software_referenz_release": {"label": "Software-Referenz zu Release", "type": "text"},
    "hardware_aenderungsindex": {"label": "Hardware-Änderungsindex", "type": "text"},
}


@st.cache_data
def lade_sample_daten():
    return load_qm_data()


def init_state():
    if "qm_liste" not in st.session_state:
        st.session_state.qm_liste = lade_sample_daten()
    if "current_user" not in st.session_state:
        st.session_state.current_user = None
        st.session_state.current_abteilung_key = None
    if "view" not in st.session_state:
        st.session_state.view = "liste"
    if "detail_qm_id" not in st.session_state:
        st.session_state.detail_qm_id = None
    if "detail_bearbeiten" not in st.session_state:
        st.session_state.detail_bearbeiten = False


def aktueller_user():
    return st.session_state.current_user


def aktuelle_abteilung():
    # ABTEILUNGEN wird bei jedem Rerun neu definiert - darum hier per Name aus der
    # aktuellen Klasse auflösen statt das Enum-Mitglied selbst in session_state abzulegen.
    key = st.session_state.current_abteilung_key
    return ABTEILUNGEN[key] if key else None


def hat_recht(recht):
    abteilung = aktuelle_abteilung()
    if not abteilung:
        return False
    rechte = abteilung.value["Rechte"]
    return RECHTE.SUPERUSER in rechte or recht in rechte


def nur_erfasser(abteilung=None):
    # Abteilungen wie Montage/Kundendienst haben ausschliesslich ERFASSEN: für sie ist das
    # Board/Bucket/Statistik nur Ballast - sie sollen einfach nur einen QM melden können.
    abteilung = abteilung or aktuelle_abteilung()
    return bool(abteilung) and abteilung.value["Rechte"] == {RECHTE.ERFASSEN}


def hat_bucket(abteilung=None):
    # Bucket/Abteilungs-Ansicht nur zeigen, wenn die Abteilung auch tatsächlich Ziel
    # einer Kategorie ist - sonst ist sie immer leer und damit nutzlos.
    abteilung = abteilung or aktuelle_abteilung()
    if not abteilung:
        return False
    rechte = abteilung.value["Rechte"]
    darf_bearbeiten = RECHTE.SUPERUSER in rechte or RECHTE.BEARBEITEN in rechte
    return darf_bearbeiten and abteilung in KATEGORIE_ABTEILUNG.values()


def finde_qm(qm_id):
    for qm in st.session_state.qm_liste:
        if qm.qm_id == qm_id:
            return qm
    return None


def status_ereignis(qm, status_wert):
    # "Neu" hat keinen eigenen status_geaendert-Eintrag - der erste History-Eintrag
    # (erstellt) ist gleichzeitig das Erreichen von "Neu".
    if status_wert == QMStatus.NEU.value:
        return qm.history[0] if qm.history else None
    for h in qm.history:
        if h.neuer_wert == status_wert:
            return h
    return None


def status_zeitpunkt(qm, status_wert):
    ereignis = status_ereignis(qm, status_wert)
    return ereignis.timestamp if ereignis else None


def naechste_qm_id():
    ids = [qm.qm_id for qm in st.session_state.qm_liste]
    return max(ids, default=0) + 1


def naechste_qm_nummer():
    # Format JJQM1XXXX: 2-stelliges Jahr + QM + laufende Nummer ab 10000.
    jahr_kurz = date.today().year % 100
    return f"{jahr_kurz:02d}QM{9999 + naechste_qm_id()}"


def kuerzel(name):
    return "".join(w[0] for w in name.split()).upper()


def render_field(name, config, value, key):
    label = config["label"] + (" *" if config.get("required") else "")
    typ = config["type"]
    if typ == "text":
        return st.text_input(label, value=value or "", placeholder=config.get("placeholder", ""), key=key)
    if typ == "textarea":
        return st.text_area(label, value=value or "", placeholder=config.get("placeholder", ""), key=key)
    if typ == "selectbox":
        options = config["options"]
        index = options.index(value) if value in options else 0
        return st.selectbox(label, options, index=index, key=key)
    if typ == "checkbox":
        return st.checkbox(label, value=bool(value), key=key)
    if typ == "date":
        return st.date_input(label, value=value or date.today(), key=key)
    return value


def render_feld_gruppe(felder, werte_quelle, key_prefix):
    """Rendert Felder nacheinander (kein st.form, damit Checkboxen sofort einen Rerun
    auslösen). Abhängige Felder (FELD_ABHAENGIGKEIT) erscheinen erst, wenn ihr Auslöser
    - der davor in derselben Liste gerendert wurde - aktuell True ist."""
    werte = {}
    for f in felder:
        if f in AUTOMATISCHE_FELDER:
            continue
        trigger = FELD_ABHAENGIGKEIT.get(f)
        if trigger and not werte.get(trigger):
            continue
        werte[f] = render_field(f, FORMULAR_CONFIG[f], werte_quelle(f), key=f"{key_prefix}_{f}")
    return werte


def render_erfassung_layout(werte_quelle, editierbar, key_prefix="erfassung"):
    """Feste, mehrspaltige Ansicht der Erfassungs-Felder (Grunddaten, Software-Details,
    Kundenrückmeldung) - für das Erfassungsformular UND den 'Neu'-Tab der Detailansicht,
    je nach `editierbar` als Eingabefelder oder als reiner Text."""

    def feld(name):
        roh = werte_quelle(name)
        if editierbar:
            return render_field(name, FORMULAR_CONFIG[name], roh, key=f"{key_prefix}_{name}")
        anzeige = "Ja" if roh is True else "Nein" if roh is False else roh
        st.write(f"**{FORMULAR_CONFIG[name]['label']}:** {anzeige if anzeige not in (None, '') else '–'}")
        return roh

    werte = {}
    st.caption("Grunddaten")
    c1, c2 = st.columns(2)
    with c1:
        werte["titel"] = feld("titel")
        werte["hauptkategorie"] = feld("hauptkategorie")
        werte["wunsch_oder_mangel"] = feld("wunsch_oder_mangel")
        werte["sicherheitsrelevant"] = feld("sicherheitsrelevant")
    with c2:
        werte["beschreibung"] = feld("beschreibung")
        werte["involvierte"] = feld("involvierte")

    st.divider()
    st.caption("Software-Details")
    c3, c4 = st.columns(2)
    with c3:
        werte["ist_software"] = feld("ist_software")
        if werte["ist_software"]:
            werte["plc"] = feld("plc")
            if werte["plc"]:
                werte["plc_version"] = feld("plc_version")
            werte["nc"] = feld("nc")
            if werte["nc"]:
                werte["nc_version"] = feld("nc_version")
            werte["mcm"] = feld("mcm")
    with c4:
        werte["maschinentyp"] = feld("maschinentyp")
        werte["serie_oder_einzelfall"] = feld("serie_oder_einzelfall")

    st.divider()
    st.caption("Kundenrückmeldung")
    werte["kundenrueckmeldung_noetig"] = feld("kundenrueckmeldung_noetig")
    if werte["kundenrueckmeldung_noetig"]:
        c5, c6 = st.columns(2)
        with c5:
            werte["ticket_nr_intern"] = feld("ticket_nr_intern")
        with c6:
            werte["kontaktperson_servicetechniker"] = feld("kontaktperson_servicetechniker")

    return werte


def oeffne_details(qm_id):
    st.session_state.detail_qm_id = qm_id
    st.session_state.detail_bearbeiten = False


# ---------- Login ----------

def view_login():
    _, mitte, _ = st.columns([1, 1, 1])
    with mitte:
        st.title("🔐 Anmeldung")
        abteilung = st.selectbox("Abteilung", list(ABTEILUNGEN), format_func=lambda a: a.value["name"])
        person = st.selectbox("Mitarbeiter", abteilung.value["Mitarbeiter"])
        if st.button("Anmelden", type="primary", use_container_width=True):
            st.session_state.current_user = person
            st.session_state.current_abteilung_key = abteilung.name
            if nur_erfasser(abteilung):
                st.session_state.view = "meine_qms"
            elif hat_bucket(abteilung):
                st.session_state.view = "abteilung"
            else:
                st.session_state.view = "liste"
            st.rerun()


# ---------- Status ändern ----------

def setze_status(qm, ziel, user):
    if ziel == QMStatus.PAUSIERT.value:
        qm.pause(user=user)
    elif qm.status == QMStatus.PAUSIERT.value and ziel == QMStatus.IN_BEARBEITUNG.value:
        qm.resume(user=user)
    elif ziel == QMStatus.ABGEBROCHEN.value:
        qm.cancel(user=user)
    elif qm.status == QMStatus.ABGESCHLOSSEN.value and ziel == QMStatus.WIEDEREROEFFNET.value:
        qm.reopen(user=user)
    else:
        qm.change_status(ziel, user=user)


def render_status_wechsel(qm):
    if not hat_recht(RECHTE.BEARBEITEN):
        return
    optionen = [qm.status] + VALID_TRANSITIONS.get(qm.status, [])
    c1, c2 = st.columns([3, 1])
    auswahl = c1.selectbox(
        "Status", optionen, index=0, key=f"status_sel_{qm.qm_id}",
        format_func=lambda s: f"{STATUS_ICON.get(s, '📌')} {s}", label_visibility="collapsed",
    )
    c2.write("")
    if c2.button("Anwenden", key=f"status_apply_{qm.qm_id}", use_container_width=True, disabled=auswahl == qm.status):
        setze_status(qm, auswahl, aktueller_user())
        st.rerun()


# ---------- Karten (wiederverwendet in Meine QMs, Abteilung, Statistik-Detail) ----------

def render_karte(qm, key_prefix, uebernehmen_erlaubt=False):
    with st.container(border=True):
        st.markdown(f"**{qm.qm_nummer}**  \n{qm.titel}")
        st.badge(qm.prioritaet, color=PRIORITAET_FARBE.get(qm.prioritaet, "gray"))
        st.caption(f"{STATUS_ICON.get(qm.status, '')} {qm.status} · {qm.hauptkategorie}")
        if uebernehmen_erlaubt and hat_recht(RECHTE.BEARBEITEN):
            c1, c2 = st.columns(2)
            if c1.button("Öffnen", key=f"{key_prefix}_open_{qm.qm_id}", use_container_width=True):
                oeffne_details(qm.qm_id)
            if c2.button("🙋 Übernehmen", key=f"{key_prefix}_take_{qm.qm_id}", use_container_width=True):
                uebernehmen(qm)
                st.rerun()
        elif st.button("Öffnen", key=f"{key_prefix}_{qm.qm_id}", use_container_width=True):
            oeffne_details(qm.qm_id)


def render_karten_raster(qm_liste, key_prefix, pro_reihe=3, uebernehmen_erlaubt=False):
    if not qm_liste:
        st.caption("Keine.")
        return
    for i in range(0, len(qm_liste), pro_reihe):
        for col, qm in zip(st.columns(pro_reihe), qm_liste[i:i + pro_reihe]):
            with col:
                render_karte(qm, key_prefix=key_prefix, uebernehmen_erlaubt=uebernehmen_erlaubt)


# ---------- Meine QMs (für alle: eigene + zugewiesene) ----------

def view_meine_qms():
    st.header("📄 Meine QMs")
    st.caption("QMs, die du erfasst hast oder die dir zugewiesen sind.")
    if st.button("➕ Neuen QM erfassen", type="primary"):
        st.session_state.view = "neu"
        st.rerun()
    user = aktueller_user()
    meine = [qm for qm in st.session_state.qm_liste if qm.ersteller == user or qm.zugewiesen_an == user]
    if not meine:
        st.info("Du bist aktuell an keinem QM beteiligt.")
        return
    render_karten_raster(meine, key_prefix="meine")


# ---------- Alle QMs (filterbare Liste, allgemeine Übersicht) ----------

def view_liste():
    st.header("📋 Alle QMs")
    c1, c2, c3 = st.columns(3)
    status_filter = c1.multiselect("Status", [s.value for s in QMStatus])
    kategorie_filter = c2.multiselect("Kategorie", HAUPTKATEGORIEN)
    suche = c3.text_input("Suche", placeholder="Titel oder Nummer...")

    qm_liste = st.session_state.qm_liste
    if status_filter:
        qm_liste = [qm for qm in qm_liste if qm.status in status_filter]
    if kategorie_filter:
        qm_liste = [qm for qm in qm_liste if qm.hauptkategorie in kategorie_filter]
    if suche:
        s = suche.lower()
        qm_liste = [qm for qm in qm_liste if s in qm.titel.lower() or s in qm.qm_nummer.lower()]

    st.caption(f"{len(qm_liste)} von {len(st.session_state.qm_liste)} QMs")
    kopf = st.columns([1.3, 3, 1.4, 1.3, 1, 1])
    for col, label in zip(kopf, ["Nummer", "Titel", "Status", "Kategorie", "Priorität", ""]):
        col.markdown(f"**{label}**")
    for qm in qm_liste:
        c1, c2, c3, c4, c5, c6 = st.columns([1.3, 3, 1.4, 1.3, 1, 1])
        c1.write(qm.qm_nummer)
        c2.write(qm.titel)
        c3.write(f"{STATUS_ICON.get(qm.status, '')} {qm.status}")
        c4.write(qm.hauptkategorie)
        c5.write(qm.prioritaet)
        if c6.button("Öffnen", key=f"liste_{qm.qm_id}", use_container_width=True):
            oeffne_details(qm.qm_id)


# ---------- Mein Bucket / Meine Abteilung ----------

def uebernehmen(qm):
    user = aktueller_user()
    if qm.status == QMStatus.NEU.value:
        qm.change_status(QMStatus.IN_PRUEFUNG.value, user=user)
    qm.assign_to(user, aktuelle_abteilung().value["name"], user=user)
    qm.change_status(QMStatus.ZUGEWIESEN.value, user=user)


def letzte_aktivitaet(qm):
    return qm.history[-1].timestamp if qm.history else qm.erstellt_am


def render_erledigt_bereich(erledigte, key_prefix):
    tage = st.slider("Zeitraum (Tage)", 1, 90, 14, key=f"{key_prefix}_tage")
    grenze = datetime.now() - timedelta(days=tage)
    aktuelle = [qm for qm in erledigte if letzte_aktivitaet(qm) >= grenze]
    aeltere = [qm for qm in erledigte if letzte_aktivitaet(qm) < grenze]
    render_karten_raster(aktuelle, key_prefix=f"{key_prefix}_aktuell")
    if aeltere:
        with st.expander(f"Ältere anzeigen ({len(aeltere)})"):
            render_karten_raster(aeltere, key_prefix=f"{key_prefix}_alt")


def view_bucket():
    abteilung = aktuelle_abteilung()
    st.header(f"🪣 {abteilung.value['name']}")
    st.caption("Was in deiner Abteilung läuft - Details ansehen, bearbeiten, übernehmen oder zuweisen.")

    relevante = [qm for qm in st.session_state.qm_liste if KATEGORIE_ABTEILUNG.get(qm.hauptkategorie) == abteilung]
    nicht_zugewiesen = [qm for qm in relevante if qm.status in (QMStatus.NEU.value, QMStatus.IN_PRUEFUNG.value) and not qm.zugewiesen_an]
    zugewiesen = [qm for qm in relevante if qm.status == QMStatus.ZUGEWIESEN.value]
    in_bearbeitung = [qm for qm in relevante if qm.status in (QMStatus.IN_BEARBEITUNG.value, QMStatus.PAUSIERT.value)]
    erledigt = [qm for qm in relevante if qm.status in (QMStatus.BEHOBEN.value, QMStatus.ABGESCHLOSSEN.value, QMStatus.ABGEBROCHEN.value)]

    st.subheader(f"🆕 Noch nicht zugewiesen ({len(nicht_zugewiesen)})")
    render_karten_raster(nicht_zugewiesen, key_prefix="abt_frei", pro_reihe=2, uebernehmen_erlaubt=True)

    st.divider()
    st.subheader(f"👤 Zugewiesen ({len(zugewiesen)})")
    render_karten_raster(zugewiesen, key_prefix="abt_zugewiesen")

    st.divider()
    st.subheader(f"🔧 In Bearbeitung ({len(in_bearbeitung)})")
    render_karten_raster(in_bearbeitung, key_prefix="abt_bearbeitung")

    st.divider()
    st.subheader(f"✅ Abgeschlossen ({len(erledigt)})")
    render_erledigt_bereich(erledigt, key_prefix="abt_erledigt")


# ---------- Neuer QM ----------

def view_neuer_qm():
    st.header("➕ Neuen Qualitätsmangel erfassen")
    st.caption(f"Erfasst durch {aktueller_user()} ({aktuelle_abteilung().value['name']})")

    werte = render_erfassung_layout(lambda f: None, editierbar=True, key_prefix="neu")

    if not st.button("✅ Erfassen", type="primary"):
        return
    if not werte.get("titel") or not werte.get("beschreibung"):
        st.error("Titel und Mangelbeschreibung sind Pflichtfelder.")
        return

    qm = QualitaetsMangel(
        qm_id=naechste_qm_id(),
        qm_nummer=naechste_qm_nummer(),
        ersteller=aktueller_user(),
        erfasser_kuerzel=kuerzel(aktueller_user()),
        erfasser_abteilung=aktuelle_abteilung().value["name"],
        **werte,
    )
    st.session_state.qm_liste.append(qm)
    st.success(f"{qm.qm_nummer} wurde erfasst.")
    if nur_erfasser():
        st.session_state.view = "meine_qms"
    oeffne_details(qm.qm_id)


# ---------- Detail-Dialog ----------

def render_kurzfakten(qm):
    # Kompakte, immer sichtbare Zusammenfassung - man sieht sofort worum es geht,
    # bevor man in die Details/Tabs wechselt.
    fakten = [qm.hauptkategorie, f"Priorität: {qm.prioritaet}"]
    if qm.zugewiesen_an:
        fakten.append(f"Zugewiesen an {qm.zugewiesen_an}")
    if qm.faellig_am:
        fakten.append(f"Fällig am {qm.faellig_am:%d.%m.%Y}")
    fakten.append(f"Erfasst von {qm.erfasser_kuerzel or qm.ersteller}")
    st.caption(" · ".join(fakten))


def render_gruppe_tab(qm, gruppen_key, felder, editierbar):
    # Automatische Felder (Erfasser Kürzel/Abteilung) immer nur lesend zeigen.
    for f in [f for f in felder if f in AUTOMATISCHE_FELDER]:
        st.write(f"**{FORMULAR_CONFIG[f]['label']}:** {getattr(qm, f) or '–'}")

    if gruppen_key == QMStatus.NEU.value:
        werte = render_erfassung_layout(lambda f: getattr(qm, f), editierbar, key_prefix=f"tab_{qm.qm_id}")
    elif editierbar:
        werte = render_feld_gruppe(felder, lambda f: getattr(qm, f), key_prefix=f"tab_{qm.qm_id}_{gruppen_key}")
    else:
        werte = {}
        for f in felder:
            if f in AUTOMATISCHE_FELDER:
                continue
            trigger = FELD_ABHAENGIGKEIT.get(f)
            if trigger and not getattr(qm, trigger):
                continue
            wert = getattr(qm, f)
            if isinstance(wert, bool):
                wert = "Ja" if wert else "Nein"
            st.write(f"**{FORMULAR_CONFIG[f]['label']}:** {wert if wert not in (None, '') else '–'}")

    if editierbar and st.button("💾 Speichern", key=f"tab_speichern_{qm.qm_id}_{gruppen_key}"):
        for f, w in werte.items():
            setattr(qm, f, w)
        qm.add_history_entry(HistoryEntryType.BEARBEITET.value, "Angaben aktualisiert", user=aktueller_user())
        st.session_state.detail_bearbeiten = False
        st.rerun()


def _prozess_node_farbe(qm, status, besucht):
    if status == qm.status:
        return "#E45756" if status == QMStatus.ABGEBROCHEN.value else "#F58518"
    if status in besucht:
        return "#54A24B"
    return None  # noch offen - bleibt weiss


def render_prozess_uebersicht(qm):
    # Kompakte, rein lineare Ansicht: nur Erfassen -> Abgeschlossen, ohne
    # Nebenzustände/Schlaufen - Platz direkt in der Detailansicht. Die vollständige
    # Karte mit Pausiert/Abgebrochen/Wiedereröffnet gibt es im Tab "Ablauf".
    aktueller_hauptschritt = HAUPTPFAD_ANZEIGE_STATUS.get(qm.status, qm.status)
    besucht = {QMStatus.NEU.value} | {h.neuer_wert for h in qm.history if h.neuer_wert in PROZESS_HAUPTPFAD}
    gegangene_kanten = {(h.alter_wert, h.neuer_wert) for h in qm.history if h.alter_wert and h.neuer_wert}

    zeilen = [
        "digraph {", "rankdir=LR;", 'bgcolor="transparent"; nodesep=0.2; ranksep=1.7;',
        'node [shape=box, style="rounded,filled", fontname="Arial", fontsize=8, margin="0.04,0.02"];',
        'edge [color="#cccccc", arrowsize=0.5, penwidth=0.8];',
    ]
    for status in PROZESS_HAUPTPFAD:
        label = f"{STATUS_ICON.get(status, '')}\\n{status}"
        aktiv = status == aktueller_hauptschritt and qm.status not in (QMStatus.ABGEBROCHEN.value,)
        farbe = ("#F58518" if aktiv else None) or _prozess_node_farbe(qm, status, besucht)
        if farbe:
            zeilen.append(f'"{status}" [label="{label}", fillcolor="{farbe}", color="{farbe}", fontcolor="white"];')
        else:
            zeilen.append(f'"{status}" [label="{label}", fillcolor="white", color="#999999", fontcolor="#555555"];')
    for von, ziel in HAUPTPFAD_KANTEN:
        if (von, ziel) in gegangene_kanten:
            zeilen.append(f'"{von}" -> "{ziel}" [color="#4C78A8", penwidth=1.6, arrowsize=0.6];')
        else:
            zeilen.append(f'"{von}" -> "{ziel}";')
    zeilen.append("}")

    st.graphviz_chart("\n".join(zeilen), width="stretch")
    if qm.status == QMStatus.ABGEBROCHEN.value:
        st.caption("❌ Abgebrochen - Details und vollständiger Ablauf im Tab \"Ablauf\".")
    elif qm.status == QMStatus.PAUSIERT.value:
        st.caption("⏸️ Aktuell pausiert - Details im Tab \"Ablauf\".")


def render_prozess_diagramm(qm):
    # Vollständiger Prozessgraph (alle Status + alle erlaubten Übergänge aus
    # VALID_TRANSITIONS) - einfache Schritte von oben nach unten, ohne Bahnen.
    # Farbe zeigt erledigt/aktuell/offen, die blaue Linie den tatsächlich
    # gegangenen Weg dieses QMs.
    besucht = {QMStatus.NEU.value} | {h.neuer_wert for h in qm.history if h.neuer_wert}
    gegangene_kanten = {(h.alter_wert, h.neuer_wert) for h in qm.history if h.alter_wert and h.neuer_wert}

    zeilen = [
        "digraph {", "rankdir=TB;", 'bgcolor="transparent"; nodesep=0.25; ranksep=0.3;',
        'node [fontname="Arial", fontsize=8, margin="0.04,0.02", fixedsize=false, width=0, height=0];',
        'edge [color="#cccccc", arrowsize=0.5, fontsize=8, penwidth=0.8];',
    ]

    for status in [s.value for s in QMStatus]:
        icon = STATUS_ICON.get(status, "")
        ereignis = status_ereignis(qm, status)
        label = f"{icon}\\n{status}" + (f"\\n{ereignis.timestamp:%d.%m.%y}" if ereignis else "")
        form = "circle" if status == QMStatus.NEU.value else "doublecircle" if status in (QMStatus.ABGESCHLOSSEN.value, QMStatus.ABGEBROCHEN.value) else "box"
        stil = "filled" if form == "box" else "filled,bold"
        farbe = _prozess_node_farbe(qm, status, besucht)
        if farbe:
            zeilen.append(f'"{status}" [label="{label}", shape={form}, style="{stil}", fillcolor="{farbe}", color="{farbe}", fontcolor="white"];')
        else:
            zeilen.append(f'"{status}" [label="{label}", shape={form}, style="{stil}", fillcolor="white", color="#999999", fontcolor="#555555"];')

    rueckwaerts = {(QMStatus.PAUSIERT.value, QMStatus.IN_BEARBEITUNG.value), (QMStatus.WIEDEREROEFFNET.value, QMStatus.IN_PRUEFUNG.value)}
    for von, ziele in VALID_TRANSITIONS.items():
        for ziel in ziele:
            attrs = []
            if (von, ziel) in gegangene_kanten:
                attrs += ['color="#4C78A8"', "penwidth=1.6", "arrowsize=0.6"]
            if (von, ziel) in HAUPTPFAD_KANTEN:
                attrs.append("weight=10")
            if (von, ziel) in rueckwaerts:
                attrs.append("constraint=false")
            attr_text = f" [{', '.join(attrs)}]" if attrs else ""
            zeilen.append(f'"{von}" -> "{ziel}"{attr_text};')
    zeilen.append("}")

    st.graphviz_chart("\n".join(zeilen), width=280)
    st.caption("🟠 aktueller Schritt · 🟢 bereits durchlaufen · ⚪ noch offen · blaue Linie = tatsächlicher Weg dieses QMs")


def render_verlauf(qm):
    # Timeline aller Ereignisse - Statuswechsel und Zuweisungen zeigen explizit
    # "von -> zu", damit Personenwechsel sofort auffallen.
    if not qm.history:
        st.info("Keine Historie vorhanden.")
    for h in qm.history:
        icon = VERLAUF_ICON.get(h.typ, "📌")
        with st.container(border=True):
            st.caption(f"{h.timestamp:%d.%m.%Y %H:%M} · {h.user}")
            if h.typ == "zugewiesen":
                st.write(f"{icon} Zuweisung: {h.alter_wert or 'niemand'} → **{h.neuer_wert}**")
            elif h.typ == "status_geaendert":
                von = f"{STATUS_ICON.get(h.alter_wert, '')} {h.alter_wert}"
                zu = f"{STATUS_ICON.get(h.neuer_wert, '')} {h.neuer_wert}"
                st.write(f"{icon} Status: {von} → **{zu}**")
            else:
                st.write(f"{icon} {h.details}")


def render_kommentare(qm):
    for k in qm.kommentare:
        st.markdown(f"_{k.timestamp:%d.%m.%Y %H:%M}_ **{k.user}:** {k.text}")
    if not qm.kommentare:
        st.caption("Noch keine Kommentare.")
    if hat_recht(RECHTE.BEARBEITEN) or hat_recht(RECHTE.ERFASSEN):
        text = st.text_input("Neuer Kommentar", key=f"kommentar_{qm.qm_id}", label_visibility="collapsed", placeholder="Kommentar hinzufügen...")
        if st.button("Hinzufügen", key=f"kommentar_go_{qm.qm_id}") and text:
            qm.add_kommentar(text, user=aktueller_user())
            st.rerun()


def schliesse_dialog():
    st.session_state.detail_qm_id = None
    st.session_state.detail_bearbeiten = False


@st.dialog(" ", width="large", on_dismiss=schliesse_dialog)
def zeige_details(qm_id):
    qm = finde_qm(qm_id)
    if qm is None:
        st.error("QM nicht gefunden.")
        return

    st.subheader(f"{qm.qm_nummer} – {qm.titel}")
    st.caption(qm.beschreibung)
    render_kurzfakten(qm)

    st.markdown(f"**{STATUS_ICON.get(qm.status, '')} {qm.status}**")
    render_status_wechsel(qm)
    if not qm.zugewiesen_an and qm.status not in TERMINAL_STATUS and hat_recht(RECHTE.BEARBEITEN):
        if st.button("🙋 Übernehmen", key=f"dialog_take_{qm.qm_id}"):
            uebernehmen(qm)
            st.rerun()

    render_prozess_uebersicht(qm)

    _, taste = st.columns([5, 1])
    if hat_recht(RECHTE.BEARBEITEN):
        label = "👁️ Ansehen" if st.session_state.detail_bearbeiten else "✏️ Bearbeiten"
        if taste.button(label, key=f"toggle_edit_{qm.qm_id}", use_container_width=True):
            st.session_state.detail_bearbeiten = not st.session_state.detail_bearbeiten
            st.rerun()

    editierbar = hat_recht(RECHTE.BEARBEITEN) and st.session_state.detail_bearbeiten
    tab_namen = [f"{STATUS_ICON.get(status, '')} {status}" for status in STATUS_FELDER] + ["🗺️ Ablauf", "💬 Kommentare", "📜 Verlauf"]
    tabs = st.tabs(tab_namen)
    for tab, (status, felder) in zip(tabs, STATUS_FELDER.items()):
        with tab:
            render_gruppe_tab(qm, status, felder, editierbar)
    with tabs[-3]:
        render_prozess_diagramm(qm)
    with tabs[-2]:
        render_kommentare(qm)
    with tabs[-1]:
        render_verlauf(qm)


# ---------- Statistik ----------

ALT_SCHWELLE_TAGE = 14
SLA_TAGE_KUNDE = 5


def terminal_zeitpunkt(qm):
    return status_zeitpunkt(qm, QMStatus.BEHOBEN.value) or status_zeitpunkt(qm, QMStatus.ABGESCHLOSSEN.value)


def fall_ende(qm):
    # Wie terminal_zeitpunkt, aber auch Abgebrochen zählt als Fallende (für Falldauer/Process Mining -
    # separat gehalten, damit bestehendes SLA/Zeitverlauf-Verhalten unverändert bleibt).
    return (
        status_zeitpunkt(qm, QMStatus.ABGESCHLOSSEN.value)
        or status_zeitpunkt(qm, QMStatus.BEHOBEN.value)
        or status_zeitpunkt(qm, QMStatus.ABGEBROCHEN.value)
    )


# History-Eintragstypen, die einen echten Statuswechsel dokumentieren (im Gegensatz zu
# z.B. Zuweisungs- oder Prioritätsänderungen, die ebenfalls alter_wert/neuer_wert setzen).
STATUS_AENDERUNGS_TYPEN = {
    HistoryEntryType.STATUS_GEAENDERT.value, HistoryEntryType.PAUSIERT.value,
    HistoryEntryType.FORTGESETZT.value, HistoryEntryType.WIEDEREROEFFNET.value,
    HistoryEntryType.ABGEBROCHEN.value,
}


def aktivitaeten_verlauf(qm):
    # (Status, Zeitpunkt-des-Erreichens) je Schritt, chronologisch - Neu + jeder
    # tatsächliche Statuswechsel. Grundlage für Sequenz UND Verweildauer je Schritt.
    verlauf = [(QMStatus.NEU.value, qm.erstellt_am)]
    for h in qm.history:
        if h.typ in STATUS_AENDERUNGS_TYPEN and h.alter_wert and h.neuer_wert:
            verlauf.append((h.neuer_wert, h.timestamp))
    return verlauf


def aktivitaeten_sequenz(qm):
    return [status for status, _ in aktivitaeten_verlauf(qm)]


def fall_dauer_stunden(qm, jetzt):
    ende = fall_ende(qm) or jetzt
    return (ende - qm.erstellt_am).total_seconds() / 3600


def hat_self_loop(sequenz):
    return any(a == b for a, b in zip(sequenz, sequenz[1:]))


def hat_loop(sequenz):
    return len(set(sequenz)) < len(sequenz)


def ist_rework(qm):
    return any(
        h.typ in (HistoryEntryType.PAUSIERT.value, HistoryEntryType.WIEDEREROEFFNET.value)
        for h in qm.history
    )


def ressourcen_anzahl(qm_liste):
    ressourcen = {h.user for qm in qm_liste for h in qm.history if h.user}
    return len(ressourcen)


def berechne_varianten(qm_liste):
    zaehler = {}
    for qm in qm_liste:
        variante = " → ".join(aktivitaeten_sequenz(qm))
        zaehler[variante] = zaehler.get(variante, 0) + 1
    return pd.Series(zaehler, dtype=int).sort_values(ascending=False)


def berechne_dfg(qm_liste):
    kanten = {}
    for qm in qm_liste:
        sequenz = aktivitaeten_sequenz(qm)
        for a, b in zip(sequenz, sequenz[1:]):
            kanten[(a, b)] = kanten.get((a, b), 0) + 1
    return kanten


def berechne_start_end_zaehler(qm_liste):
    start_zaehler, end_zaehler = {}, {}
    for qm in qm_liste:
        sequenz = aktivitaeten_sequenz(qm)
        start_zaehler[sequenz[0]] = start_zaehler.get(sequenz[0], 0) + 1
        if fall_ende(qm):
            end_zaehler[sequenz[-1]] = end_zaehler.get(sequenz[-1], 0) + 1
    return start_zaehler, end_zaehler


def render_dfg(qm_liste, kanten, ausgewaehlt=None):
    # Interaktiver Prozessgraph (Plotly statt Graphviz): Knoten sind echte,
    # klickbare Marker (st.plotly_chart mit on_select) - ein Klick liefert den
    # angeklickten Schritt zurück, damit die Detailanzeige links reagieren kann.
    if not kanten:
        st.info("Keine Daten für den Prozessgraph.")
        return None

    aktivitaeten = sorted({s for kante in kanten for s in kante})
    start_zaehler, end_zaehler = berechne_start_end_zaehler(qm_liste)

    nachfolger = {}
    for a, b in kanten:
        nachfolger.setdefault(a, set()).add(b)

    layer = {s: 1 for s in start_zaehler}
    besucht = set(layer)
    frontier = list(layer)
    while frontier:
        neue_frontier = []
        for a in frontier:
            for b in nachfolger.get(a, ()):
                if b not in besucht:
                    besucht.add(b)
                    layer[b] = layer[a] + 1
                    neue_frontier.append(b)
        frontier = neue_frontier
    for a in aktivitaeten:
        layer.setdefault(a, 1)
    max_layer = max(layer.values())

    je_layer = {}
    for a in aktivitaeten:
        je_layer.setdefault(layer[a], []).append(a)

    pos = {}
    max_pro_layer = 1
    for l, namen in je_layer.items():
        namen.sort()
        n = len(namen)
        max_pro_layer = max(max_pro_layer, n)
        for i, name in enumerate(namen):
            pos[name] = (i - (n - 1) / 2, -l)
    pos["__start__"] = (0, 0)
    pos["__end__"] = (0, -(max_layer + 1))

    akzent, dunkel = "#CC785C", "#3D3929"
    max_kante = max(kanten.values())
    annotationen = []

    def pfeil(von, nach, breite, farbe, opazitaet):
        x0, y0 = pos[von]
        x1, y1 = pos[nach]
        annotationen.append(dict(
            x=x1, y=y1, ax=x0, ay=y0, xref="x", yref="y", axref="x", ayref="y",
            showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=breite, arrowcolor=farbe,
            opacity=opazitaet, standoff=26, startstandoff=26,
        ))

    for status, n in start_zaehler.items():
        pfeil("__start__", status, 1.5, dunkel, 0.6)
    for (a, b), n in kanten.items():
        pfeil(a, b, 1.5 + 3.5 * (n / max_kante), akzent, 0.85)
        mx, my = (pos[a][0] + pos[b][0]) / 2, (pos[a][1] + pos[b][1]) / 2
        annotationen.append(dict(
            x=mx, y=my, text=str(n), showarrow=False, font=dict(size=11, color="#8A5A46"),
            bgcolor="rgba(250,249,245,0.85)",
        ))
    for status, n in end_zaehler.items():
        pfeil(status, "__end__", 1.5, dunkel, 0.6)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=[pos["__start__"][0], pos["__end__"][0]], y=[pos["__start__"][1], pos["__end__"][1]],
        mode="markers+text", text=["Start", "Ende"], textposition="middle center",
        textfont=dict(color="white", size=11),
        marker=dict(size=46, color=dunkel, line=dict(width=0)),
        hoverinfo="text", customdata=[[None], [None]], showlegend=False,
    ))
    fig.add_trace(go.Scatter(
        x=[pos[a][0] for a in aktivitaeten],
        y=[pos[a][1] for a in aktivitaeten],
        mode="markers+text",
        text=[f"{STATUS_ICON.get(a, '')} {a}" for a in aktivitaeten],
        textposition="middle center", textfont=dict(size=11, color=dunkel),
        marker=dict(
            size=58, color="#F0EEE6", symbol="square",
            line=dict(
                color=[dunkel if a == ausgewaehlt else akzent for a in aktivitaeten],
                width=[4 if a == ausgewaehlt else 2 for a in aktivitaeten],
            ),
        ),
        customdata=[[a] for a in aktivitaeten], hoverinfo="text", showlegend=False,
    ))

    fig.update_layout(
        annotations=annotationen,
        xaxis=dict(visible=False, range=[-(max_pro_layer / 2 + 1), max_pro_layer / 2 + 1]),
        yaxis=dict(visible=False, range=[-(max_layer + 1.5), 0.5]),
        margin=dict(l=10, r=10, t=10, b=10),
        height=int(105 * (max_layer + 2)),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        clickmode="event+select",
    )

    event = st.plotly_chart(
        fig, on_select="rerun", selection_mode="points", key="prozess_dfg_klick",
    )
    if event and event.selection and event.selection.points:
        for punkt in event.selection.points:
            customdata = punkt.get("customdata")
            if customdata and customdata[0]:
                return customdata[0]
    return None


def schritt_statistik(qm_liste, schritt, jetzt):
    verweildauern_h = []
    ressourcen = set()
    aktuelle_faelle = []
    for qm in qm_liste:
        verlauf = aktivitaeten_verlauf(qm)
        for i, (status, ts) in enumerate(verlauf):
            if status == schritt:
                ende = verlauf[i + 1][1] if i + 1 < len(verlauf) else jetzt
                verweildauern_h.append((ende - ts).total_seconds() / 3600)
        for h in qm.history:
            if h.neuer_wert == schritt and h.user:
                ressourcen.add(h.user)
        if qm.status == schritt:
            aktuelle_faelle.append(qm)
    return verweildauern_h, ressourcen, aktuelle_faelle


def render_schritt_detail(qm_liste, schritt, kanten, jetzt):
    icon = STATUS_ICON.get(schritt, "")
    st.markdown(f"**{icon} {schritt}**")
    verweildauern_h, ressourcen, aktuelle_faelle = schritt_statistik(qm_liste, schritt, jetzt)

    k1, k2 = st.columns(2)
    k1.metric("Fälle", len(verweildauern_h))
    k2.metric("Ø Dauer", f"{statistics.mean(verweildauern_h) / 24:.1f} Tg" if verweildauern_h else "–")
    k3, k4 = st.columns(2)
    k3.metric("Aktuell hier", len(aktuelle_faelle))
    k4.metric("Ressourcen", len(ressourcen))

    eingehend = sorted(((a, n) for (a, b), n in kanten.items() if b == schritt), key=lambda kv: -kv[1])
    ausgehend = sorted(((b, n) for (a, b), n in kanten.items() if a == schritt), key=lambda kv: -kv[1])
    if eingehend or ausgehend:
        e_spalte, a_spalte = st.columns(2)
        with e_spalte:
            if eingehend:
                st.caption("Eingehend")
                for von, n in eingehend:
                    st.caption(f"⬅️ {von} ({n})")
        with a_spalte:
            if ausgehend:
                st.caption("Ausgehend")
                for ziel, n in ausgehend:
                    st.caption(f"➡️ {ziel} ({n})")

    if aktuelle_faelle:
        st.caption("Aktuell in diesem Schritt")
        for qm in aktuelle_faelle:
            st.caption(f"{qm.qm_nummer} – {qm.titel}")


def render_varianten_chart(qm_liste, top_n=10):
    varianten = berechne_varianten(qm_liste).head(top_n)
    if varianten.empty:
        st.info("Keine Varianten gefunden.")
        return
    st.bar_chart(varianten, horizontal=True, x_label="Anzahl Fälle", y_label="")


def render_dauer_zeitverlauf(qm_liste):
    jetzt = datetime.now()
    daten = [
        {"Abgeschlossen am": fall_ende(qm).date(), "Ø Falldauer (Tage)": fall_dauer_stunden(qm, jetzt) / 24}
        for qm in qm_liste if fall_ende(qm)
    ]
    if not daten:
        st.info("Noch keine abgeschlossenen Fälle für den Zeitverlauf.")
        return
    df = pd.DataFrame(daten).groupby("Abgeschlossen am").mean()
    st.line_chart(df)


def pie_chart(werte, spaltenname):
    df = werte.rename_axis(spaltenname).reset_index(name="Anzahl")
    spec = {
        "mark": {"type": "arc", "innerRadius": 55, "tooltip": True},
        "encoding": {
            "theta": {"field": "Anzahl", "type": "quantitative"},
            "color": {"field": spaltenname, "type": "nominal"},
        },
        "height": 260,
    }
    st.vega_lite_chart(df, spec, use_container_width=True)


def wochen_zaehlung(zeitpunkte):
    if not zeitpunkte:
        return pd.Series(dtype=int)
    serie = pd.Series(pd.to_datetime(zeitpunkte))
    return serie.dt.to_period("W").apply(lambda p: p.start_time).value_counts().sort_index()


def view_statistik():
    st.header("📈 Statistik")
    qm_liste = st.session_state.qm_liste
    heute = datetime.now()

    offene = [qm for qm in qm_liste if qm.status not in TERMINAL_STATUS]
    alte_unbearbeitete = [
        qm for qm in offene
        if qm.status in (QMStatus.NEU.value, QMStatus.IN_PRUEFUNG.value)
        and (heute - qm.erstellt_am).days >= ALT_SCHWELLE_TAGE
    ]
    sicherheitsrelevant_offen = [qm for qm in offene if qm.sicherheitsrelevant]
    kuerzlich_erledigt = [qm for qm in qm_liste if qm.status in TERMINAL_STATUS and (heute - letzte_aktivitaet(qm)).days <= ALT_SCHWELLE_TAGE]

    reaktionszeiten_h, bearbeitungszeiten_h, rueckmeldungszeiten_h = [], [], []
    sla_relevant = sla_getroffen = 0
    for qm in qm_liste:
        zugewiesen_zeit = status_zeitpunkt(qm, QMStatus.ZUGEWIESEN.value)
        if zugewiesen_zeit:
            reaktionszeiten_h.append((zugewiesen_zeit - qm.erstellt_am).total_seconds() / 3600)
        ziel_zeit = terminal_zeitpunkt(qm)
        if zugewiesen_zeit and ziel_zeit and ziel_zeit > zugewiesen_zeit:
            bearbeitungszeiten_h.append((ziel_zeit - zugewiesen_zeit).total_seconds() / 3600)
        if qm.kommentare:
            erster_kommentar = min(k.timestamp for k in qm.kommentare)
            rueckmeldungszeiten_h.append((erster_kommentar - qm.erstellt_am).total_seconds() / 3600)
        if qm.kundenrueckmeldung_noetig:
            sla_relevant += 1
            if ziel_zeit and (ziel_zeit - qm.erstellt_am).days <= SLA_TAGE_KUNDE:
                sla_getroffen += 1

    mittel = lambda werte: sum(werte) / len(werte) if werte else None

    tab_kunde, tab_intern, tab_prozess = st.tabs(["🤝 Business & Kunde", "🏢 Interne KPIs", "🔬 Prozessanalyse"])

    with tab_kunde:
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Kundenzufriedenheit (Proxy)", f"{sla_getroffen}/{sla_relevant} SLA" if sla_relevant else "–")
        k2.metric("Sicherheitsrelevant offen", len(sicherheitsrelevant_offen))
        k3.metric(f"Abgeschlossen (letzte {ALT_SCHWELLE_TAGE}d)", len(kuerzlich_erledigt))
        rueckmeldung = mittel(rueckmeldungszeiten_h)
        k4.metric("Ø Zeit bis 1. Rückmeldung", f"{rueckmeldung:.1f} h" if rueckmeldung is not None else "–")
        st.caption(
            f"Kundenzufriedenheit ist ein Näherungswert: Anteil der QMs mit Kundenrückmeldung nötig, "
            f"die innert {SLA_TAGE_KUNDE} Tagen abgeschlossen wurden - es gibt keine echte Zufriedenheitsmessung."
        )

        st.divider()
        st.subheader("Verteilungen")
        p1, p2 = st.columns(2)
        with p1:
            st.caption("Nach Priorität")
            pie_chart(pd.Series([qm.prioritaet for qm in qm_liste]).value_counts(), "Priorität")
        with p2:
            st.caption("Nach Kategorie")
            pie_chart(pd.Series([qm.hauptkategorie for qm in qm_liste]).value_counts(), "Kategorie")

    with tab_intern:
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Offene QMs", len(offene))
        k2.metric(f"Alte unbearb. Fälle (>{ALT_SCHWELLE_TAGE}d)", len(alte_unbearbeitete))
        reaktion = mittel(reaktionszeiten_h)
        k3.metric("Ø Reaktionszeit bis Zugewiesen", f"{reaktion:.1f} h" if reaktion is not None else "–")
        bearbeitung = mittel(bearbeitungszeiten_h)
        k4.metric("Ø Bearbeitungszeit", f"{bearbeitung / 24:.1f} Tage" if bearbeitung is not None else "–")

        st.divider()
        st.subheader("Zeitverlauf")
        verlauf = pd.DataFrame({
            "Neu erfasst": wochen_zaehlung([qm.erstellt_am for qm in qm_liste]),
            "Abgeschlossen": wochen_zaehlung([terminal_zeitpunkt(qm) for qm in qm_liste if terminal_zeitpunkt(qm)]),
        }).fillna(0)
        st.area_chart(verlauf)

        st.divider()
        c1, c2 = st.columns([1, 1])
        with c1:
            st.subheader("Offene QMs pro Abteilung")
            workload = {}
            for qm in offene:
                ziel_abt = KATEGORIE_ABTEILUNG.get(qm.hauptkategorie)
                name = ziel_abt.value["name"] if ziel_abt else "Andere"
                workload[name] = workload.get(name, 0) + 1
            st.bar_chart(pd.Series(workload, name="Offene QMs"))
        with c2:
            st.subheader("Nach Status")
            pie_chart(pd.Series([qm.status for qm in qm_liste]).value_counts(), "Status")

    with tab_prozess:
        st.caption("Process Mining auf Basis des QM-Verlaufs: jeder QM ist ein Fall, jeder Statuswechsel eine Aktivität.")
        sequenzen = [aktivitaeten_sequenz(qm) for qm in qm_liste]
        dauern_tage = [fall_dauer_stunden(qm, heute) / 24 for qm in qm_liste]
        self_loop_anteil = sum(hat_self_loop(s) for s in sequenzen) / len(sequenzen) if sequenzen else 0
        loop_anteil = sum(hat_loop(s) for s in sequenzen) / len(sequenzen) if sequenzen else 0
        rework_anteil = sum(ist_rework(qm) for qm in qm_liste) / len(qm_liste) if qm_liste else 0

        k1, k2, k3, k4, k5, k6 = st.columns(6)
        k1.metric("Ø Falldauer (Median)", f"{statistics.median(dauern_tage):.1f} d" if dauern_tage else "–")
        k2.metric("Ø Falldauer (Mittelwert)", f"{statistics.mean(dauern_tage):.1f} d" if dauern_tage else "–")
        k3.metric("Self-Loop-Fälle", f"{self_loop_anteil:.0%}")
        k4.metric("Fälle mit Schlaufe", f"{loop_anteil:.0%}")
        k5.metric("Rework-Fälle", f"{rework_anteil:.0%}")
        k6.metric("Ressourcen", ressourcen_anzahl(qm_liste))

        varianten = berechne_varianten(qm_liste)
        aktivitaeten_beobachtet = {s for seq in sequenzen for s in seq}
        m1, m2, m3 = st.columns(3)
        m1.metric("Varianten", len(varianten))
        m2.metric("Fälle", len(qm_liste))
        m3.metric("Aktivitäten", len(aktivitaeten_beobachtet))

        st.divider()
        st.subheader("Entdeckter Prozessgraph")
        st.caption("Klicke auf einen Schritt im Graph oder wähle ihn links aus, um Details zu sehen.")
        schritte_reihenfolge = [s.value for s in QMStatus]
        alle_schritte = sorted(aktivitaeten_beobachtet, key=schritte_reihenfolge.index)
        kanten = berechne_dfg(qm_liste)
        col_detail, col_graph = st.columns([1, 2])
        with col_graph:
            schritt_klick = render_dfg(qm_liste, kanten, ausgewaehlt=st.session_state.get("prozess_schritt_wahl"))
        with col_detail:
            if schritt_klick:
                st.session_state["prozess_schritt_wahl"] = schritt_klick
            schritt_wahl = st.selectbox("Schritt für Details wählen", alle_schritte, key="prozess_schritt_wahl")
            render_schritt_detail(qm_liste, schritt_wahl, kanten, heute)

        st.divider()
        g1, g2 = st.columns(2)
        with g1:
            st.subheader("Varianten (Häufigkeit)")
            render_varianten_chart(qm_liste)
        with g2:
            st.subheader("Falldauer im Zeitverlauf")
            render_dauer_zeitverlauf(qm_liste)


# ---------- Planung ----------

def gantt_chart(zeilen, hoehe=260):
    df = pd.DataFrame(zeilen)
    spec = {
        "mark": {"type": "bar", "tooltip": True, "cornerRadius": 3},
        "encoding": {
            "y": {"field": "Ticket", "type": "nominal", "sort": "-x", "title": None},
            "x": {"field": "Start", "type": "temporal", "title": None},
            "x2": {"field": "Ende", "type": "temporal"},
            "color": {"field": "Abteilung", "type": "nominal"},
            "tooltip": [
                {"field": "Ticket", "type": "nominal"},
                {"field": "Titel", "type": "nominal"},
                {"field": "Start", "type": "temporal"},
                {"field": "Ende", "type": "temporal"},
            ],
        },
        "height": hoehe,
    }
    st.vega_lite_chart(df, spec, use_container_width=True)


def view_planung():
    st.header("📅 Planung")
    st.caption("Auslastung der Teams und geplante Termine - hilft bei der Ressourcenplanung.")
    qm_liste = st.session_state.qm_liste
    heute = datetime.now().date()
    offene = [qm for qm in qm_liste if qm.status not in TERMINAL_STATUS]
    HOEHE = 230

    links, rechts = st.columns(2)
    with links:
        st.subheader("Team-Auslastung")
        workload = {}
        for qm in offene:
            if qm.zugewiesen_an:
                workload[qm.zugewiesen_an] = workload.get(qm.zugewiesen_an, 0) + 1
        if workload:
            st.bar_chart(pd.Series(workload, name="Offene QMs").sort_values(ascending=False), height=HOEHE)
        else:
            st.caption("Aktuell niemandem etwas zugewiesen.")

    with rechts:
        st.subheader("Termine & Fälligkeiten")
        mit_termin = [qm for qm in offene if qm.faellig_am or qm.termin_geplante_umsetzung]
        mit_termin.sort(key=lambda qm: qm.faellig_am or qm.termin_geplante_umsetzung)
        with st.container(height=HOEHE):
            if not mit_termin:
                st.caption("Keine offenen QMs mit Termin oder Fälligkeitsdatum.")
            for qm in mit_termin:
                datum = qm.faellig_am or qm.termin_geplante_umsetzung
                ueberfaellig = datum < heute
                icon = "🔴" if ueberfaellig else "🟢"
                label = f"{icon} {qm.qm_nummer} · {datum:%d.%m.%Y} · {qm.titel}"
                if st.button(label, key=f"planung_{qm.qm_id}", use_container_width=True):
                    oeffne_details(qm.qm_id)

    st.subheader("Zeitplan")
    zeilen = []
    for qm in offene:
        ende = qm.faellig_am or qm.termin_geplante_umsetzung
        if not ende:
            continue
        ziel_abt = KATEGORIE_ABTEILUNG.get(qm.hauptkategorie)
        zeilen.append({
            "Ticket": qm.qm_nummer,
            "Titel": qm.titel,
            "Start": qm.erstellt_am.date().isoformat(),
            "Ende": ende.isoformat(),
            "Abteilung": ziel_abt.value["name"] if ziel_abt else "Andere",
        })
    if zeilen:
        gantt_chart(zeilen, hoehe=HOEHE)
    else:
        st.caption("Keine Termine für einen Zeitplan vorhanden.")


# ---------- Navigation ----------

def render_sidebar():
    with st.sidebar:
        st.title("📋 QM-App")
        st.caption(f"👤 {aktueller_user()} · {aktuelle_abteilung().value['name']}")
        st.divider()
        if nur_erfasser():
            if st.button("📄 Meine QMs", use_container_width=True):
                st.session_state.view = "meine_qms"
            if st.button("➕ Neuer QM", use_container_width=True):
                st.session_state.view = "neu"
        else:
            if hat_bucket() and st.button("🪣 Mein Bucket", use_container_width=True):
                st.session_state.view = "abteilung"
            if st.button("📄 Meine QMs", use_container_width=True):
                st.session_state.view = "meine_qms"
            if st.button("📋 Alle QMs", use_container_width=True):
                st.session_state.view = "liste"
            if hat_recht(RECHTE.ERFASSEN) and st.button("➕ Neuer QM", use_container_width=True):
                st.session_state.view = "neu"
            if hat_recht(RECHTE.STATISTIK) and st.button("📈 Statistik", use_container_width=True):
                st.session_state.view = "statistik"
            if hat_recht(RECHTE.STATISTIK) and st.button("📅 Planung", use_container_width=True):
                st.session_state.view = "planung"
        st.divider()
        if st.button("🚪 Abmelden", use_container_width=True):
            st.session_state.current_user = None
            st.session_state.current_abteilung_key = None
            st.session_state.view = "meine_qms"
            st.rerun()


def main():
    st.set_page_config(page_title="QM-App", page_icon="📋", layout="wide")
    init_state()

    if not st.session_state.current_user:
        view_login()
        return

    render_sidebar()
    view = st.session_state.view

    if nur_erfasser():
        if view == "neu":
            view_neuer_qm()
        else:
            view_meine_qms()
    elif view == "meine_qms":
        view_meine_qms()
    elif view == "abteilung" and hat_bucket():
        view_bucket()
    elif view == "neu" and hat_recht(RECHTE.ERFASSEN):
        view_neuer_qm()
    elif view == "statistik" and hat_recht(RECHTE.STATISTIK):
        view_statistik()
    elif view == "planung" and hat_recht(RECHTE.STATISTIK):
        view_planung()
    else:
        view_liste()

    if st.session_state.detail_qm_id:
        zeige_details(st.session_state.detail_qm_id)


if __name__ == "__main__":
    main()