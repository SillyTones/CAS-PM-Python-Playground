"""
QM Model - Qualitätsmangel Class
=================================
Datenmodell für Qualitätsmängel mit vollständiger Feldstruktur und History-Management.

Status- und Feldstruktur folgen dem Prozessdiagramm (5 Schritte, Status oben):
QM Erfassung -> Erfassung präzisieren/priorisieren (QM-Kiosk) -> Ursache finden
-> Mangel beheben -> Abschluss QM, mit Nebenzuständen Pausiert/Wiedereröffnet/Abgebrochen.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, date
from typing import List, Dict, Optional, Any
from enum import Enum
import json


class QMStatus(Enum):
    """Status-Enum für QM (entspricht den Boxen im Statusdiagramm)"""
    NEU = "Neu"
    IN_PRUEFUNG = "In Prüfung"
    ZUGEWIESEN = "Zugewiesen"
    IN_BEARBEITUNG = "In Bearbeitung"
    PAUSIERT = "Pausiert"
    BEHOBEN = "Behoben"
    ABGESCHLOSSEN = "Abgeschlossen"
    WIEDEREROEFFNET = "Wiedereröffnet"
    ABGEBROCHEN = "Abgebrochen"


# Erlaubte Übergänge gemäss den Pfeilen im Statusdiagramm. Abgebrochen ist von jedem
# noch offenen Schritt aus erreichbar (Pfeil spannt im Diagramm über den ganzen Bereich
# In Prüfung...Behoben); Wiedereröffnet/Pausiert sind je ein eigener Zwischenschritt
# mit genau einem Rücksprungziel.
VALID_TRANSITIONS: Dict[str, List[str]] = {
    QMStatus.NEU.value: [QMStatus.IN_PRUEFUNG.value],
    QMStatus.IN_PRUEFUNG.value: [QMStatus.ZUGEWIESEN.value, QMStatus.ABGEBROCHEN.value],
    QMStatus.ZUGEWIESEN.value: [QMStatus.IN_BEARBEITUNG.value, QMStatus.ABGEBROCHEN.value],
    QMStatus.IN_BEARBEITUNG.value: [QMStatus.PAUSIERT.value, QMStatus.BEHOBEN.value, QMStatus.ABGEBROCHEN.value],
    QMStatus.PAUSIERT.value: [QMStatus.IN_BEARBEITUNG.value, QMStatus.ABGEBROCHEN.value],
    QMStatus.BEHOBEN.value: [QMStatus.ABGESCHLOSSEN.value, QMStatus.ABGEBROCHEN.value],
    QMStatus.ABGESCHLOSSEN.value: [QMStatus.WIEDEREROEFFNET.value],
    QMStatus.WIEDEREROEFFNET.value: [QMStatus.IN_PRUEFUNG.value],
    QMStatus.ABGEBROCHEN.value: [],
}


class HistoryEntryType(Enum):
    """Typen von History-Einträgen"""
    ERSTELLT = "erstellt"
    STATUS_GEAENDERT = "status_geaendert"
    BEARBEITET = "bearbeitet"
    ZUGEWIESEN = "zugewiesen"
    KOMMENTAR = "kommentar"
    PRIORITAET_GEAENDERT = "prioritaet_geaendert"
    PAUSIERT = "pausiert"
    FORTGESETZT = "fortgesetzt"
    WIEDEREROEFFNET = "wiedereroeffnet"
    ABGEBROCHEN = "abgebrochen"


# Optionslisten für die Auswahlfelder aus dem Diagramm (Schritt 1 & 2)
HAUPTKATEGORIEN = ["Software", "Mechanik", "Elektro", "Organisatorisch", "Qualität", "Applikation"]
WUNSCH_ODER_MANGEL_OPTIONEN = ["Wunsch", "Mangel"]
SERIE_ODER_EINZELFALL_OPTIONEN = ["Serie", "Einzelfall"]
MINOR_MAJOR_OPTIONEN = ["Minor", "Major"]


@dataclass
class HistoryEntry:
    """History-Eintrag für QM"""
    timestamp: datetime
    typ: str
    user: str
    details: str
    status: str
    alter_wert: Optional[str] = None
    neuer_wert: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert History-Eintrag zu Dictionary"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "typ": self.typ,
            "user": self.user,
            "details": self.details,
            "status": self.status,
            "alter_wert": self.alter_wert,
            "neuer_wert": self.neuer_wert
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HistoryEntry':
        """Erstellt History-Eintrag aus Dictionary"""
        data_copy = data.copy()
        data_copy["timestamp"] = datetime.fromisoformat(data_copy["timestamp"])
        return cls(**data_copy)


@dataclass
class Kommentar:
    """Kommentar für QM (Schritt 3 - Ursache finden)"""
    timestamp: datetime
    user: str
    text: str

    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert Kommentar zu Dictionary"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "user": self.user,
            "text": self.text
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Kommentar':
        """Erstellt Kommentar aus Dictionary"""
        data_copy = data.copy()
        data_copy["timestamp"] = datetime.fromisoformat(data_copy["timestamp"])
        return cls(**data_copy)


@dataclass
class QualitaetsMangel:
    """
    Hauptklasse für Qualitätsmangel (QM)

    Feldgruppen folgen den 5 Prozessschritten aus dem Statusdiagramm:
    1. QM Erfassung (Neu)
    2. Erfassung präzisieren und priorisieren / QM-Kiosk (In Prüfung)
    3. Ursache finden (Zugewiesen)
    4. Mangel beheben (In Bearbeitung)
    5. Abschluss QM (Behoben / Abgeschlossen)
    """
    # Identifikation
    qm_id: int
    qm_nummer: str

    # --- Schritt 1: QM Erfassung ---
    # Allgemeine Infos
    erfasser_kuerzel: Optional[str] = None
    erfasser_abteilung: Optional[str] = None
    involvierte: Optional[str] = None  # Besprochen mit

    # Infos zu Mangel
    titel: str = ""
    beschreibung: str = ""  # Mangelbeschreibung
    wunsch_oder_mangel: str = "Mangel"
    sicherheitsrelevant: bool = False
    hauptkategorie: str = "Software"

    # Software?
    ist_software: bool = False
    plc: bool = False
    plc_version: Optional[str] = None
    nc: bool = False
    nc_version: Optional[str] = None
    mcm: bool = False

    maschinentyp: Optional[str] = None
    serie_oder_einzelfall: Optional[str] = None

    kundenrueckmeldung_noetig: bool = False
    ticket_nr_intern: Optional[str] = None
    kontaktperson_servicetechniker: Optional[str] = None

    # --- Schritt 2: Erfassung präzisieren und priorisieren / QM-Kiosk ---
    minor_major: Optional[str] = None
    prioritaet: str = "Mittel"
    termin_geplante_umsetzung: Optional[date] = None

    # --- Zuweisung (Schritt 3: Ursache finden) ---
    abteilung: Optional[str] = None
    zugewiesen_an: Optional[str] = None
    faellig_am: Optional[date] = None

    # --- Schritt 4: Mangel beheben ---
    bearbeitung_extern: bool = False
    ticket_nr_extern: Optional[str] = None
    korrespondenz_extern: Optional[str] = None
    statuseintraege_vorhanden: bool = False
    anleitung_link: Optional[str] = None

    # --- Schritt 5: Abschluss QM ---
    software_referenz_release: Optional[str] = None
    hardware_aenderungsindex: Optional[str] = None

    # Metadaten
    erstellt_am: datetime = field(default_factory=datetime.now)
    ersteller: str = "System"
    status: str = QMStatus.NEU.value

    # History und Kommentare
    history: List[HistoryEntry] = field(default_factory=list)
    kommentare: List[Kommentar] = field(default_factory=list)

    def __post_init__(self):
        """Initialisierung nach Erstellung - fügt ersten History-Eintrag hinzu"""
        if not self.history:
            self.add_history_entry(
                typ=HistoryEntryType.ERSTELLT.value,
                user=self.ersteller,
                details=f"QM {self.qm_nummer} wurde erstellt"
            )

    def add_history_entry(
        self,
        typ: str,
        details: str,
        user: str = "System",
        alter_wert: Optional[str] = None,
        neuer_wert: Optional[str] = None
    ) -> None:
        """Fügt einen neuen History-Eintrag hinzu"""
        entry = HistoryEntry(
            timestamp=datetime.now(),
            typ=typ,
            user=user,
            details=details,
            status=self.status,
            alter_wert=alter_wert,
            neuer_wert=neuer_wert
        )
        self.history.append(entry)

    def add_kommentar(self, text: str, user: str = "System") -> None:
        """Fügt einen Kommentar hinzu"""
        kommentar = Kommentar(
            timestamp=datetime.now(),
            user=user,
            text=text
        )
        self.kommentare.append(kommentar)
        self.add_history_entry(
            typ=HistoryEntryType.KOMMENTAR.value,
            user=user,
            details=f"Kommentar hinzugefügt: {text[:50]}..."
        )

    def _assert_transition(self, neuer_status: str) -> None:
        """Prüft den Statuswechsel gegen VALID_TRANSITIONS (siehe Statusdiagramm)"""
        erlaubt = VALID_TRANSITIONS.get(self.status, [])
        if neuer_status not in erlaubt:
            raise ValueError(
                f"Übergang von '{self.status}' zu '{neuer_status}' ist laut Statusdiagramm nicht erlaubt."
            )

    def change_status(self, neuer_status: str, user: str = "System") -> None:
        """Ändert den Status entlang des Hauptprozesses und dokumentiert dies in der History"""
        self._assert_transition(neuer_status)
        alter_status = self.status
        self.status = neuer_status
        self.add_history_entry(
            typ=HistoryEntryType.STATUS_GEAENDERT.value,
            user=user,
            details=f"Status geändert von '{alter_status}' zu '{neuer_status}'",
            alter_wert=alter_status,
            neuer_wert=neuer_status
        )

    def pause(self, user: str = "System", grund: Optional[str] = None) -> None:
        """Pausiert die Bearbeitung (nur aus 'In Bearbeitung' möglich)"""
        self._assert_transition(QMStatus.PAUSIERT.value)
        alter_status = self.status
        self.status = QMStatus.PAUSIERT.value
        details = "Bearbeitung pausiert"
        if grund:
            details += f": {grund}"
        self.add_history_entry(
            typ=HistoryEntryType.PAUSIERT.value,
            user=user,
            details=details,
            alter_wert=alter_status,
            neuer_wert=self.status
        )

    def resume(self, user: str = "System") -> None:
        """Setzt eine pausierte Bearbeitung fort"""
        self._assert_transition(QMStatus.IN_BEARBEITUNG.value)
        alter_status = self.status
        self.status = QMStatus.IN_BEARBEITUNG.value
        self.add_history_entry(
            typ=HistoryEntryType.FORTGESETZT.value,
            user=user,
            details="Bearbeitung fortgesetzt",
            alter_wert=alter_status,
            neuer_wert=self.status
        )

    def reopen(self, user: str = "System", grund: Optional[str] = None) -> None:
        """Eröffnet ein abgeschlossenes QM wieder (Abgeschlossen -> Wiedereröffnet)"""
        self._assert_transition(QMStatus.WIEDEREROEFFNET.value)
        alter_status = self.status
        self.status = QMStatus.WIEDEREROEFFNET.value
        details = "QM wiedereröffnet"
        if grund:
            details += f": {grund}"
        self.add_history_entry(
            typ=HistoryEntryType.WIEDEREROEFFNET.value,
            user=user,
            details=details,
            alter_wert=alter_status,
            neuer_wert=self.status
        )

    def cancel(self, user: str = "System", grund: Optional[str] = None) -> None:
        """Bricht die Bearbeitung ab (aus jedem noch offenen Schritt möglich)"""
        self._assert_transition(QMStatus.ABGEBROCHEN.value)
        alter_status = self.status
        self.status = QMStatus.ABGEBROCHEN.value
        details = "QM abgebrochen"
        if grund:
            details += f": {grund}"
        self.add_history_entry(
            typ=HistoryEntryType.ABGEBROCHEN.value,
            user=user,
            details=details,
            alter_wert=alter_status,
            neuer_wert=self.status
        )

    def assign_to(self, person: str, abteilung: Optional[str] = None, user: str = "System") -> None:
        """Weist QM einer Person/Abteilung zu"""
        alte_zuweisung = self.zugewiesen_an
        self.zugewiesen_an = person
        if abteilung:
            self.abteilung = abteilung

        details = f"Zugewiesen an {person}"
        if abteilung:
            details += f" ({abteilung})"

        self.add_history_entry(
            typ=HistoryEntryType.ZUGEWIESEN.value,
            user=user,
            details=details,
            alter_wert=alte_zuweisung,
            neuer_wert=person
        )

    def change_priority(self, neue_prioritaet: str, user: str = "System") -> None:
        """Ändert die Priorität"""
        alte_prioritaet = self.prioritaet
        self.prioritaet = neue_prioritaet
        self.add_history_entry(
            typ=HistoryEntryType.PRIORITAET_GEAENDERT.value,
            user=user,
            details=f"Priorität geändert von '{alte_prioritaet}' zu '{neue_prioritaet}'",
            alter_wert=alte_prioritaet,
            neuer_wert=neue_prioritaet
        )

    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert QM zu Dictionary (für Serialisierung)"""
        data = {
            "qm_id": self.qm_id,
            "qm_nummer": self.qm_nummer,
            "erfasser_kuerzel": self.erfasser_kuerzel,
            "erfasser_abteilung": self.erfasser_abteilung,
            "involvierte": self.involvierte,
            "titel": self.titel,
            "beschreibung": self.beschreibung,
            "wunsch_oder_mangel": self.wunsch_oder_mangel,
            "sicherheitsrelevant": self.sicherheitsrelevant,
            "hauptkategorie": self.hauptkategorie,
            "ist_software": self.ist_software,
            "plc": self.plc,
            "plc_version": self.plc_version,
            "nc": self.nc,
            "nc_version": self.nc_version,
            "mcm": self.mcm,
            "maschinentyp": self.maschinentyp,
            "serie_oder_einzelfall": self.serie_oder_einzelfall,
            "kundenrueckmeldung_noetig": self.kundenrueckmeldung_noetig,
            "ticket_nr_intern": self.ticket_nr_intern,
            "kontaktperson_servicetechniker": self.kontaktperson_servicetechniker,
            "minor_major": self.minor_major,
            "prioritaet": self.prioritaet,
            "termin_geplante_umsetzung": self.termin_geplante_umsetzung.isoformat() if self.termin_geplante_umsetzung else None,
            "abteilung": self.abteilung,
            "zugewiesen_an": self.zugewiesen_an,
            "faellig_am": self.faellig_am.isoformat() if self.faellig_am else None,
            "bearbeitung_extern": self.bearbeitung_extern,
            "ticket_nr_extern": self.ticket_nr_extern,
            "korrespondenz_extern": self.korrespondenz_extern,
            "statuseintraege_vorhanden": self.statuseintraege_vorhanden,
            "anleitung_link": self.anleitung_link,
            "software_referenz_release": self.software_referenz_release,
            "hardware_aenderungsindex": self.hardware_aenderungsindex,
            "erstellt_am": self.erstellt_am.isoformat(),
            "ersteller": self.ersteller,
            "status": self.status,
            "history": [entry.to_dict() for entry in self.history],
            "kommentare": [kommentar.to_dict() for kommentar in self.kommentare]
        }
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QualitaetsMangel':
        """Erstellt QM aus Dictionary (für Deserialisierung)"""
        data_copy = data.copy()

        # Konvertiere Datums-Strings zurück zu datetime/date
        data_copy["erstellt_am"] = datetime.fromisoformat(data_copy["erstellt_am"])
        if data_copy.get("faellig_am"):
            data_copy["faellig_am"] = date.fromisoformat(data_copy["faellig_am"])
        if data_copy.get("termin_geplante_umsetzung"):
            data_copy["termin_geplante_umsetzung"] = date.fromisoformat(data_copy["termin_geplante_umsetzung"])

        # Konvertiere History-Einträge
        history_data = data_copy.pop("history", [])
        data_copy["history"] = [HistoryEntry.from_dict(entry) for entry in history_data]

        # Konvertiere Kommentare
        kommentare_data = data_copy.pop("kommentare", [])
        data_copy["kommentare"] = [Kommentar.from_dict(komm) for komm in kommentare_data]

        return cls(**data_copy)

    def to_json(self) -> str:
        """Konvertiert QM zu JSON-String"""
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)

    @classmethod
    def from_json(cls, json_str: str) -> 'QualitaetsMangel':
        """Erstellt QM aus JSON-String"""
        data = json.loads(json_str)
        return cls.from_dict(data)

    def __str__(self) -> str:
        """String-Repräsentation"""
        return f"QM-{self.qm_nummer}: {self.titel} (Status: {self.status})"

    def __repr__(self) -> str:
        """Repr-Repräsentation"""
        return f"QualitaetsMangel(qm_id={self.qm_id}, qm_nummer='{self.qm_nummer}', titel='{self.titel}')"