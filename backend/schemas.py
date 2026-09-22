"""Schémas Pydantic : la forme des données qui entrent/sortent de l'API."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class SecteurOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nom: str
    description: Optional[str]


class MesureIn(BaseModel):
    """Format d'échange défini section 10 du cahier des charges.

    Exemple : {"source": "serre", "horodatage": "...", "type": "humidite",
               "valeur": 62, "unite": "%"}
    """
    source: str
    horodatage: Optional[datetime] = None
    type: str
    valeur: float
    unite: str
    secteur: Optional[str] = None  # nom du secteur (optionnel)


class MesureOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    horodatage: datetime
    id_secteur: Optional[int]
    type: str
    valeur: float
    unite: str
    source: str


class IncidentIn(BaseModel):
    secteur: Optional[str] = None
    gravite: str = "moyenne"
    description: str
    statut: str = "ouvert"


class IncidentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    horodatage: datetime
    id_secteur: Optional[int]
    gravite: str
    description: str
    statut: str


class PositionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    date: datetime
    x: float
    y: float
    z: float
    vitesse: float
    incertitude: float
    methode: str


class NavigationStatus(BaseModel):
    position_actuelle: PositionOut
    trajet: List[PositionOut]
    distance_restante: float
    destination: str
    eta_jours: float


class ObservationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    horodatage: datetime
    chemin_image: Optional[str]
    ascension_droite: Optional[float]
    declinaison: Optional[float]
    constellations_detectees: Optional[str]
    statut_analyse: str


class JournalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    date: datetime
    texte_genere: str
    donnees_sources: Optional[str]
    modele_utilise: str
    notes_manuelles: Optional[str]
    id_utilisateur: Optional[int]


class NoteIn(BaseModel):
    texte: str


class AskRequest(BaseModel):
    question: str


class AskResponse(BaseModel):
    reponse: str
    source: str  # "ollama" ou "repli" (si Ollama n'a pas répondu)
