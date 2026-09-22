// Page Navigation : appelle le backend (voir backend/routers/navigation.py)
// et affiche la position du jour + l'historique.
// La carte du trajet (canvas) est une autre user story (NAV-03), pas encore faite ici.
genererBarreLaterale("navigation");

const API_POSITIONS = "/api/navigation/positions";
const API_CALCULER = "/api/navigation/calculer";

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
