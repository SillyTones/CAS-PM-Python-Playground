"""
QM-App
======
QM-Tracking auf Basis von qm_model.QualitaetsMangel: Login mit Berechtigung je
Abteilung, ein Planner-artiges Board mit Karten je Status, ein persönliches
Bucket mit offenen QMs zum Übernehmen, und ein Detail-Dialog pro QM.
"""

import streamlit as st
import pandas as pd
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


def render_verlauf(qm):
    if not qm.history:
        st.info("Keine Historie vorhanden.")
    for h in qm.history:
        st.markdown(f"**{h.timestamp:%d.%m.%Y %H:%M}** – {h.details} _(von {h.user})_")


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

    kopf, taste = st.columns([5, 1])
    kopf.subheader(f"{qm.qm_nummer} – {qm.titel}")
    if hat_recht(RECHTE.BEARBEITEN):
        label = "👁️ Ansehen" if st.session_state.detail_bearbeiten else "✏️ Bearbeiten"
        if taste.button(label, key=f"toggle_edit_{qm.qm_id}", use_container_width=True):
            st.session_state.detail_bearbeiten = not st.session_state.detail_bearbeiten
            st.rerun()

    st.caption(qm.beschreibung)
    render_kurzfakten(qm)

    st.markdown(f"**{STATUS_ICON.get(qm.status, '')} {qm.status}**")
    render_status_wechsel(qm)
    if not qm.zugewiesen_an and qm.status not in TERMINAL_STATUS and hat_recht(RECHTE.BEARBEITEN):
        if st.button("🙋 Übernehmen", key=f"dialog_take_{qm.qm_id}"):
            uebernehmen(qm)
            st.rerun()

    st.divider()
    editierbar = hat_recht(RECHTE.BEARBEITEN) and st.session_state.detail_bearbeiten
    tab_namen = [f"{STATUS_ICON.get(status, '')} {status}" for status in STATUS_FELDER] + ["💬 Kommentare", "📜 Verlauf"]
    tabs = st.tabs(tab_namen)
    for tab, (status, felder) in zip(tabs, STATUS_FELDER.items()):
        with tab:
            render_gruppe_tab(qm, status, felder, editierbar)
    with tabs[-2]:
        render_kommentare(qm)
    with tabs[-1]:
        render_verlauf(qm)


# ---------- Statistik ----------

ALT_SCHWELLE_TAGE = 14
SLA_TAGE_KUNDE = 5


def status_zeitpunkt(qm, status_wert):
    for h in qm.history:
        if h.neuer_wert == status_wert:
            return h.timestamp
    return None


def terminal_zeitpunkt(qm):
    return status_zeitpunkt(qm, QMStatus.BEHOBEN.value) or status_zeitpunkt(qm, QMStatus.ABGESCHLOSSEN.value)


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

    st.subheader("Auf einen Blick")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Offene QMs", len(offene))
    k2.metric(f"Alte unbearb. Fälle (>{ALT_SCHWELLE_TAGE}d)", len(alte_unbearbeitete))
    k3.metric("Sicherheitsrelevant offen", len(sicherheitsrelevant_offen))
    k4.metric(f"Abgeschlossen (letzte {ALT_SCHWELLE_TAGE}d)", len(kuerzlich_erledigt))

    k5, k6, k7, k8 = st.columns(4)
    reaktion = mittel(reaktionszeiten_h)
    k5.metric("Ø Reaktionszeit bis Zugewiesen", f"{reaktion:.1f} h" if reaktion is not None else "–")
    rueckmeldung = mittel(rueckmeldungszeiten_h)
    k6.metric("Ø Zeit bis 1. Rückmeldung", f"{rueckmeldung:.1f} h" if rueckmeldung is not None else "–")
    bearbeitung = mittel(bearbeitungszeiten_h)
    k7.metric("Ø Bearbeitungszeit", f"{bearbeitung / 24:.1f} Tage" if bearbeitung is not None else "–")
    k8.metric("Kundenzufriedenheit (Proxy)", f"{sla_getroffen}/{sla_relevant} SLA" if sla_relevant else "–")
    st.caption(
        f"Kundenzufriedenheit ist ein Näherungswert: Anteil der QMs mit Kundenrückmeldung nötig, "
        f"die innert {SLA_TAGE_KUNDE} Tagen abgeschlossen wurden - es gibt keine echte Zufriedenheitsmessung."
    )

    st.divider()
    st.subheader("Zeitverlauf")
    verlauf = pd.DataFrame({
        "Neu erfasst": wochen_zaehlung([qm.erstellt_am for qm in qm_liste]),
        "Abgeschlossen": wochen_zaehlung([terminal_zeitpunkt(qm) for qm in qm_liste if terminal_zeitpunkt(qm)]),
    }).fillna(0)
    st.area_chart(verlauf)

    st.divider()
    st.subheader("Verteilungen")
    p1, p2, p3 = st.columns(3)
    with p1:
        st.caption("Nach Status")
        pie_chart(pd.Series([qm.status for qm in qm_liste]).value_counts(), "Status")
    with p2:
        st.caption("Nach Kategorie")
        pie_chart(pd.Series([qm.hauptkategorie for qm in qm_liste]).value_counts(), "Kategorie")
    with p3:
        st.caption("Nach Priorität")
        pie_chart(pd.Series([qm.prioritaet for qm in qm_liste]).value_counts(), "Priorität")

    st.divider()
    st.subheader("Offene QMs pro Abteilung")
    workload = {}
    for qm in offene:
        ziel_abt = KATEGORIE_ABTEILUNG.get(qm.hauptkategorie)
        name = ziel_abt.value["name"] if ziel_abt else "Andere"
        workload[name] = workload.get(name, 0) + 1
    st.bar_chart(pd.Series(workload, name="Offene QMs"))


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