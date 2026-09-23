"""Tâches qui doivent se déclencher automatiquement chaque jour, sans action
de l'équipage (cf. NFR "Fonctionnement hors ligne" : tout tourne en local,
rien ne dépend d'une requête extérieure pour se lancer).
"""
from apscheduler.schedulers.background import BackgroundScheduler

from config import config
from database import SessionLocal
from services.navigation import calculer_position_du_jour

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
    """Déclenche une capture automatique."""
    print("Capture automatique")


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
    scheduler.start()
