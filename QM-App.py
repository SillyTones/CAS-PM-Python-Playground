"""
QM-App
======
QM-Tracking auf Basis von qm_model.QualitaetsMangel: Login mit Berechtigung je
Abteilung, ein Planner-artiges Board mit Karten je Status, ein persönliches
Bucket mit offenen QMs zum Übernehmen, und ein Detail-Dialog pro QM.
"""

import streamlit as st
import pandas as pd
from datetime import date
from enum import Enum, auto

from qm_model import (
    QualitaetsMangel, QMStatus, VALID_TRANSITIONS, HistoryEntryType,
    HAUPTKATEGORIEN, WUNSCH_ODER_MANGEL_OPTIONEN, SERIE_ODER_EINZELFALL_OPTIONEN,
    MINOR_MAJOR_OPTIONEN,
)
from qm_data_reader import load_qm_data

# Mitarbeiterlisten (fiktiv)
_MITARBEITER_KUNDENDIENST = ['Schilling Curdin', 'Mettler Walo', 'Grieder Linus', 'Vogt Tarzisius', 'Wiesmann Pankraz', 'Rossier Beda', 'Marending Gion', 'Repond Hugo', 'Amrein Aldo', 'Wenger Werner', 'Oesch Hansjörg', 'Wicht Silvio', 'Waldmeier Tarzisius', 'Schürch Notker', 'Blatter Marco', 'Hodel Valentin', 'Schmutz Gion']
_MITARBEITER_HOTLINE = ['Scherrer Duri', 'Imhof Domenic', 'Iseli Fritz', 'Vial Kaspar', 'Sudan Gion', 'Tinguely Elias', 'Wenger Nils', 'Rindlisbacher Odilo', 'Rickenbacher Nino', 'Brunschwiler Benno', 'Zbinden Yves', 'Frischknecht Livio']
_MITARBEITER_VERKAUF = ['Gonseth Quirin', 'Berthoud Valerio', 'Piller Nils', 'Chevalley Cornel', 'Zeller Aldo', 'Wehrli Jann', 'Zollinger Werner', 'Küpfer Flavio', 'Wetzel Klemens', 'Tanner Ephrem', 'Schoch Jodok']
_MITARBEITER_MONTAGE = ['Vial Kaspar', 'Brogli Gieri', 'Marmy Flurin', 'Knecht Thom', 'Hangartner Jann', 'Overney Ilir', 'Feuz Notker', 'Zingg Ephrem', 'Stalder Andri', 'Probst Christof', 'Descloux Ursin', 'Rennhard Livio', 'Rüegg Urban', 'Tinguely Hubert', 'Kaufmann Yves', 'Grunder Aldo', 'Oesch Curdin', 'Wüthrich Walo', 'Steffen Quirin', 'Progin Meinrad', 'Wanner Andri', 'Junod Thom', 'Yerly Mario', 'Wehrli Jann', 'Brülisauer Ilir', 'Frischknecht Livio', 'Habegger Urban', 'Zbinden Werner']
_MITARBEITER_INBETRIEBNAHME = ['Fivaz Remo', 'Landolt Marco', 'Christinat Leandro', 'Overney Ilir', 'Kaufmann Yves', 'Aellen Domenic', 'Cathomen Jachen', 'Kellenberger Beda', 'Magnenat Gion', 'Baertschi Odilo', 'Herzig Iso']
_MITARBEITER_KONSTRUKTION = ['Sturzenegger Meinrad', 'Jost Jachen', 'Hirschy Mario', 'Steinmann Hubert']
_MITARBEITER_VORFUHRUNG = ['Zbinden Elio', 'Delessert Elio', 'Stalder Andri', 'Jaton Jodok', 'Bissig Benno', 'Descloux Ursin', 'Marmy Flurin', 'Junod Thom', 'Genoud Silas', 'Ruckstuhl Leandro', 'Salvisberg Hugo', 'Zimmerli Nino', 'Savary Elias', 'Zbinden Yves', 'Zeller Aldo', 'Zollinger Werner']
_MITARBEITER_SOFTWARE_ENT = ['Aebischer Silvio', 'Iseli Fritz', 'Wicht Klemens', 'Rennhard Livio', 'Baertschi Odilo', 'Yerly Mario', 'Portmann Flurin']
_MITARBEITER_ELEKTRO_ENT = ['Nydegger Orlando', 'Eichmann Duri', 'Vionnet Pankraz', 'Savary Elias']
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
    ENTWICKLUNGSLEITUNG = {"name": "Entwicklungsleitung", "Mitarbeiter": _MITARBEITER_ENTWICKLUNGSLEITUNG, "Rechte": {RECHTE.ERFASSEN, RECHTE.BEARBEITEN, RECHTE.ZUWEISEN}}
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

