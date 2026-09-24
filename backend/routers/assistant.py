import httpx

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db
from config import config, get_ollama_base_url


router = APIRouter(prefix="/api/assistant", tags=["assistant"])

OLLAMA_URL = get_ollama_base_url()
OLLAMA_MODEL = config["ollama"]["model"]


@router.post("/ask", response_model=schemas.AskResponse)
def poser_question(
    demande: schemas.AskRequest,
    db: Session = Depends(get_db),
):
    mesures = (
        db.query(models.Mesure)
        .order_by(models.Mesure.horodatage.desc())
        .limit(20)
        .all()
    )

    incidents = (
        db.query(models.Incident)
        .order_by(models.Incident.horodatage.desc())
        .limit(10)
        .all()
    )

    dernier_journal = (
        db.query(models.Journal)
        .order_by(models.Journal.date.desc())
        .first()
    )

    secteurs = db.query(models.Secteur).all()

    noms_secteurs = [secteur.nom for secteur in secteurs]
    
    contexte = {
        "mesures": [
            {
                "type": m.type,
                "valeur": m.valeur,
                "unite": m.unite,
                "date": m.horodatage.isoformat(),
            }
            for m in mesures
        ],
        "incidents": [
            {
                "gravite": i.gravite,
                "description": i.description,
                "statut": i.statut,
                "date": i.horodatage.isoformat(),
            }
            for i in incidents
        ],
        "dernier_journal": (
            {
                "date": dernier_journal.date.isoformat(),
                "texte": dernier_journal.texte_genere,
            }
            if dernier_journal
            else None
        ),
    }

    question = demande.question.lower()

    for secteur in noms_secteurs:
        if secteur.lower() in question:
            break
        else:
            if "secteur" in question:
                return {
                    "reponse": "Je ne trouve pas ce secteur dans les données de la base.",
                    "source": "bdd",
                }

    prompt = f"""
Tu es l'assistant de bord d'une navette spatiale.

Réponds à la question de l'équipage uniquement avec les données fournies
ci-dessous.

Règles :
- N'invente aucune donnée.
- Si l'information n'est pas présente, dis que tu ne la trouves pas.
- Réponds en français.
- Sois bref et précis.

Secteurs existants dans la base :
{", ".join(noms_secteurs)}

Question :
{demande.question}

Données de la base :
{contexte}
"""

    with httpx.Client(timeout=config["ollama"]["timeout_seconds"]) as client:
        reponse = client.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
            },
        )

    reponse.raise_for_status()

    resultat = reponse.json()

    return {
        "reponse": resultat["response"],
        "source": "ollama",
    }
