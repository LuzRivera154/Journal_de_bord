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
};

let typeCourbeActif = "temperature";

function formatDate(iso) {
  return new Date(iso).toLocaleString("fr-FR", { dateStyle: "short", timeStyle: "medium" });
}

async function chargerCourbe() {
  const conteneur = document.getElementById("courbe-bord");
  try {
    const reponse = await fetch(`/api/stats/mesures?type=${typeCourbeActif}&heures=24`);
    const mesures = await reponse.json();
    // L'API renvoie la plus récente en premier ; la courbe veut l'ordre chronologique.
    const points = [...mesures].reverse();
    dessinerCourbe(conteneur, points, TYPES_COURBE[typeCourbeActif]);
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
  } catch (erreur) {
    console.error(erreur);
    // Pas de message d'erreur bloquant ici : la page reste utilisable, elle
    // réessaiera au prochain rafraîchissement (cf. NFR "Résilience").
  }
}

function rafraichirTout() {
  chargerDernieresMesuresDht22();
  chargerCourbe();
}

rafraichirTout();
setInterval(rafraichirTout, RAFRAICHISSEMENT_MS);
