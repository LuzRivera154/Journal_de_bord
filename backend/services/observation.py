"""Détection des étoiles sur une image capturée (Épic 2).

Cette étape ne fait QUE détecter les points lumineux sur l'image avec
OpenCV — elle ne dit pas de quelle zone du ciel il s'agit (ça, c'est
l'identification par astrometry.net, une autre étape/US, voir la section
"astrometry" de config.yaml). Tourne entièrement en local, aucune
connexion internet nécessaire (NFR "Fonctionnement hors ligne").
"""
import cv2

# Une étoile est un petit point : en dessous, c'est du bruit (grain du
# capteur) ; au-dessus, ce n'est plus un point mais une tache (nuage
# éclairé, reflet...). À ajuster si besoin selon la caméra utilisée.
AIRE_MIN_ETOILE = 1
AIRE_MAX_ETOILE = 200

# Un pixel est considéré "lumineux" (donc peut-être une étoile) au-dessus
# de ce seuil de gris (0 = noir, 255 = blanc).
SEUIL_LUMINOSITE = 200


def detecter_etoiles(chemin_image):
    """Retourne la liste des étoiles détectées sur l'image, sous la forme
    [{"x": ..., "y": ..., "taille": ...}, ...] (coordonnées en pixels).

    Une image introuvable, illisible, ou sans aucune étoile détectable
    (ciel nuageux, mauvaise capture...) retourne juste une liste vide —
    ça ne fait jamais planter le processus (critère 3)."""
    image = cv2.imread(chemin_image, cv2.IMREAD_GRAYSCALE)
    if image is None:
        return []

    # On ne garde que les pixels très lumineux (les étoiles, sur un fond
    # de ciel sombre).
    _, image_seuillee = cv2.threshold(image, SEUIL_LUMINOSITE, 255, cv2.THRESH_BINARY)

    # Puis on regroupe les pixels lumineux voisins en "blobs" : chaque
    # blob de la bonne taille est une étoile.
    contours, _ = cv2.findContours(image_seuillee, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    etoiles = []
    for contour in contours:
        aire = cv2.contourArea(contour)
        if aire < AIRE_MIN_ETOILE or aire > AIRE_MAX_ETOILE:
            continue

        x, y, largeur, hauteur = cv2.boundingRect(contour)
        etoiles.append({
            "x": x + largeur // 2,
            "y": y + hauteur // 2,
            "taille": round(aire, 1),
        })

    return etoiles
