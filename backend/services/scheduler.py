"""Tâches qui doivent se déclencher automatiquement chaque jour, sans action
de l'équipage (cf. NFR "Fonctionnement hors ligne" : tout tourne en local,
rien ne dépend d'une requête extérieure pour se lancer).
"""
import json

import cv2
from datetime import datetime
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler

from config import config
from database import SessionLocal
from models import Observation
from services.navigation import calculer_position_du_jour
from services.dht22 import enregistrer_lecture_dht22
from services.simulateur import (
    simuler_oxygene,
    simuler_stocks,
    simuler_maintenance,
    simuler_secteurs,
    simuler_occupation,
    simuler_reserves,
)
from services.population import simuler_population
from services.journal import generer_journal
from services.crise import crise_active
from services.observation import detecter_etoiles


SCHEDULER_CONFIG = config["scheduler"]

scheduler = BackgroundScheduler()


def _enregistrer_observation(chemin):
    """Après une capture réussie : enregistre l'observation et détecte les
    étoiles dessus tout de suite (Épic 2 — la détection est locale et
    rapide, pas besoin d'une étape séparée)."""
    db = SessionLocal()
    try:
        etoiles = detecter_etoiles(chemin)
        observation = Observation(
            chemin_image=chemin,
            etoiles_detectees=json.dumps(etoiles),
            statut_analyse="reussi",
        )
        db.add(observation)
        db.commit()
    finally:
        db.close()


def tache_calcul_position():
    """Calcule la position du jour (NAV-01)."""
    db = SessionLocal()
    try:
        calculer_position_du_jour(db)
    finally:
        db.close()


def tache_capture_automatique():
    """
    Prend une photo et l'enregistre avec son horodatage.

    NOTE : VideoCapture(0) utilise actuellement la webcam du PC pour les tests,modifier cette partie pour utiliser la caméra définitive du projet.
    """
    db = SessionLocal()
    try:
        if crise_active(db):
            # Scénario de crise (Épic 7) : la caméra est hors service tant
            # que la crise n'est pas terminée.
            print("Capture automatique ignorée : crise en cours (caméra indisponible).")
            return
    finally:
        db.close()

    dossier = Path(config["camera"]["capture_dir"]) / "Automatiques"
    dossier.mkdir(parents=True, exist_ok=True)

    camera = cv2.VideoCapture(0)
    succes, image = camera.read()
    camera.release()

    if not succes:
        print("Erreur : impossible de prendre la photo.")
        return

    horodatage = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    chemin = dossier / f"capture_{horodatage}.jpg"

    cv2.imwrite(str(chemin), image)
    print(f"Capture enregistrée : {chemin}")
    _enregistrer_observation(str(chemin))


def tache_lecture_dht22():
    """Relève température et humidité du DHT22 (STA-01)."""
    db = SessionLocal()
    try:
        enregistrer_lecture_dht22(db)
    finally:
        db.close()


def tache_generation_journal():
    """Génère le journal du jour, à heure fixe (US-5.1)."""
    db = SessionLocal()
    try:
        generer_journal(db)
    finally:
        db.close()


def tache_simulation():
    """Génère les données simulées : oxygène, stocks, maintenance, secteurs,
    réserves (STA-02)."""
    db = SessionLocal()
    try:
        simuler_oxygene(db)
        simuler_stocks(db)
        simuler_maintenance(db)
        simuler_population(db)
        simuler_occupation(db)  # après simuler_population, pour répartir le total à jour
        simuler_secteurs(db)
        simuler_reserves(db)
    finally:
        db.close()


def tache_capture_manuelle():
    """Prend une photo manuelle et l'enregistre avec son horodatage."""
    db = SessionLocal()
    try:
        if crise_active(db):
            return {"success": False, "message": "Caméra indisponible : crise en cours."}
    finally:
        db.close()

    dossier = Path(config["camera"]["capture_dir"]) / "Manuelles"
    dossier.mkdir(parents=True, exist_ok=True)

    # TODO : remplacer la webcam de test par la caméra extérieure du projet
    camera = cv2.VideoCapture(0)
    succes, image = camera.read()
    camera.release()

    if not succes:
        return {"success": False, "message": "Impossible de prendre la photo."}

    horodatage = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    chemin = dossier / f"capture_{horodatage}.jpg"

    cv2.imwrite(str(chemin), image)
    _enregistrer_observation(str(chemin))

    return {"success": True, "chemin": str(chemin)}


# TODO FRONTEND : ajouter un bouton permettant de modifier l'intervalle
# Le bouton devra appeler cette API (PUT /api/scheduler/interval)
# avec le nombre de minutes choisi par l'utilisateur
def modifier_intervalle_capture(minutes: int):
    """Modifie l'intervalle des captures sans redémarrer le service."""
    scheduler.reschedule_job(
        "capture_automatique",
        trigger="interval",
        minutes=minutes,
    )


def demarrer_scheduler():
    if not SCHEDULER_CONFIG["enabled"]:
        return

    scheduler.add_job(
        tache_calcul_position,
        "cron",
        hour=SCHEDULER_CONFIG["navigation_calculation_hour"],
        id="calcul_position",
        replace_existing=True,
    )

    scheduler.add_job(
        tache_capture_automatique,
        "interval",
        minutes=SCHEDULER_CONFIG["observation_interval_minutes"],
        id="capture_automatique",
        replace_existing=True,
    )

    scheduler.add_job(
        tache_lecture_dht22,
        "interval",
        minutes=SCHEDULER_CONFIG["dht22_read_interval_minutes"],
        id="lecture_dht22",
        replace_existing=True,
    )

    scheduler.add_job(
        tache_simulation,
        "interval",
        minutes=SCHEDULER_CONFIG["simulation_interval_minutes"],
        id="simulation",
        replace_existing=True,
    )

    scheduler.add_job(
        tache_generation_journal,
        "cron",
        hour=SCHEDULER_CONFIG["journal_generation_hour"],
        id="generation_journal",
        replace_existing=True,
    )
    scheduler.start()
