// Page Journal : liste des journaux archivés + génération à la demande (US-5.2).
genererBarreLaterale("journal");
genererEntete();

function formatDate(iso) {
  return new Date(iso).toLocaleString("fr-FR", { dateStyle: "full", timeStyle: "short" });
}

// Convertit le texte du journal ("## titre", "- élément", paragraphes) en
// HTML lisible — c'est le format imposé au modèle par la consigne
// (voir backend/services/journal.py).
function formaterTexteJournal(texte) {
  const lignes = texte.split("\n");
  let html = "";
  let dansListe = false;

  lignes.forEach((ligne) => {
    const ligneNettoyee = ligne.trim();

    if (ligneNettoyee.startsWith("## ")) {
      if (dansListe) { html += "</ul>"; dansListe = false; }
      html += "<h3>" + ligneNettoyee.slice(3) + "</h3>";
    } else if (ligneNettoyee.startsWith("- ")) {
      if (!dansListe) { html += "<ul>"; dansListe = true; }
      html += "<li>" + ligneNettoyee.slice(2) + "</li>";
    } else if (ligneNettoyee === "") {
      if (dansListe) { html += "</ul>"; dansListe = false; }
    } else {
      if (dansListe) { html += "</ul>"; dansListe = false; }
      html += "<p>" + ligneNettoyee + "</p>";
    }
  });

  if (dansListe) html += "</ul>";
  return html;
}

function afficherJournal(journal) {
  const article = document.getElementById("journal-article");
  article.innerHTML = `
    <div class="journal-entete">
      <div>
        <h1>${formatDate(journal.date)}</h1>
        <p class="journal-meta">Rédigé par ${journal.modele_utilise}</p>
      </div>
    </div>
    <div class="journal-corps">${formaterTexteJournal(journal.texte_genere)}</div>
    ${journal.notes_manuelles ? '<div class="note-equipage"><span>Note ajoutée</span>' + journal.notes_manuelles + "</div>" : ""}
  `;

  // Marque l'élément actif dans la liste
  document.querySelectorAll(".liste-journaux .element-liste").forEach((el) => {
    el.setAttribute("aria-current", el.dataset.id === String(journal.id) ? "true" : "false");
  });
}

async function chargerJournal(id) {
  try {
    const reponse = await fetch("/api/journal/" + id);
    if (!reponse.ok) return;
    afficherJournal(await reponse.json());
  } catch (erreur) {
    console.error(erreur);
  }
}

function formatDateCourte(iso) {
  return new Date(iso).toLocaleDateString("fr-FR", { day: "2-digit", month: "2-digit", year: "numeric" });
}

// Remplit le menu "Aller à une date" avec les dates qui ont vraiment un
// journal (pas de date au hasard) — une seule fois au chargement de la
// page, indépendamment de la recherche en cours.
async function remplirSelectDates() {
  try {
    const reponse = await fetch("/api/journal/");
    const journaux = await reponse.json();

    // journal.date est en UTC (ex: "2026-09-24T12:32:05...") — on garde
    // juste les 10 premiers caractères pour avoir "AAAA-MM-JJ", pareil que
    // ce que le filtre ?date=... attend côté backend.
    const datesUniques = [...new Set(journaux.map((j) => j.date.slice(0, 10)))].sort().reverse();

    const select = document.getElementById("recherche-date-select");
    datesUniques.forEach((date) => {
      const option = document.createElement("option");
      option.value = date;
      option.textContent = formatDateCourte(date);
      select.appendChild(option);
    });
  } catch (erreur) {
    console.error(erreur);
  }
}

async function chargerListeJournaux(idASelectionner, parametresRecherche) {
  try {
    const requete = new URLSearchParams(parametresRecherche || {});
    const reponse = await fetch("/api/journal/?" + requete.toString());
    const journaux = await reponse.json();
    const liste = document.getElementById("liste-journaux");

    if (journaux.length === 0) {
      const parametres = parametresRecherche || {};
      let message = "Aucun journal pour l'instant.";
      if (parametres.date) {
        message = "Aucun journal disponible ce jour-là.";
      } else if (parametres.du || parametres.au) {
        message = "Aucun journal disponible pour cette période.";
      }

      liste.innerHTML = '<li><p class="vide">' + message + "</p></li>";
      document.getElementById("journal-article").innerHTML = '<p class="vide">' + message + "</p>";
      return;
    }

    liste.innerHTML = journaux.map((j) => `
      <li>
        <button class="element-liste" type="button" data-id="${j.id}">
          <span class="element-titre">${formatDate(j.date)}</span>
          <span class="element-sous">${j.modele_utilise}</span>
        </button>
      </li>
    `).join("");

    document.querySelectorAll(".element-liste").forEach((bouton) => {
      bouton.addEventListener("click", () => chargerJournal(bouton.dataset.id));
    });

    // Affiche celui qu'on vient de générer, sinon le plus récent (premier de la liste).
    chargerJournal(idASelectionner || journaux[0].id);
  } catch (erreur) {
    console.error(erreur);
  }
}

document.getElementById("bouton-generer").addEventListener("click", async () => {
  const bouton = document.getElementById("bouton-generer");
  const message = document.getElementById("message-generation");

  bouton.disabled = true;
  bouton.textContent = "Rédaction en cours… (jusqu'à 2 minutes)";
  message.hidden = true;

  try {
    const reponse = await fetch("/api/journal/generer", { method: "POST" });
    if (!reponse.ok) throw new Error("HTTP " + reponse.status);
    const journal = await reponse.json();
    await chargerListeJournaux(journal.id);
  } catch (erreur) {
    message.textContent = "La génération a échoué. Voir la console pour le détail.";
    message.classList.add("erreur");
    message.hidden = false;
    console.error(erreur);
  } finally {
    bouton.disabled = false;
    bouton.textContent = "Rédiger le journal du jour";
  }
});

// Date exacte : menu déroulant, la liste se met à jour dès qu'on choisit
// une date (pas besoin de bouton) — US-5.4, critère 1.
document.getElementById("recherche-date-select").addEventListener("change", (evenement) => {
  const date = evenement.target.value;
  chargerListeJournaux(undefined, date ? { date: date } : {});
});

// Plage de dates : du/au, avec son propre bouton "Rechercher une plage" —
// US-5.4, critère 2. Les deux recherches sont indépendantes.
document.getElementById("recherche-journal").addEventListener("submit", (evenement) => {
  evenement.preventDefault();

  const du = document.getElementById("recherche-du").value;
  const au = document.getElementById("recherche-au").value;

  const parametres = {};
  if (du) parametres.du = du;
  if (au) parametres.au = au;

  document.getElementById("recherche-date-select").value = ""; // les deux recherches ne se cumulent pas
  chargerListeJournaux(undefined, parametres);
});

document.getElementById("bouton-reinitialiser").addEventListener("click", () => {
  document.getElementById("recherche-journal").reset();
  document.getElementById("recherche-date-select").value = "";
  chargerListeJournaux();
});

remplirSelectDates();
chargerListeJournaux();
