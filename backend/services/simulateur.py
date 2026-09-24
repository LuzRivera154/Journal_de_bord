"""Génère des données simulées : taux d'oxygène, niveaux de réserves, et
secteurs en maintenance (STA-02) — pour compléter le tableau de bord sans
dépendre de capteurs réels qu'on n'a pas encore.

Chaque simulateur peut être activé/désactivé indépendamment dans
config.yaml (section "simulateurs").
"""
import random
from datetime import datetime, timedelta

from config import config
from models import Mesure, Maintenance, Secteur, Population, Reserve
from services.alertes import verifier_seuil

SIMULATEURS_CONFIG = config["simulateurs"]
RESERVES_CONFIG = config["reserves"]

# Panneau "Secteurs" du Bord : ce qui est simulé pour chaque secteur, en
# plus de l'oxygène (déjà géré par simuler_oxygene ci-dessous).
MESURES_SECTEUR_SIMULEES = [
    {"type": "co2", "unite": "ppm", "min": 450, "max": 900},
    {"type": "pression", "unite": "kPa", "min": 100.5, "max": 101.5},
    {"type": "temperature", "unite": "°C", "min": 18.0, "max": 26.0},
    {"type": "humidite", "unite": "%", "min": 35.0, "max": 65.0},
]

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


def simuler_secteurs(db):
    """CO2, pression, température et humidité par secteur, pour le
    panneau "Secteurs" du Bord (l'oxygène est déjà géré séparément par
    simuler_oxygene, ci-dessus)."""
    if not SIMULATEURS_CONFIG["secteurs"]:
        return []

    mesures = []
    for secteur in db.query(Secteur).all():
        for info in MESURES_SECTEUR_SIMULEES:
            mesure = Mesure(
                id_secteur=secteur.id,
                type=info["type"],
                valeur=round(random.uniform(info["min"], info["max"]), 1),
                unite=info["unite"],
                source="simulee",
            )
            db.add(mesure)
            mesures.append(mesure)
    db.commit()
    return mesures


def simuler_occupation(db):
    """Répartit l'effectif total simulé entre les secteurs, pour la
    colonne "Équipage" du panneau "Secteurs" — approximatif, juste pour
    que le tableau de bord ait quelque chose à montrer."""
    if not SIMULATEURS_CONFIG["secteurs"]:
        return []

    secteurs = db.query(Secteur).all()
    if not secteurs:
        return []

    derniere_population = db.query(Population).order_by(Population.horodatage.desc()).first()
    restant = derniere_population.nombre_personnes if derniere_population else 0

    mesures = []
    for i, secteur in enumerate(secteurs):
        if i == len(secteurs) - 1:
            nombre = restant  # le dernier secteur récupère ce qui reste, pour que le total soit juste
        else:
            nombre = random.randint(0, restant)
            restant -= nombre

        mesure = Mesure(id_secteur=secteur.id, type="occupation", valeur=nombre, unite="personnes", source="simulee")
        db.add(mesure)
        mesures.append(mesure)
    db.commit()
    return mesures


def simuler_reserves(db):
    """Fait descendre chaque réserve (eau, nourriture...) selon sa
    consommation par jour, au rythme de l'intervalle de simulation —
    panneau "Réserves et besoins" du Bord."""
    if not SIMULATEURS_CONFIG["reserves"]:
        return []

    minutes_ecoulees = config["scheduler"]["simulation_interval_minutes"]
    fraction_de_jour = minutes_ecoulees / (24 * 60)

    reserves = db.query(Reserve).all()
    for reserve in reserves:
        consommation_par_jour = RESERVES_CONFIG[reserve.type]["consommation_par_jour"]
        reserve.quantite_actuelle = max(0.0, reserve.quantite_actuelle - consommation_par_jour * fraction_de_jour)
    db.commit()
    return reserves
