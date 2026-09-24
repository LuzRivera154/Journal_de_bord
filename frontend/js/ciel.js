// Page Ciel : historique des observations + nombre d'étoiles détectées
// par photo (Épic 2). La détection se fait toute seule côté serveur juste
// après chaque capture (voir backend/services/scheduler.py), donc cette
// page n'a qu'à afficher le résultat.

function formatDate(iso) {
  return new Date(iso).toLocaleString("fr-FR", { dateStyle: "short", timeStyle: "medium" });
}

function libelleEtoiles(observation) {
  if (observation.statut_analyse !== "reussi" || !observation.etoiles_detectees) {
    return "Analyse en attente";
  }

  const etoiles = JSON.parse(observation.etoiles_detectees);
  if (etoiles.length === 0) {
    return "Aucune étoile détectée";
  }
  return etoiles.length + " étoile" + (etoiles.length > 1 ? "s" : "") + " détectée" + (etoiles.length > 1 ? "s" : "");
}

async function chargerObservations() {
  try {
    const reponse = await fetch("/api/observations/");
    const observations = await reponse.json();
    const liste = document.getElementById("liste-observations");

    if (observations.length === 0) {
      liste.innerHTML = '<li><p class="vide">Aucune observation pour l\'instant.</p></li>';
      return;
    }

    liste.innerHTML = observations.map((observation) => `
      <li class="element-observation">
        <div class="element-observation-tete">
          <span>${formatDate(observation.horodatage)}</span>
          <span class="pastille" data-statut-observation="${observation.statut_analyse}">${observation.statut_analyse}</span>
        </div>
        <p>${libelleEtoiles(observation)}</p>
      </li>
    `).join("");
  } catch (erreur) {
    console.error(erreur);
  }
}

chargerObservations();
setInterval(chargerObservations, 5000);
