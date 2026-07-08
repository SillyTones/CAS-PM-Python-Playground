"""
QM Data Reader - Laden von Sample-Daten
========================================
Funktionen zum Laden und Speichern von QM-Daten aus/in JSON-Dateien.
"""

import json
from typing import List, Dict, Any
from pathlib import Path
from qm_model import QualitaetsMangel


class QMDataReader:
    """Reader für QM-Daten aus JSON-Dateien"""
    
    @staticmethod
    def load_from_file(filepath: str) -> List[QualitaetsMangel]:
        """
        Lädt QM-Liste aus JSON-Datei
        
        Args:
            filepath: Pfad zur JSON-Datei
            
        Returns:
            Liste von QualitaetsMangel-Objekten
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            qm_liste = []
            for qm_data in data:
                qm = QualitaetsMangel.from_dict(qm_data)
                qm_liste.append(qm)
            
            return qm_liste
        except FileNotFoundError:
            print(f"Datei nicht gefunden: {filepath}")
            return []
        except json.JSONDecodeError as e:
            print(f"Fehler beim Parsen der JSON-Datei: {e}")
            return []
        except Exception as e:
            print(f"Fehler beim Laden der Daten: {e}")
            return []
    
    @staticmethod
    def save_to_file(qm_liste: List[QualitaetsMangel], filepath: str) -> bool:
        """
        Speichert QM-Liste in JSON-Datei
        
        Args:
            qm_liste: Liste von QualitaetsMangel-Objekten
            filepath: Pfad zur Zieldatei
            
        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            data = [qm.to_dict() for qm in qm_liste]
            
            # Stelle sicher, dass das Verzeichnis existiert
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"Fehler beim Speichern der Daten: {e}")
            return False
    
    @staticmethod
    def load_sample_data() -> List[QualitaetsMangel]:
        """
        Lädt die Standard-Sample-Daten
        
        Returns:
            Liste von QualitaetsMangel-Objekten
        """
        return QMDataReader.load_from_file("qm_sample_data.json")


def load_qm_data(filepath: str = "qm_sample_data.json") -> List[QualitaetsMangel]:
    """
    Convenience-Funktion zum Laden von QM-Daten
    
    Args:
        filepath: Pfad zur JSON-Datei (Standard: qm_sample_data.json)
        
    Returns:
        Liste von QualitaetsMangel-Objekten
    """
    reader = QMDataReader()
    return reader.load_from_file(filepath)


def save_qm_data(qm_liste: List[QualitaetsMangel], filepath: str = "qm_data_backup.json") -> bool:
    """
    Convenience-Funktion zum Speichern von QM-Daten
    
    Args:
        qm_liste: Liste von QualitaetsMangel-Objekten
        filepath: Pfad zur Zieldatei
        
    Returns:
        True bei Erfolg, False bei Fehler
    """
    reader = QMDataReader()
    return reader.save_to_file(qm_liste, filepath)


# Beispiel-Verwendung
if __name__ == "__main__":
    # Lade Sample-Daten
    qm_liste = load_qm_data("qm_sample_data.json")
    
    print(f"Geladene QMs: {len(qm_liste)}")
    for qm in qm_liste:
        print(f"  - {qm}")
        print(f"    Status: {qm.status}")
        print(f"    History-Einträge: {len(qm.history)}")
        print()
