"""Endpoint du module Population (section 4.3 du cahier des charges, STA-04)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db
from services.population import enregistrer_population_reelle

router = APIRouter(prefix="/api/population", tags=["population"])


@router.get("/", response_model=schemas.PopulationOut)
def obtenir_population(db: Session = Depends(get_db)):
    """Effectif actuel à bord (le plus récent connu).

    Disponible pour le tableau de bord et, plus tard, pour la génération du
    journal (US-4.4, critère 2)."""
    derniere = db.query(models.Population).order_by(models.Population.horodatage.desc()).first()
    if derniere is None:
        raise HTTPException(status_code=404, detail="Aucune donnée de population pour l'instant.")
    return derniere


@router.post("/", response_model=schemas.PopulationOut)
def recevoir_population(donnee: schemas.PopulationIn, db: Session = Depends(get_db)):
    """Reçoit un effectif réel envoyé par un autre projet (la caméra à
    reconnaissance faciale) — format d'échange, section 10 du cahier des
    charges. Utilisé seulement si population.source = "reelle" dans
    config.yaml, sinon le simulateur écrase avec ses propres valeurs."""
    return enregistrer_population_reelle(db, donnee.nombre_personnes)
