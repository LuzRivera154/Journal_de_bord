"""Lecture du capteur DHT22 (température + humidité) via l'Arduino en USB
série (STA-01).

Si l'Arduino n'est pas branché ou ne répond pas, on retombe sur une valeur
simulée pour ne pas bloquer le reste du système (cf. NFR "Résilience") —
mais on essaie toujours la vraie mesure en premier. Voir arduino/README.md
pour le format attendu sur le port série (texte, pas JSON : ex.
"Temperature: 22.4 C | Humidite: 45 % | Gaz: 612").
"""
import random

import serial

from config import config
from models import Mesure, Secteur
from services.alertes import verifier_seuil

DHT22_CONFIG = config["dht22"]


def _parser_ligne_arduino(ligne):
    """Lit une ligne du genre "Temperature: 22.4 C | Humidite: 45 % | Gaz: 612"
    et retourne {"temperature": ..., "humidite": ...}. Retourne None si la
    ligne n'a pas ce format (ex: une ligne "ALERTE ..." de la carte, ou une
    ligne coupée en cours de lecture)."""
    valeurs = {}

    for segment in ligne.split("|"):
        segment = segment.strip()
        try:
            if segment.startswith("Temperature:"):
                valeurs["temperature"] = float(segment.replace("Temperature:", "").replace("C", "").strip())
            elif segment.startswith("Humidite:"):
                valeurs["humidite"] = float(segment.replace("Humidite:", "").replace("%", "").strip())
        except ValueError:
            return None

    if "temperature" in valeurs and "humidite" in valeurs:
        return valeurs
    return None


def lire_dht22():
    """Retourne {"temperature": ..., "humidite": ..., "source": "reelle"|"simulee"}."""
    try:
        with serial.Serial(
            DHT22_CONFIG["serial_port"],
            DHT22_CONFIG["baud_rate"],
            timeout=DHT22_CONFIG["read_timeout_seconds"],
        ) as ligne_serie:
            # Entre deux relevés, la carte peut aussi envoyer des lignes
            # "ALERTE ..." qui ne sont pas des mesures — on essaie
            # plusieurs lignes avant d'abandonner.
            for _ in range(5):
                ligne = ligne_serie.readline().decode("utf-8", errors="ignore").strip()
                mesure = _parser_ligne_arduino(ligne)
                if mesure:
                    mesure["source"] = "reelle"
                    return mesure
    except Exception:
        pass

    # Port série absent, Arduino débranché, aucune ligne exploitable... -> on simule
    return {
        "temperature": round(random.uniform(18.0, 24.0), 1),
        "humidite": round(random.uniform(35.0, 55.0), 1),
        "source": "simulee",
    }


def enregistrer_lecture_dht22(db):
    """Lit le capteur et enregistre température + humidité dans mesures (STA-01)."""
    lecture = lire_dht22()
    secteur = db.query(Secteur).filter_by(nom=DHT22_CONFIG["secteur"]).first()

    mesure_temperature = Mesure(
        id_secteur=secteur.id if secteur else None,
        type="temperature",
        valeur=lecture["temperature"],
        unite="°C",
        source=lecture["source"],
    )
    mesure_humidite = Mesure(
        id_secteur=secteur.id if secteur else None,
        type="humidite",
        valeur=lecture["humidite"],
        unite="%",
        source=lecture["source"],
    )
    db.add(mesure_temperature)
    db.add(mesure_humidite)
    db.commit()
    db.refresh(mesure_temperature)
    db.refresh(mesure_humidite)

    # Si la température ou l'humidité sort de la plage normale, ça crée un
    # incident tout seul (US-4.3, création automatique).
    verifier_seuil(mesure_temperature, db)
    verifier_seuil(mesure_humidite, db)

    return mesure_temperature, mesure_humidite
