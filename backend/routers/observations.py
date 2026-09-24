"""Endpoints du module Observation stellaire (Épic 2)."""
import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db
from services.observation import detecter_etoiles

router = APIRouter(prefix="/api/observations", tags=["observations"])


@router.get("/", response_model=list[schemas.ObservationOut])
def lister_observations(db: Session = Depends(get_db)):
    """Historique des observations (une par capture), la plus récente en premier."""
    return db.query(models.Observation).order_by(models.Observation.horodatage.desc()).all()


@router.post("/{observation_id}/analyser", response_model=schemas.ObservationOut)
def analyser_observation(observation_id: int, db: Session = Depends(get_db)):
    """Relance la détection d'étoiles sur une observation déjà capturée —
    sert surtout à retester sans reprendre une photo."""
    observation = db.query(models.Observation).filter_by(id=observation_id).first()
    if observation is None:
        raise HTTPException(status_code=404, detail="Observation introuvable.")

    etoiles = detecter_etoiles(observation.chemin_image)
    observation.etoiles_detectees = json.dumps(etoiles)
    # La détection elle-même ne "rate" jamais (liste vide si rien trouvé,
    # critère 3) — "echec" est réservé à un problème plus en amont (image
    # illisible, capture ratée).
    observation.statut_analyse = "reussi"
    db.commit()
    db.refresh(observation)
    return observation