# Board-Spalten (Buckets). Pausiert/Abgebrochen werden der Nachbarspalte zugeschlagen,
# die Karte selbst zeigt aber weiterhin ihren echten Status.
BOARD_SPALTEN = [
    QMStatus.NEU.value, QMStatus.IN_PRUEFUNG.value, QMStatus.ZUGEWIESEN.value,
    QMStatus.IN_BEARBEITUNG.value, QMStatus.BEHOBEN.value, QMStatus.ABGESCHLOSSEN.value,
]
SPALTE_FUER_STATUS = {
    QMStatus.PAUSIERT.value: QMStatus.IN_BEARBEITUNG.value,
    QMStatus.ABGEBROCHEN.value: QMStatus.ABGESCHLOSSEN.value,
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
NEU_FELDER = STATUS_FELDER[QMStatus.NEU.value]

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
        st.session_state.view = "board"
    if "detail_qm_id" not in st.session_state:
        st.session_state.detail_qm_id = None


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


def finde_qm(qm_id):
    for qm in st.session_state.qm_liste:
        if qm.qm_id == qm_id:
            return qm
    return None


def naechste_qm_id():
    ids = [qm.qm_id for qm in st.session_state.qm_liste]
    return max(ids, default=0) + 1


def naechste_qm_nummer():
    return f"QM-{date.today().year}-{naechste_qm_id():03d}"


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


def oeffne_details(qm_id):
    st.session_state.detail_qm_id = qm_id


# ---------- Login ----------

def view_login():
    st.title("🔐 QM-App Anmeldung")
    abteilung = st.selectbox("Abteilung", list(ABTEILUNGEN), format_func=lambda a: a.value["name"])
    person = st.selectbox("Mitarbeiter", abteilung.value["Mitarbeiter"])
    if st.button("Anmelden", type="primary"):
        st.session_state.current_user = person
        st.session_state.current_abteilung_key = abteilung.name
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
    optionen = VALID_TRANSITIONS.get(qm.status, [])
    if not optionen or not hat_recht(RECHTE.BEARBEITEN):
        return
    st.caption("Status ändern")
    cols = st.columns(len(optionen))
    for col, ziel in zip(cols, optionen):
        label = f"{STATUS_ICON.get(ziel, '📌')} {ziel}"
        if col.button(label, key=f"status_{qm.qm_id}_{ziel}", use_container_width=True):
            setze_status(qm, ziel, aktueller_user())
            st.rerun()


# ---------- Karten & Board ----------

def render_karte(qm, key_prefix):
    with st.container(border=True):
        st.markdown(f"**{qm.qm_nummer}**  \n{qm.titel}")
        badge_farbe = PRIORITAET_FARBE.get(qm.prioritaet, "gray")
        st.badge(qm.prioritaet, color=badge_farbe)
        st.caption(f"{qm.hauptkategorie}" + (f" · {qm.zugewiesen_an}" if qm.zugewiesen_an else ""))
        if qm.status in SPALTE_FUER_STATUS:
            st.caption(f"{STATUS_ICON.get(qm.status, '')} {qm.status}")
        if st.button("Öffnen", key=f"{key_prefix}_{qm.qm_id}", use_container_width=True):
            oeffne_details(qm.qm_id)


def view_board():
    st.header("📋 Board")
    suche = st.text_input("🔎 Suche", placeholder="Titel oder Nummer...", label_visibility="collapsed")
    qm_liste = st.session_state.qm_liste
    if suche:
        s = suche.lower()
        qm_liste = [qm for qm in qm_liste if s in qm.titel.lower() or s in qm.qm_nummer.lower()]

    spalten = st.columns(len(BOARD_SPALTEN))
    for spalte, status in zip(spalten, BOARD_SPALTEN):
        with spalte:
            st.markdown(f"**{STATUS_ICON.get(status, '')} {status}**")
            treffer = [qm for qm in qm_liste if SPALTE_FUER_STATUS.get(qm.status, qm.status) == status]
            if not treffer:
                st.caption("–")
            for qm in treffer:
                render_karte(qm, key_prefix="board_open")


# ---------- Mein Bucket ----------

def uebernehmen(qm):
    user = aktueller_user()
    if qm.status == QMStatus.NEU.value:
        qm.change_status(QMStatus.IN_PRUEFUNG.value, user=user)
    qm.assign_to(user, aktuelle_abteilung().value["name"], user=user)
    qm.change_status(QMStatus.ZUGEWIESEN.value, user=user)


def view_bucket():
    abteilung = aktuelle_abteilung()
    st.header(f"🪣 Mein Bucket – {abteilung.value['name']}")
    st.caption("Noch nicht zugewiesene QMs, deren Kategorie zu dieser Abteilung passt.")
    offene_status = (QMStatus.NEU.value, QMStatus.IN_PRUEFUNG.value)
    qm_liste = [
        qm for qm in st.session_state.qm_liste
        if KATEGORIE_ABTEILUNG.get(qm.hauptkategorie) == abteilung
        and qm.status in offene_status and not qm.zugewiesen_an
    ]
    if not qm_liste:
        st.info("Aktuell nichts Offenes in deinem Bucket.")
        return
    for qm in qm_liste:
        with st.container(border=True):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"**{qm.qm_nummer}** – {qm.titel}")
                st.caption(f"{qm.hauptkategorie} · {qm.prioritaet} · {qm.status}")
            with col2:
                if hat_recht(RECHTE.BEARBEITEN) and st.button("🙋 Übernehmen", key=f"take_{qm.qm_id}", use_container_width=True):
                    uebernehmen(qm)
                    st.rerun()


