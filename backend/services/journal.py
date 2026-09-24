"""Génération du journal de bord quotidien (section 4.4 du cahier des charges).


"""
import json
from datetime import datetime, timedelta

import httpx

from config import config, get_ollama_base_url
from models import Journal, Position, Mesure, Incident, Maintenance, Observation

OLLAMA_CONFIG = config["ollama"]

CONSIGNE = (
    "Tu es l'assistant de bord d'un vaisseau spatial autonome. "
    "Rédige le journal de bord du jour à partir UNIQUEMENT des données JSON "
    "fournies ci-dessous. N'invente aucune information absente de ces "
    "données ; si une donnée manque, dis-le clairement.\n\n"
    "Structure le texte en 5 parties, dans cet ordre : Position, État "
    "général, Incidents, Maintenance, Besoins et observations.\n\n"
    "Format à respecter strictement :\n"
    "- '## ' devant le titre de chaque partie (ex: '## Position')\n"
    "- '- ' devant chaque élément de liste\n"
    "- une ligne par paragraphe, pas de texte sur plusieurs lignes collées\n\n"
    "Données du jour :\n"
)


def _vers_dict(ligne):
    """Transforme une ligne de la base en dictionnaire simple, pour pouvoir
    la mettre dans le JSON envoyé au modèle."""
    if ligne is None:
        return None

    resultat = {}
    for colonne in ligne.__table__.columns:
        valeur = getattr(ligne, colonne.name)
        if isinstance(valeur, datetime):
            valeur = valeur.isoformat()
        resultat[colonne.name] = valeur
    return resultat


def _resumer_mesures(mesures):
    """Résume les mesures du jour par type (min/max/moyenne), au lieu
    d'envoyer chaque ligne individuelle au modèle — un secteur avec un
    relevé toutes les 15 minutes peut vite faire des centaines de lignes
    presque identiques, ce qui ralentit beaucoup Ollama pour rien."""
    par_type = {}
    for mesure in mesures:
        if mesure.type not in par_type:
            par_type[mesure.type] = {"valeurs": [], "unite": mesure.unite, "source": mesure.source}
        par_type[mesure.type]["valeurs"].append(mesure.valeur)

    resume = {}
    for type_mesure, info in par_type.items():
        valeurs = info["valeurs"]
        resume[type_mesure] = {
            "min": round(min(valeurs), 2),
            "max": round(max(valeurs), 2),
            "moyenne": round(sum(valeurs) / len(valeurs), 2),
            "nombre_releves": len(valeurs),
            "unite": info["unite"],
            "source": info["source"],
        }
    return resume


def rassembler_donnees_du_jour(db):
    """Rassemble ce qu'on sait sur les dernières 24h. Une donnée manquante
    donne juste une valeur vide, ça ne bloque rien (NFR "Résilience")."""
    depuis = datetime.utcnow() - timedelta(hours=24)

    derniere_position = db.query(Position).order_by(Position.date.desc()).first()
    mesures_du_jour = db.query(Mesure).filter(Mesure.horodatage >= depuis).all()
    incidents_ouverts = db.query(Incident).filter(Incident.statut != "resolu").all()
    maintenance_en_cours = db.query(Maintenance).filter(Maintenance.statut != "terminee").all()
    observations_du_jour = db.query(Observation).filter(Observation.horodatage >= depuis).all()

    return {
        "position": _vers_dict(derniere_position),
        "mesures_resumees": _resumer_mesures(mesures_du_jour),
        "incidents_ouverts": [_vers_dict(i) for i in incidents_ouverts],
        "maintenance_en_cours": [_vers_dict(m) for m in maintenance_en_cours],
        "observations": [_vers_dict(o) for o in observations_du_jour],
    }


def generer_journal(db):
    """Rassemble les données, appelle Ollama (ou le repli), et enregistre le
    journal dans la table journaux (US-5.1, critère 3)."""
    donnees = rassembler_donnees_du_jour(db)
    donnees_json = json.dumps(donnees, ensure_ascii=False)

    texte, modele = _appeler_ollama(donnees_json)

    journal = Journal(
        date=datetime.utcnow(),
        texte_genere=texte,
        donnees_sources=donnees_json,
        modele_utilise=modele,
    )
    db.add(journal)
    db.commit()
    db.refresh(journal)
    return journal


def _appeler_ollama(donnees_json):
    if not OLLAMA_CONFIG["enabled"]:
        return _texte_repli(donnees_json), "gabarit_repli"

    try:
        reponse = httpx.post(
            get_ollama_base_url() + "/api/generate",
            json={
                "model": OLLAMA_CONFIG["model"],
                "prompt": CONSIGNE + donnees_json,
                "stream": False,
            },
            timeout=OLLAMA_CONFIG["timeout_seconds"],
        )
        reponse.raise_for_status()
        texte = reponse.json()["response"]
        return texte, OLLAMA_CONFIG["model"]
    except Exception:
        # Ollama pas démarré, modèle pas téléchargé, trop lent...
        return _texte_repli(donnees_json), "gabarit_repli"


def _texte_repli(donnees_json):
    """Journal minimal, sans IA, à partir d'un texte fixe (solution de repli,
    section 13 du cahier des charges)."""
    donnees = json.loads(donnees_json)
    position = donnees.get("position")
    incidents = donnees.get("incidents_ouverts", [])
    maintenances = donnees.get("maintenance_en_cours", [])
    mesures = donnees.get("mesures_resumees", {})

    lignes = [
        "[Journal généré automatiquement — modèle de langage indisponible]",
        "",
        "## Position",
        str(position) if position else "Donnée manquante.",
        "",
        "## État général",
        str(mesures) if mesures else "Aucun relevé disponible sur les dernières 24h.",
        "",
        "## Incidents",
        str(len(incidents)) + " incident(s) en cours.",
        "",
        "## Maintenance",
        str(len(maintenances)) + " maintenance(s) en cours." if maintenances else "Aucune maintenance en cours.",
        "",
        "## Besoins et observations",
        "Pas de résumé automatique disponible sans le modèle de langage.",
    ]
    return "\n".join(lignes)
