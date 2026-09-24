// Page Bord : courbe des mesures sur 24h + dernier relevé du DHT22 (STA-01).
// Le vrai tableau de bord complet (autres capteurs, alertes...) est une
// autre user story (US-6.1).
genererBarreLaterale("bord");
genererEntete();

// Ces deux valeurs viennent de config.yaml (dht22.secteur et
// scheduler.dht22_read_interval_minutes) — pas d'endpoint pour les exposer
// pour l'instant, donc dupliquées ici juste pour l'affichage.
document.getElementById("courbe-secteur").textContent = "Pont";
document.getElementById("courbe-intervalle").textContent = "15";

const RAFRAICHISSEMENT_MS = 5000; // se met à jour toutes les 5 secondes

const TYPES_COURBE = {
  temperature: { libelle: "Température", unite: "°C", decimales: 1 },
  humidite: { libelle: "Humidité", unite: "%", decimales: 0 },
  oxygene: { libelle: "Oxygène", unite: "%", decimales: 1 },
};

let typeCourbeActif = "temperature";
let graphique = null; // instance Chart.js : créée une fois, puis mise à jour (pas recréée)

function formatDate(iso) {
  return new Date(iso).toLocaleString("fr-FR", { dateStyle: "short", timeStyle: "medium" });
}