# ---------- Neuer QM ----------

def view_neuer_qm():
    st.header("➕ Neuen Qualitätsmangel erfassen")
    vorbelegung = {
        "erfasser_kuerzel": "".join(w[0] for w in aktueller_user().split()).upper(),
        "erfasser_abteilung": aktuelle_abteilung().value["name"],
    }
    with st.form("neuer_qm"):
        werte = {
            name: render_field(name, FORMULAR_CONFIG[name], vorbelegung.get(name), key=f"neu_{name}")
            for name in NEU_FELDER
        }
        abgesendet = st.form_submit_button("✅ Erfassen", type="primary")

    if not abgesendet:
        return
    if not werte["titel"] or not werte["beschreibung"]:
        st.error("Titel und Mangelbeschreibung sind Pflichtfelder.")
        return

    qm = QualitaetsMangel(qm_id=naechste_qm_id(), qm_nummer=naechste_qm_nummer(), ersteller=aktueller_user(), **werte)
    st.session_state.qm_liste.append(qm)
    st.success(f"{qm.qm_nummer} wurde erfasst.")
    oeffne_details(qm.qm_id)


# ---------- Detail-Dialog ----------

def render_editierbare_felder(qm):
    felder = STATUS_FELDER.get(qm.status, [])
    if not felder or not hat_recht(RECHTE.BEARBEITEN):
        return
    with st.form(f"felder_{qm.qm_id}_{qm.status}"):
        werte = {f: render_field(f, FORMULAR_CONFIG[f], getattr(qm, f), key=f"f_{qm.qm_id}_{f}") for f in felder}
        if st.form_submit_button("💾 Speichern"):
            for f, w in werte.items():
                setattr(qm, f, w)
            qm.add_history_entry(HistoryEntryType.BEARBEITET.value, "Angaben aktualisiert", user=aktueller_user())
            st.rerun()


