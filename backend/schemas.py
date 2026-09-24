"""Schémas Pydantic : la forme des données qui entrent/sortent de l'API."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class SecteurOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nom: str
    description: Optional[str]


class SecteurResumeOut(BaseModel):
    """Snapshot d'un secteur pour le panneau "Secteurs" du Bord — pas
    directement une table, construit à partir des dernières mesures."""
    id: int
    nom: str
    oxygene: Optional[float]
    co2: Optional[float]
    temperature: Optional[float]
    humidite: Optional[float]
    pression: Optional[float]
    occupation: Optional[int]
    statut: str  # nominal | maintenance


class ReserveOut(BaseModel):
    """État d'une réserve (eau, nourriture...) pour le panneau "Réserves et
    besoins" du Bord. jours_restants est calculé, pas stocké."""
    type: str
    libelle: str
    quantite_actuelle: float
    quantite_initiale: float
    unite: str
    consommation_par_jour: float
    jours_restants: float


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


class IncidentStatutIn(BaseModel):
    """Pour changer juste le statut d'un incident (boutons "Prendre en
    charge" / "Marquer résolu" de la page Incidents)."""
    statut: str


class IncidentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    horodatage: datetime
    id_secteur: Optional[int]
    gravite: str
    description: str
    statut: str


class CriseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    debut: datetime
    fin: Optional[datetime]
    id_incident: Optional[int]


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


class MaintenanceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    id_secteur: Optional[int]
    debut: datetime
    fin_prevue: Optional[datetime]
    motif: str
    statut: str


class DestinationOut(BaseModel):
    nom: str
    x: float
    y: float
    z: float
    distance_restante: float
    date_arrivee_estimee: Optional[datetime]


class ObservationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    horodatage: datetime
    chemin_image: Optional[str]
    ascension_droite: Optional[float]
    declinaison: Optional[float]
    constellations_detectees: Optional[str]
    etoiles_detectees: Optional[str]
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


class PopulationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    horodatage: datetime
    nombre_personnes: int
    source: str


class PopulationIn(BaseModel):
    nombre_personnes: int


class NoteIn(BaseModel):
    texte: str


class AskRequest(BaseModel):
    question: str


class AskResponse(BaseModel):
    reponse: str
    source: str  # "ollama" ou "repli" (si Ollama n'a pas répondu)