// Dessine ou met à jour la courbe avec Chart.js (chargé depuis js/vendor/,
// pas de CDN — doit marcher hors ligne).
function afficherCourbe(points) {
  const config = TYPES_COURBE[typeCourbeActif];
  const etiquettes = points.map((p) => new Date(p.horodatage).toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" }));
  const valeurs = points.map((p) => p.valeur);

  if (graphique) {
    // Déjà créée : on remplace juste les données, plus fluide qu'une recréation.
    graphique.data.labels = etiquettes;
    graphique.data.datasets[0].label = config.libelle;
    graphique.data.datasets[0].data = valeurs;
    graphique.update();
    return;
  }

  const canvas = document.getElementById("courbe-bord");
  const ctx = canvas.getContext("2d");
  const degrade = ctx.createLinearGradient(0, 0, 0, canvas.height);
  degrade.addColorStop(0, "rgba(143, 179, 255, 0.28)");
  degrade.addColorStop(1, "rgba(143, 179, 255, 0)");

  graphique = new Chart(canvas, {
    type: "line",
    data: {
      labels: etiquettes,
      datasets: [{
        label: config.libelle,
        data: valeurs,
        borderColor: "#8FB3FF",
        backgroundColor: degrade,
        fill: true,
        tension: 0.3,
        pointRadius: 0,
        pointHoverRadius: 4,
        borderWidth: 2,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: { grid: { color: "#22324A" }, ticks: { color: "#8CA0B8", maxTicksLimit: 6 } },
        y: { grid: { color: "#22324A" }, ticks: { color: "#8CA0B8" } },
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: "#1E2C40",
          titleColor: "#DCE5EF",
          bodyColor: "#DCE5EF",
          borderColor: "#22324A",
          borderWidth: 1,
        },
      },
    },
  });
}

// L'oxygène a plusieurs valeurs en même temps (une par secteur) : on les
// regroupe par tanda (même seconde) et on affiche la moyenne de chaque
// tanda, sinon la courbe fait des zigzags entre les secteurs.
function moyenneParTanda(points) {
  const tandas = {}; // clé = horodatage arrondi à la seconde

  points.forEach((p) => {
    const cle = p.horodatage.slice(0, 19); // "2026-09-24T07:34:30" (sans les millisecondes)
    if (!tandas[cle]) tandas[cle] = { horodatage: p.horodatage, total: 0, nombre: 0 };
    tandas[cle].total += p.valeur;
    tandas[cle].nombre += 1;
  });

  return Object.values(tandas).map((tanda) => ({
    horodatage: tanda.horodatage,
    valeur: tanda.total / tanda.nombre,
  }));
}

async function chargerCourbe() {
  try {
    const reponse = await fetch(`/api/stats/mesures?type=${typeCourbeActif}&heures=24`);
    const mesures = await reponse.json();
    // L'API renvoie la plus récente en premier ; la courbe veut l'ordre chronologique.
    let points = [...mesures].reverse();
    if (typeCourbeActif === "oxygene") points = moyenneParTanda(points);
    afficherCourbe(points);
  } catch (erreur) {
    console.error(erreur);
  }
}

document.getElementById("choix-courbe").addEventListener("click", (evenement) => {
  const bouton = evenement.target.closest("button[data-type]");
  if (!bouton) return;

  document.querySelectorAll("#choix-courbe button").forEach((b) => b.setAttribute("aria-pressed", "false"));
  bouton.setAttribute("aria-pressed", "true");
  typeCourbeActif = bouton.dataset.type;
  chargerCourbe();
});

async function chargerDernieresMesuresDht22() {
  try {
    const [reponseTemp, reponseHumidite] = await Promise.all([
      fetch("/api/stats/mesures?type=temperature"),
      fetch("/api/stats/mesures?type=humidite"),
    ]);
    const temperatures = await reponseTemp.json();
    const humidites = await reponseHumidite.json();

    if (temperatures.length === 0 || humidites.length === 0) {
      return; // pas encore de relevé, on laisse "n/d" affiché
    }

    const derniereTemperature = temperatures[0]; // la plus récente est en premier
    const derniereHumidite = humidites[0];

    document.getElementById("dht22-temperature").textContent = `${derniereTemperature.valeur} ${derniereTemperature.unite}`;
    document.getElementById("dht22-humidite").textContent = `${derniereHumidite.valeur} ${derniereHumidite.unite}`;
    document.getElementById("dht22-date").textContent = formatDate(derniereTemperature.horodatage);

    const pastille = document.getElementById("pastille-source-dht22");
    pastille.textContent = derniereTemperature.source;
    pastille.dataset.source = derniereTemperature.source;

    // Les mêmes valeurs alimentent les fiches du haut.
    document.getElementById("fiche-temperature").textContent = derniereTemperature.valeur + " " + derniereTemperature.unite;
    document.getElementById("fiche-temperature-sous").textContent = "capteur DHT22, secteur Pont";
    document.getElementById("fiche-humidite").textContent = derniereHumidite.valeur + " " + derniereHumidite.unite;
    document.getElementById("fiche-humidite-sous").textContent = "capteur DHT22, secteur Pont";
  } catch (erreur) {
    console.error(erreur);
    // Pas de message d'erreur bloquant ici : la page reste utilisable, elle
    // réessaiera au prochain rafraîchissement (cf. NFR "Résilience").
  }
}

// Oxygène : une valeur simulée par secteur, donc on affiche la moyenne de
// la dernière heure plutôt qu'une seule ligne (US-4.2).
async function chargerFicheOxygene() {
  try {
    const reponse = await fetch("/api/stats/mesures?type=oxygene&heures=1");
    const mesures = await reponse.json();

    if (mesures.length === 0) return; // laisse "n/d" affiché

    const somme = mesures.reduce((total, m) => total + m.valeur, 0);
    const moyenne = somme / mesures.length;
    document.getElementById("fiche-oxygene").textContent = moyenne.toFixed(1) + " %";
  } catch (erreur) {
    console.error(erreur);
  }
}

// Effectif à bord (US-4.4).
async function chargerFichePopulation() {
  try {
    const reponse = await fetch("/api/population/");
    if (!reponse.ok) return; // 404 = pas encore de donnée, laisse "n/d" affiché

    const population = await reponse.json();
    document.getElementById("fiche-population").innerHTML = population.nombre_personnes + " <small>à bord</small>";
    document.getElementById("fiche-population-sous").textContent = "source : " + population.source;
  } catch (erreur) {
    console.error(erreur);
  }
}

// Les secteurs changent presque jamais : on les récupère une seule fois,
// pour afficher leur nom à côté de chaque alerte (au lieu du numéro d'id).
let secteursParId = {};

async function chargerSecteurs() {
  try {
    const reponse = await fetch("/api/secteurs");
    const secteurs = await reponse.json();
    secteurs.forEach((s) => { secteursParId[s.id] = s.nom; });
  } catch (erreur) {
    console.error(erreur);
  }
}

// Passe une fiche en rouge (bordure + pastille "Critique") quand sa valeur
// est hors plage — l'info vient des alertes ouvertes, pas d'un seuil
// recalculé ici, pour rester la même source de vérité que le backend
// (services/alertes.py).
function marquerFicheCritique(prefixe, critique) {
  const carte = document.getElementById("fiche-" + prefixe + "-carte");
  const pastille = document.getElementById("fiche-" + prefixe + "-pastille");
  if (!carte || !pastille) return;

  carte.classList.toggle("critique", critique);
  pastille.hidden = !critique;
}

// Alertes en cours = incidents pas encore résolus (US-4.5, critère 2).
// Une crise en cours (Épic 7) passe aussi les fiches en rouge, même sans
// alerte de seuil précise sur cette mesure — la crise concerne tout le
// vaisseau.
async function chargerAlertes() {
  try {
    const [reponseAlertes, reponseCrise] = await Promise.all([
      fetch("/api/incidents/?statut=ouvert"),
      fetch("/api/crise/"),
    ]);
    const alertes = await reponseAlertes.json();
    const criseActive = (await reponseCrise.json()) !== null;

    document.getElementById("compteur-alertes").textContent = alertes.length + " active" + (alertes.length > 1 ? "s" : "");

    marquerFicheCritique("oxygene", criseActive || alertes.some((a) => a.description.startsWith("Oxygène")));
    marquerFicheCritique("temperature", criseActive || alertes.some((a) => a.description.startsWith("Température")));
    marquerFicheCritique("humidite", criseActive || alertes.some((a) => a.description.startsWith("Humidité")));

    const liste = document.getElementById("liste-alertes");
    if (alertes.length === 0) {
      liste.innerHTML = '<p class="vide">Aucune alerte en cours.</p>';
      return;
    }

    liste.innerHTML = alertes.map((alerte) => {
      const nomSecteur = alerte.id_secteur ? (secteursParId[alerte.id_secteur] || "secteur inconnu") : "tout le vaisseau";
      return "<li class=\"alerte\" data-gravite=\"" + alerte.gravite + "\">"
        + "<span class=\"alerte-point\"></span>"
        + "<span class=\"alerte-titre\">" + alerte.description + "</span>"
        + "<span class=\"alerte-texte\">" + nomSecteur + " — " + formatDate(alerte.horodatage) + "</span>"
        + "</li>";
    }).join("");
  } catch (erreur) {
    console.error(erreur);
  }
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

// Juste un extrait sur le Bord (2 premières lignes de contenu, titres "## "
// exclus mais listes "- " gardées comme texte simple — le modèle écrit
// parfois tout en listes, sans aucun paragraphe) — le texte complet se lit
// sur journal.html (bouton "Lire le journal").
async function chargerDernierJournal() {
  try {
    const reponse = await fetch("/api/journal/");
    const journaux = await reponse.json();

    if (journaux.length === 0) return; // laisse le message "Aucun journal..."

    const dernier = journaux[0]; // le plus récent est en premier

    const toutesLesLignes = dernier.texte_genere
      .split("\n")
      .map((ligne) => ligne.trim())
      .filter((ligne) => ligne && !ligne.startsWith("## "))
      .map((ligne) => (ligne.startsWith("- ") ? ligne.slice(2) : ligne));
    const lignes = toutesLesLignes.slice(0, 2);

    let html = lignes.map((l) => "<p>" + l + "</p>").join("");
    if (toutesLesLignes.length > lignes.length) {
      html += '<p class="extrait-suite">…</p>'; // signale qu'il y a plus à lire dans journal.html
    }
    document.getElementById("journal-extrait").innerHTML = html;
    document.getElementById("journal-meta").textContent = "Rédigé le " + formatDate(dernier.date) + " par " + dernier.modele_utilise;
  } catch (erreur) {
    console.error(erreur);
  }
}

// Résumé du trajet (US-3.3/3.4 déjà construites côté Navigation, ici on
// recalcule juste le % parcouru pour l'affichage).
async function chargerTrajet() {
  try {
    const [reponsePositions, reponseDestination] = await Promise.all([
      fetch("/api/navigation/positions"),
      fetch("/api/navigation/destination"),
    ]);
    const positions = await reponsePositions.json();
    const destination = await reponseDestination.json();

    if (positions.length === 0) return;

    const depart = positions[positions.length - 1]; // la liste va du plus récent au plus ancien
    const dx = destination.x - depart.x;
    const dy = destination.y - depart.y;
    const dz = destination.z - depart.z;
    const distanceTotale = Math.sqrt(dx * dx + dy * dy + dz * dz);
    const distanceParcourue = Math.max(0, distanceTotale - destination.distance_restante);
    const pourcentage = distanceTotale > 0 ? (distanceParcourue / distanceTotale) * 100 : 0;

    document.getElementById("trajet-pourcentage").textContent = pourcentage.toFixed(1);
    document.getElementById("trajet-barre").style.width = Math.min(100, Math.max(0, pourcentage)) + "%";
    document.getElementById("trajet-destination-nom").textContent = destination.nom;
    document.getElementById("trajet-parcouru").textContent = distanceParcourue.toFixed(2);
    document.getElementById("trajet-restant").textContent = destination.distance_restante.toFixed(2);
    document.getElementById("trajet-arrivee").textContent = destination.date_arrivee_estimee
      ? new Date(destination.date_arrivee_estimee).toLocaleDateString("fr-FR")
      : "n/d";
  } catch (erreur) {
    console.error(erreur);
  }
}

function rafraichirTout() {
  chargerDernieresMesuresDht22();
  chargerFicheOxygene();
  chargerFichePopulation();
  chargerAlertes();
  chargerCourbe();
  chargerDernierJournal();
  chargerTrajet();
}

chargerSecteurs();
rafraichirTout();
setInterval(rafraichirTout, RAFRAICHISSEMENT_MS);