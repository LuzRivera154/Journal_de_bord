// Page Incidents et maintenance (US-4.3 : déclarer / suivre les incidents ;
// US-4.5 : les incidents ouverts remontent aussi en alertes sur le Bord).
genererBarreLaterale("incidents");
genererEntete();

function formatDate(iso) {
  return new Date(iso).toLocaleString("fr-FR", { day: "2-digit", month: "2-digit", year: "2-digit", hour: "2-digit", minute: "2-digit" });
}

function formatDateCourte(iso) {
  return new Date(iso).toLocaleDateString("fr-FR", { day: "2-digit", month: "2-digit" });
}

function libelleStatut(statut) {
  if (statut === "ouvert") return "ouvert";
  if (statut === "en_cours") return "en cours";
  return "résolu";
}

// Les secteurs changent presque jamais : récupérés une seule fois, pour le
// menu déroulant du formulaire et pour afficher le nom dans le tableau.
let secteursParId = {};

async function chargerSecteurs() {
  try {
    const reponse = await fetch("/api/secteurs");
    const secteurs = await reponse.json();
    secteurs.forEach((s) => { secteursParId[s.id] = s.nom; });

    const select = document.getElementById("champ-secteur");
    secteurs.forEach((s) => {
      const option = document.createElement("option");
      option.value = s.nom;
      option.textContent = s.nom;
      select.appendChild(option);
    });
  } catch (erreur) {
    console.error(erreur);
  }
}

let filtreActif = "non_resolus";

function construireLigneIncident(incident) {
  const reference = "INC-" + String(incident.id).padStart(4, "0");
  const nomSecteur = incident.id_secteur ? (secteursParId[incident.id_secteur] || "secteur inconnu") : "tout le vaisseau";

  let action = "";
  if (incident.statut === "ouvert") {
    action = '<button class="bouton bouton-petit" type="button" data-action="en_cours" data-id="' + incident.id + '">Prendre en charge</button>';
  } else if (incident.statut === "en_cours") {
    action = '<button class="bouton bouton-petit" type="button" data-action="resolu" data-id="' + incident.id + '">Marquer résolu</button>';
  }

  return "<tr>"
    + "<td>" + reference + "</td>"
    + "<td>" + formatDate(incident.horodatage) + "</td>"
    + "<td>" + nomSecteur + "</td>"
    + "<td><span class=\"pastille\" data-gravite=\"" + incident.gravite + "\">" + incident.gravite + "</span></td>"
    + "<td class=\"col-description\">" + incident.description + "</td>"
    + "<td><span class=\"pastille\" data-statut-incident=\"" + incident.statut + "\">" + libelleStatut(incident.statut) + "</span></td>"
    + "<td>" + action + "</td>"
    + "</tr>";
}

async function chargerIncidents() {
  try {
    const reponse = await fetch("/api/incidents/");
    const incidents = await reponse.json();
    const affiches = filtreActif === "tous" ? incidents : incidents.filter((i) => i.statut !== "resolu");

    const corps = document.getElementById("corps-incidents");
    const messageVide = document.getElementById("message-incidents-vide");

    if (affiches.length === 0) {
      corps.innerHTML = "";
      messageVide.hidden = false;
      return;
    }

    messageVide.hidden = true;
    corps.innerHTML = affiches.map(construireLigneIncident).join("");

    corps.querySelectorAll("button[data-action]").forEach((bouton) => {
      bouton.addEventListener("click", () => changerStatutIncident(bouton.dataset.id, bouton.dataset.action));
    });
  } catch (erreur) {
    console.error(erreur);
  }
}

async function changerStatutIncident(id, nouveauStatut) {
  try {
    await fetch("/api/incidents/" + id, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ statut: nouveauStatut }),
    });
    chargerIncidents();
  } catch (erreur) {
    console.error(erreur);
  }
}

document.getElementById("filtre-incidents").addEventListener("click", (evenement) => {
  const bouton = evenement.target.closest("button[data-filtre]");
  if (!bouton) return;

  filtreActif = bouton.dataset.filtre;
  document.querySelectorAll("#filtre-incidents button").forEach((b) => b.setAttribute("aria-pressed", b === bouton ? "true" : "false"));
  chargerIncidents();
});

document.getElementById("formulaire-incident").addEventListener("submit", async (evenement) => {
  evenement.preventDefault();

  const message = document.getElementById("message-incident");
  const secteur = document.getElementById("champ-secteur").value;
  const gravite = document.getElementById("champ-gravite").value;
  const description = document.getElementById("champ-description").value;

  try {
    const reponse = await fetch("/api/incidents/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ secteur: secteur || null, gravite: gravite, description: description, statut: "ouvert" }),
    });
    if (!reponse.ok) throw new Error("HTTP " + reponse.status);

    document.getElementById("formulaire-incident").reset();
    message.textContent = "Incident déclaré.";
    message.classList.remove("erreur");
    message.hidden = false;
    chargerIncidents();
  } catch (erreur) {
    message.textContent = "La déclaration a échoué. Voir la console pour le détail.";
    message.classList.add("erreur");
    message.hidden = false;
    console.error(erreur);
  }
});

async function chargerMaintenance() {
  try {
    const reponse = await fetch("/api/stats/maintenance");
    const maintenances = await reponse.json();
    const liste = document.getElementById("liste-maintenance");

    if (maintenances.length === 0) {
      liste.innerHTML = '<li><p class="vide">Aucune maintenance en cours.</p></li>';
      return;
    }

    liste.innerHTML = maintenances.map((m) => {
      const nomSecteur = m.id_secteur ? (secteursParId[m.id_secteur] || "secteur inconnu") : "tout le vaisseau";
      const periode = formatDateCourte(m.debut) + (m.fin_prevue ? " au " + formatDateCourte(m.fin_prevue) : "");
      return "<li class=\"element-maintenance\">"
        + "<div class=\"element-maintenance-tete\">"
        + "<strong>" + nomSecteur + "</strong>"
        + "<span class=\"pastille\" data-statut-maintenance=\"" + m.statut + "\">" + (m.statut === "en_cours" ? "en cours" : "terminée") + "</span>"
        + "</div>"
        + "<p>" + m.motif + "</p>"
        + "<p class=\"note\">MNT-" + String(m.id).padStart(3, "0") + ", " + periode + "</p>"
        + "</li>";
    }).join("");
  } catch (erreur) {
    console.error(erreur);
  }
}

async function rafraichirTout() {
  await chargerSecteurs();
  chargerIncidents();
  chargerMaintenance();
}

const RAFRAICHISSEMENT_MS = 5000;
rafraichirTout();
setInterval(() => { chargerIncidents(); chargerMaintenance(); }, RAFRAICHISSEMENT_MS);
