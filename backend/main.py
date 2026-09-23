"""Point d'entrée de l'app. Pour l'instant : connexion à la base + un endpoint
de test. Chaque module (observations, navigation, stats, journal, assistant...)
aura son propre fichier dans routers/, à ajouter ici avec app.include_router().
"""
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from apscheduler.schedulers.background import BackgroundScheduler

from config import config
from database import engine, SessionLocal, Base, get_db
import models
import schemas

app = FastAPI(title=config["app"]["name"])

# Scheduler exécuté en arrière-plan
scheduler = BackgroundScheduler()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# capture exécutée toutes les 60 min
def test_capture():
    print("Capture automatique")


@app.on_event("startup")
def au_demarrage():
    Base.metadata.create_all(bind=engine)
    _creer_secteurs_initiaux()

    # Lance la capture selon l'intervalle défini dans config.yaml
    scheduler.add_job(
        test_capture,
        "interval",
        minutes=config["scheduler"]["observation_interval_minutes"],
    )
    scheduler.start()


def _creer_secteurs_initiaux():
    """Crée les secteurs de config.yaml au premier démarrage, si la table est vide."""
    db = SessionLocal()
    try:
        if db.query(models.Secteur).count() == 0:
            for nom in config["secteurs_initiaux"]:
                db.add(models.Secteur(nom=nom))
            db.commit()
    finally:
        db.close()


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/secteurs", response_model=list[schemas.SecteurOut])
def lister_secteurs(db: Session = Depends(get_db)):
    return db.query(models.Secteur).all()
