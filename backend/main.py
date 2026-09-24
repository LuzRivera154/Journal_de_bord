"""Point d'entrée de l'app. Pour l'instant : connexion à la base + un endpoint
de test. Chaque module (observations, navigation, stats, journal, assistant...)
aura son propre fichier dans routers/, à ajouter ici avec app.include_router().
"""
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from apscheduler.schedulers.background import BackgroundScheduler

from config import config
from database import engine, SessionLocal, Base, get_db
import models
import schemas
from routers import assistant, navigation, stats, incidents, population, journal
from routers import navigation, stats, incidents, population, journal, crise
from services.scheduler import (
    demarrer_scheduler,
    modifier_intervalle_capture,
    tache_capture_manuelle,
)

app = FastAPI(title=config["app"]["name"])


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)



app.include_router(navigation.router)
app.include_router(stats.router)
app.include_router(incidents.router)
app.include_router(population.router)
app.include_router(journal.router)
app.include_router(assistant.router)
app.include_router(crise.router)



@app.on_event("startup")
def au_demarrage():
    Base.metadata.create_all(bind=engine)
    _creer_secteurs_initiaux()
    demarrer_scheduler()


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


@app.get("/health")
@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/secteurs", response_model=list[schemas.SecteurOut])
def lister_secteurs(db: Session = Depends(get_db)):
    return db.query(models.Secteur).all()


@app.put("/api/scheduler/interval")
def changer_intervalle(minutes: int):
    modifier_intervalle_capture(minutes)
    return {"message": f"Intervalle modifié à {minutes} minutes"}


# TODO FRONTEND : le bouton "Capture manuelle" devra appeler cette API.
@app.post("/api/capture/manuelle")
def capture_manuelle():
    return tache_capture_manuelle()

# Sert le tableau de bord (index.html, navigation.html, css/, js/).
# Monté en dernier pour que les routes /api/* ci-dessus restent prioritaires.
app.mount("/", StaticFiles(directory="../frontend", html=True), name="frontend")
