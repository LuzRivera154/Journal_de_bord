// Page Navigation : appelle le backend (voir backend/routers/navigation.py)
// et affiche la position du jour, le trajet et l'historique.
genererBarreLaterale("navigation");
genererEntete();

const API_POSITIONS = "/api/navigation/positions";
const API_CALCULER = "/api/navigation/calculer";
const API_DESTINATION = "/api/navigation/destination";

const elMessage = document.getElementById("message-etat");
const elBoutonCalculer = document.getElementById("bouton-calculer");

function afficherErreur(texte) {
  elMessage.textContent = texte;
  elMessage.classList.add("erreur");
  elMessage.hidden = false;
}

function formatDate(iso) {
  return new Date(iso).toLocaleString("fr-FR", { dateStyle: "short", timeStyle: "short" });
}

function formatNombre(valeur, decimales = 2) {
  return new Intl.NumberFormat("fr-FR", { minimumFractionDigits: decimales, maximumFractionDigits: decimales }).format(valeur);
}

function afficherPositionDuJour(position) {
  document.getElementById("pos-date").textContent = formatDate(position.date);
  document.getElementById("pos-x").textContent = formatNombre(position.x);
  document.getElementById("pos-y").textContent = formatNombre(position.y);
  document.getElementById("pos-z").textContent = formatNombre(position.z);
  document.getElementById("pos-vitesse").textContent = formatNombre(position.vitesse);
  document.getElementById("pos-incertitude").textContent = formatNombre(position.incertitude);

  const pastille = document.getElementById("pastille-methode");
  pastille.textContent = position.methode;
  pastille.dataset.methode = position.methode;
}

// Distance restante et date d'arrivée estimée (US-3.4).
function afficherDestination(destination) {
  document.getElementById("dest-nom").textContent = destination.nom;
  document.getElementById("dest-distance").textContent = formatNombre(destination.distance_restante);
  document.getElementById("dest-arrivee").textContent = destination.date_arrivee_estimee
    ? formatDate(destination.date_arrivee_estimee)
    : "n/d";
}

// Retourne la destination (ou null si l'appel échoue), pour que la carte
// puisse s'en servir en plus du panneau de texte.
async function chargerDestination() {
  try {
    const reponse = await fetch(API_DESTINATION);
    if (!reponse.ok) throw new Error(`HTTP ${reponse.status}`);
    const destination = await reponse.json();
    afficherDestination(destination);
    return destination;
  } catch (erreur) {
    console.error(erreur);
    // Pas grave si ça échoue : le reste de la page (position, trajet) marche quand même.
    return null;
  }
}

function remplirTableau(positions) {
  const corps = document.getElementById("table-positions");
  corps.innerHTML = positions.map((p) => `
    <tr>
      <td>${formatDate(p.date)}</td>
      <td>${formatNombre(p.x)}</td>
      <td>${formatNombre(p.y)}</td>
      <td>${formatNombre(p.z)}</td>
      <td>${formatNombre(p.vitesse)}</td>
      <td>${formatNombre(p.incertitude)}</td>
      <td><span class="pastille" data-methode="${p.methode}">${p.methode}</span></td>
    </tr>`).join("");
}


function dessinerEtiquette(ctx, texte, x, y, largeurCanvas, decalage = 8) {
  const largeurTexte = ctx.measureText(texte).width;
  if (x + decalage + largeurTexte > largeurCanvas - 4) {
    ctx.textAlign = "right";
    ctx.fillText(texte, x - decalage, y - 8);
  } else {
    ctx.textAlign = "left";
    ctx.fillText(texte, x + decalage, y - 8);
  }
}

