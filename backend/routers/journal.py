"""Endpoints du module Journal de bord (section 4.4 du cahier des charges)."""
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db
from services.journal import generer_journal

router = APIRouter(prefix="/api/journal", tags=["journal"])


@router.post("/generer", response_model=schemas.JournalOut)
def generer(db: Session = Depends(get_db)):
    """Génère le journal du jour tout de suite.

    Se lance aussi automatiquement à heure fixe via le scheduler (voir
    services/scheduler.py, US-5.1) — cet endpoint sert surtout à tester
    sans attendre l'heure configurée."""
    return generer_journal(db)


@router.get("/", response_model=list[schemas.JournalOut])
def lister_journaux(
    date: str | None = None,
    du: str | None = None,
    au: str | None = None,
    db: Session = Depends(get_db),
):
    """Archive des journaux, le plus récent en premier.

    Filtrable par date exacte (ex: ?date=2026-09-24) ou par plage de dates
    (ex: ?du=2026-09-20&au=2026-09-24) — US-5.4, critères 1 et 2."""
    requete = db.query(models.Journal)

    if date:
        debut_jour = datetime.strptime(date, "%Y-%m-%d")
        fin_jour = debut_jour + timedelta(days=1)
        requete = requete.filter(models.Journal.date >= debut_jour, models.Journal.date < fin_jour)

    if du:
        requete = requete.filter(models.Journal.date >= datetime.strptime(du, "%Y-%m-%d"))

    if au:
        fin_plage = datetime.strptime(au, "%Y-%m-%d") + timedelta(days=1)
        requete = requete.filter(models.Journal.date < fin_plage)

    return requete.order_by(models.Journal.date.desc()).all()


@router.get("/{journal_id}", response_model=schemas.JournalOut)
def obtenir_journal(journal_id: int, db: Session = Depends(get_db)):
    journal = db.query(models.Journal).filter(models.Journal.id == journal_id).first()
    if journal is None:
        raise HTTPException(status_code=404, detail="Journal introuvable.")
    return journal
