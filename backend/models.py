"""Tables de la base de données, une classe par table.

Ça correspond au tableau de la section 8 du cahier des charges.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey

from database import Base


class Secteur(Base):
    __tablename__ = "secteurs"

    id = Column(Integer, primary_key=True)
    nom = Column(String, unique=True)
    description = Column(String, nullable=True)


class Mesure(Base):
    __tablename__ = "mesures"

    id = Column(Integer, primary_key=True)
    horodatage = Column(DateTime, default=datetime.utcnow)
    id_secteur = Column(Integer, ForeignKey("secteurs.id"), nullable=True)
    type = Column(String)  # temperature, humidite, oxygene, niveau_eau...
    valeur = Column(Float)
    unite = Column(String)
    source = Column(String, default="simulee")  # reelle | simulee | nom du projet externe


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True)
    horodatage = Column(DateTime, default=datetime.utcnow)
    id_secteur = Column(Integer, ForeignKey("secteurs.id"), nullable=True)
    gravite = Column(String, default="moyenne")  # faible | moyenne | critique
    description = Column(String)
    statut = Column(String, default="ouvert")  # ouvert | en_cours | resolu


class Maintenance(Base):
    __tablename__ = "maintenance"

    id = Column(Integer, primary_key=True)
    id_secteur = Column(Integer, ForeignKey("secteurs.id"), nullable=True)
    debut = Column(DateTime, default=datetime.utcnow)
    fin_prevue = Column(DateTime, nullable=True)
    motif = Column(String)
    statut = Column(String, default="en_cours")  # en_cours | terminee


class Observation(Base):
    __tablename__ = "observations"

    id = Column(Integer, primary_key=True)
    horodatage = Column(DateTime, default=datetime.utcnow)
    chemin_image = Column(String, nullable=True)
    ascension_droite = Column(Float, nullable=True)
    declinaison = Column(Float, nullable=True)
    constellations_detectees = Column(String, nullable=True)  # liste stockée en JSON (texte)
    etoiles_detectees = Column(String, nullable=True)  # liste de points {x, y, taille} en JSON (texte)
    statut_analyse = Column(String, default="en_attente")  # reussi | echec | en_attente


class Position(Base):
    __tablename__ = "positions"

    id = Column(Integer, primary_key=True)
    date = Column(DateTime, default=datetime.utcnow)
    x = Column(Float)
    y = Column(Float)
    z = Column(Float)
    vitesse = Column(Float)
    incertitude = Column(Float, default=0.0)
    methode = Column(String, default="estime")  # estime | recalage


class Reserve(Base):
    """État actuel des réserves générales (eau, nourriture...), pour le
    panneau "Réserves et besoins" du Bord. Pas dans les 9 tables du cahier
    des charges — une ligne par réserve, mise à jour au fil du temps
    (pas un historique comme Mesure, juste l'état courant)."""
    __tablename__ = "reserves"

    id = Column(Integer, primary_key=True)
    type = Column(String, unique=True)  # eau | nourriture | lioh | azote (voir config.yaml)
    quantite_actuelle = Column(Float)


class Population(Base):
    __tablename__ = "population"

    id = Column(Integer, primary_key=True)
    horodatage = Column(DateTime, default=datetime.utcnow)
    nombre_personnes = Column(Integer)
    source = Column(String, default="simulee")


class Utilisateur(Base):
    __tablename__ = "utilisateurs"

    id = Column(Integer, primary_key=True)
    nom = Column(String, unique=True)
    role = Column(String, default="equipier")  # equipier | commandant | technicien
    id_secteur = Column(Integer, ForeignKey("secteurs.id"), nullable=True)
    identifiants_hash = Column(String, nullable=True)
    date_creation = Column(DateTime, default=datetime.utcnow)


class Crise(Base):
    """Scénario de crise pour la démo (Épic 7) : dépressurisation + perte de
    caméra, déclenché à la main. Pas dans les 9 tables du cahier des
    charges (section 8) — c'est un nouveau besoin, un Incident seul ne
    suffit pas car il n'a pas de date de fin à comparer avec les journaux."""
    __tablename__ = "crises"

    id = Column(Integer, primary_key=True)
    debut = Column(DateTime, default=datetime.utcnow)
    fin = Column(DateTime, nullable=True)
    id_incident = Column(Integer, ForeignKey("incidents.id"), nullable=True)


class Journal(Base):
    __tablename__ = "journaux"

    id = Column(Integer, primary_key=True)
    date = Column(DateTime, default=datetime.utcnow)
    texte_genere = Column(String)
    donnees_sources = Column(String, nullable=True)  # JSON stocké en texte
    modele_utilise = Column(String, default="inconnu")
    notes_manuelles = Column(String, nullable=True)
    id_utilisateur = Column(Integer, ForeignKey("utilisateurs.id"), nullable=True)