def render_alle_angaben(qm):
    for status, felder in STATUS_FELDER.items():
        st.markdown(f"**{STATUS_ICON.get(status, '')} {status}**")
        for f in felder:
            wert = getattr(qm, f)
            if isinstance(wert, bool):
                wert = "Ja" if wert else "Nein"
            st.write(f"{FORMULAR_CONFIG[f]['label']}: {wert if wert not in (None, '') else '–'}")


def render_verlauf(qm):
    if not qm.history:
        st.info("Keine Historie vorhanden.")
    for h in qm.history:
        st.markdown(f"**{h.timestamp:%d.%m.%Y %H:%M}** – {h.details} _(von {h.user})_")


def render_kommentare(qm):
    st.markdown("**💬 Kommentare**")
    for k in qm.kommentare:
        st.markdown(f"_{k.timestamp:%d.%m.%Y %H:%M}_ **{k.user}:** {k.text}")
    if hat_recht(RECHTE.BEARBEITEN) or hat_recht(RECHTE.ERFASSEN):
        text = st.text_input("Neuer Kommentar", key=f"kommentar_{qm.qm_id}", label_visibility="collapsed", placeholder="Kommentar hinzufügen...")
        if st.button("Hinzufügen", key=f"kommentar_go_{qm.qm_id}") and text:
            qm.add_kommentar(text, user=aktueller_user())
            st.rerun()


@st.dialog(" ", width="large")
def zeige_details(qm_id):
    qm = finde_qm(qm_id)
    if qm is None:
        st.error("QM nicht gefunden.")
        return

    if st.button("✖ Schliessen"):
        st.session_state.detail_qm_id = None
        st.rerun()

    st.subheader(f"{qm.qm_nummer} – {qm.titel}")
    st.caption(qm.beschreibung)
    st.markdown(f"**Status:** {STATUS_ICON.get(qm.status, '')} {qm.status}")
    render_status_wechsel(qm)
    st.divider()

    render_editierbare_felder(qm)

    with st.expander("📄 Alle Angaben"):
        render_alle_angaben(qm)
    with st.expander("📜 Verlauf"):
        render_verlauf(qm)

    st.divider()
    render_kommentare(qm)


# ---------- Statistik ----------

def view_statistik():
    st.header("📈 Statistik")
    df = pd.DataFrame([{"Status": qm.status, "Kategorie": qm.hauptkategorie} for qm in st.session_state.qm_liste])
    col1, col2 = st.columns(2)
    col1.subheader("Nach Status")
    col1.bar_chart(df["Status"].value_counts())
    col2.subheader("Nach Kategorie")
    col2.bar_chart(df["Kategorie"].value_counts())


# ---------- Navigation ----------

def render_sidebar():
    with st.sidebar:
        st.title("📋 QM-App")
        st.caption(f"👤 {aktueller_user()} · {aktuelle_abteilung().value['name']}")
        st.divider()
        if st.button("📋 Board", use_container_width=True):
            st.session_state.view = "board"
        if st.button("🪣 Mein Bucket", use_container_width=True):
            st.session_state.view = "bucket"
        if hat_recht(RECHTE.ERFASSEN) and st.button("➕ Neuer QM", use_container_width=True):
            st.session_state.view = "neu"
        if hat_recht(RECHTE.STATISTIK) and st.button("📈 Statistik", use_container_width=True):
            st.session_state.view = "statistik"
        st.divider()
        if st.button("🚪 Abmelden", use_container_width=True):
            st.session_state.current_user = None
            st.session_state.current_abteilung_key = None
            st.session_state.view = "board"
            st.rerun()


def main():
    st.set_page_config(page_title="QM-App", page_icon="📋", layout="wide")
    init_state()

    if not st.session_state.current_user:
        view_login()
        return

    render_sidebar()
    view = st.session_state.view
    if view == "board":
        view_board()
    elif view == "bucket":
        view_bucket()
    elif view == "neu":
        view_neuer_qm()
    elif view == "statistik":
        view_statistik()

    if st.session_state.detail_qm_id:
        zeige_details(st.session_state.detail_qm_id)


if __name__ == "__main__":
    main()