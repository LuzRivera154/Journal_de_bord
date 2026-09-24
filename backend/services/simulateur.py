"""Génère des données simulées : taux d'oxygène, niveaux de réserves, et
secteurs en maintenance (STA-02) — pour compléter le tableau de bord sans
dépendre de capteurs réels qu'on n'a pas encore.

Chaque simulateur peut être activé/désactivé indépendamment dans
config.yaml (section "simulateurs").
"""
import random
from datetime import datetime, timedelta

from config import config
from models import Mesure, Maintenance, Secteur
from services.alertes import verifier_seuil

SIMULATEURS_CONFIG = config["simulateurs"]

# Réserves générales du vaisseau (pas liées à un secteur précis).
STOCKS_SIMULES = [
    {"type": "stock_eau", "unite": "%", "min": 40, "max": 95},
    {"type": "stock_nourriture", "unite": "%", "min": 30, "max": 90},
    {"type": "stock_oxygene_reserve", "unite": "%", "min": 50, "max": 100},
]


def simuler_oxygene(db):
    """Un taux d'oxygène simulé par secteur."""
    if not SIMULATEURS_CONFIG["oxygene"]:
        return []

    mesures = []
    for secteur in db.query(Secteur).all():
        mesure = Mesure(
            id_secteur=secteur.id,
            type="oxygene",
            valeur=round(random.uniform(19.5, 21.0), 2),
            unite="%",
            source="simulee",
        )
        db.add(mesure)
        mesures.append(mesure)
    db.commit()

    # Si un taux d'oxygène simulé tombe sous le seuil, ça crée un incident
    # tout seul (US-4.3, création automatique).
    for mesure in mesures:
        verifier_seuil(mesure, db)

    return mesures


def simuler_stocks(db):
    """Niveaux de réserves simulés (eau, nourriture, oxygène de secours)."""
    if not SIMULATEURS_CONFIG["stocks"]:
        return []

    mesures = []
    for stock in STOCKS_SIMULES:
        mesure = Mesure(
            id_secteur=None,
            type=stock["type"],
            valeur=round(random.uniform(stock["min"], stock["max"]), 1),
            unite=stock["unite"],
            source="simulee",
        )
        db.add(mesure)
        mesures.append(mesure)
    db.commit()
    return mesures


def simuler_maintenance(db):
    """De temps en temps, met un secteur en maintenance simulée.

    Pas à chaque passage, sinon on aurait un secteur en maintenance en
    permanence — juste une petite chance à chaque appel.
    """
    if not SIMULATEURS_CONFIG["maintenance"]:
        return None
    if random.random() > 0.15:
        return None

    secteurs = db.query(Secteur).all()
    if not secteurs:
        return None

    secteur = random.choice(secteurs)
    maintenance = Maintenance(
        id_secteur=secteur.id,
        debut=datetime.utcnow(),
        fin_prevue=datetime.utcnow() + timedelta(hours=random.randint(2, 12)),
        motif="Maintenance simulée",
        statut="en_cours",
    )
    db.add(maintenance)
    db.commit()
    return maintenance
