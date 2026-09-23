"""Tâches qui doivent se déclencher automatiquement chaque jour, sans action
de l'équipage (cf. NFR "Fonctionnement hors ligne" : tout tourne en local,
rien ne dépend d'une requête extérieure pour se lancer).
"""
import cv2
from datetime import datetime
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler

from config import config
from database import SessionLocal
from services.navigation import calculer_position_du_jour
from services.dht22 import enregistrer_lecture_dht22

SCHEDULER_CONFIG = config["scheduler"]

scheduler = BackgroundScheduler()


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


def tache_lecture_dht22():
    """Relève température et humidité du DHT22 (STA-01)."""
    db = SessionLocal()
    try:
        enregistrer_lecture_dht22(db)
    finally:
        db.close()


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
    scheduler.start()