// Trajet en 2D (plan X/Y) sur un <canvas>, sans bibliothèque externe.
// Relie tous les points historiques entre eux (US-3.3, critère 1) ; cette
// fonction est rappelée à chaque chargement des positions, donc la carte
// reflète toujours la dernière position calculée (critère 2).
//
// `destination` est optionnelle (peut être null si /api/navigation/destination
// n'a pas répondu) : la carte fonctionne quand même, juste sans ce point-là.
function dessinerTrajet(positions, destination) {
  const canvas = document.getElementById("carte");
  const ctx = canvas.getContext("2d");
  const largeur = canvas.width, hauteur = canvas.height;
  ctx.clearRect(0, 0, largeur, hauteur);

  if (positions.length === 0) return;

  // positions arrive du plus récent au plus ancien : on la remet dans l'ordre chronologique
  const trajet = [...positions].reverse();

  const xs = trajet.map((p) => p.x);
  const ys = trajet.map((p) => p.y);
  if (destination) {
    xs.push(destination.x);
    ys.push(destination.y);
  }
  const margeGauche = 24, margeDroite = 24, margeHaut = 20, margeBas = 34;
  const minX = Math.min(...xs, 0), maxX = Math.max(...xs, 0);
  const minY = Math.min(...ys, 0), maxY = Math.max(...ys, 0);
  const etendueX = (maxX - minX) || 1;
  const etendueY = (maxY - minY) || 1;

  const versEcranX = (x) => margeGauche + ((x - minX) / etendueX) * (largeur - margeGauche - margeDroite);
  // Y inversé : en écran le haut est y=0, alors qu'on veut y croissant vers le haut.
  const versEcranY = (y) => hauteur - margeBas - ((y - minY) / etendueY) * (hauteur - margeHaut - margeBas);

  // Grille verticale + graduations sur l'axe X (unités arbitraires du backend)
  const nbGraduations = 5;
  ctx.fillStyle = "#8CA0B8";
  ctx.font = "11px 'IBM Plex Mono', monospace";
  ctx.textAlign = "center";
  for (let i = 0; i <= nbGraduations; i++) {
    const valeur = minX + (etendueX * i) / nbGraduations;
    const x = versEcranX(valeur);
    ctx.strokeStyle = "#22324A";
    ctx.lineWidth = 1;
    ctx.setLineDash([2, 3]);
    ctx.beginPath();
    ctx.moveTo(x, margeHaut);
    ctx.lineTo(x, hauteur - margeBas);
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillText(formatNombre(valeur, 0), x, hauteur - margeBas + 16);
  }

  // Ligne reliant toutes les positions historiques entre elles
  ctx.strokeStyle = "#8FB3FF";
  ctx.lineWidth = 2;
  ctx.beginPath();
  trajet.forEach((p, i) => {
    const x = versEcranX(p.x), y = versEcranY(p.y);
    if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
  });
  ctx.stroke();

  // Départ (point doré façon "soleil", étiqueté)
  const depart = trajet[0];
  const xDepart = versEcranX(depart.x), yDepart = versEcranY(depart.y);
  ctx.fillStyle = "#F5C866";
  ctx.beginPath();
  ctx.arc(xDepart, yDepart, 6, 0, Math.PI * 2);
  ctx.fill();
  ctx.fillStyle = "#DCE5EF";
  ctx.font = "11px 'IBM Plex Sans', sans-serif";
  dessinerEtiquette(ctx, "Départ", xDepart, yDepart, largeur);

  // Position actuelle = position du jour (point accentué avec anneau)
  const actuelle = trajet[trajet.length - 1];
  const xAct = versEcranX(actuelle.x), yAct = versEcranY(actuelle.y);
  ctx.strokeStyle = "#8FB3FF";
  ctx.lineWidth = 1.5;
  ctx.beginPath();
  ctx.arc(xAct, yAct, 9, 0, Math.PI * 2);
  ctx.stroke();
  ctx.fillStyle = "#8FB3FF";
  ctx.beginPath();
  ctx.arc(xAct, yAct, 5, 0, Math.PI * 2);
  ctx.fill();
  ctx.fillStyle = "#8FB3FF";
  ctx.font = "600 11px 'IBM Plex Sans', sans-serif";
  dessinerEtiquette(ctx, "Position actuelle", xAct, yAct, largeur, 13);

  // Destination (point + nom + ligne pointillée = route prévue, pas encore parcourue)
  if (destination) {
    const xDest = versEcranX(destination.x), yDest = versEcranY(destination.y);

    ctx.strokeStyle = "#8CA0B8";
    ctx.lineWidth = 1;
    ctx.setLineDash([4, 4]);
    ctx.beginPath();
    ctx.moveTo(xAct, yAct);
    ctx.lineTo(xDest, yDest);
    ctx.stroke();
    ctx.setLineDash([]);

    ctx.fillStyle = "#F0525A";
    ctx.beginPath();
    ctx.arc(xDest, yDest, 5, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = "#DCE5EF";
    ctx.font = "11px 'IBM Plex Sans', sans-serif";
    dessinerEtiquette(ctx, destination.nom, xDest, yDest, largeur);
  }
}

async function chargerPositions() {
  try {
    const reponse = await fetch(API_POSITIONS);
    if (!reponse.ok) throw new Error(`HTTP ${reponse.status}`);
    const positions = await reponse.json();

    if (positions.length === 0) {
      afficherErreur("Aucune position calculée pour l'instant. Cliquer sur «Calculer la position du jour».");
      return;
    }

    elMessage.hidden = true;
    afficherPositionDuJour(positions[0]); // la plus récente est en premier
    remplirTableau(positions);
    const destination = await chargerDestination();
    dessinerTrajet(positions, destination);
  } catch (erreur) {
    afficherErreur("Impossible de contacter le serveur de bord. Vérifier que le backend tourne (voir README).");
    console.error(erreur);
  }
}

elBoutonCalculer.addEventListener("click", async () => {
  elBoutonCalculer.disabled = true;
  elBoutonCalculer.textContent = "Calcul en cours…";
  try {
    const reponse = await fetch(API_CALCULER, { method: "POST" });
    if (!reponse.ok) throw new Error(`HTTP ${reponse.status}`);
    await chargerPositions();
  } catch (erreur) {
    afficherErreur("Le calcul a échoué. Voir la console pour le détail.");
    console.error(erreur);
  } finally {
    elBoutonCalculer.disabled = false;
    elBoutonCalculer.textContent = "Calculer la position du jour";
  }
});

chargerPositions();
