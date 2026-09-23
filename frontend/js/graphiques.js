// Courbes de mesures en SVG, sans bibliothèque externe (le tableau de bord
// doit fonctionner hors ligne — voir NFR "Fonctionnement hors ligne").
// Utilisé par plusieurs pages (Bord pour l'instant), donc fichier partagé.
const NS_SVG = "http://www.w3.org/2000/svg";

function svgEl(nom, attributs = {}, parent = null) {
  const element = document.createElementNS(NS_SVG, nom);
  for (const [cle, valeur] of Object.entries(attributs)) element.setAttribute(cle, valeur);
  if (parent) parent.appendChild(element);
  return element;
}

function couleurCss(variable) {
  return getComputedStyle(document.documentElement).getPropertyValue(variable).trim();
}

function heureCourte(t) {
  return new Date(t).toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" });
}

// Dessine une courbe (mesures dans le temps) dans `conteneur`, avec un
// dégradé sous la ligne et une infobulle au survol.
// `points` : liste d'objets { horodatage, valeur } — le plus ancien en premier.
// `options` : { libelle, unite, decimales, couleur }
function dessinerCourbe(conteneur, points, options) {
  conteneur.innerHTML = "";
  const largeur = conteneur.clientWidth;
  const hauteur = conteneur.clientHeight;
  if (!largeur || !hauteur) return;

  if (points.length < 2) {
    conteneur.innerHTML = '<p class="vide">Pas encore assez de relevés pour tracer une courbe.</p>';
    return;
  }

  const marges = { gauche: 40, droite: 16, haut: 16, bas: 28 };
  const donnees = points.map((p) => ({ t: Date.parse(p.horodatage), v: p.valeur }));
  const valeurs = donnees.map((p) => p.v);
  let min = Math.min(...valeurs);
  let max = Math.max(...valeurs);
  const ecart = (max - min) || Math.abs(max) * 0.02 || 1;
  min -= ecart * 0.2;
  max += ecart * 0.2;

  const t0 = donnees[0].t;
  const t1 = donnees[donnees.length - 1].t;
  const x = (t) => marges.gauche + ((t - t0) / (t1 - t0)) * (largeur - marges.gauche - marges.droite);
  const y = (v) => marges.haut + (1 - (v - min) / (max - min)) * (hauteur - marges.haut - marges.bas);
  const teinte = options.couleur || couleurCss("--accent");

  const svg = svgEl("svg", { viewBox: `0 0 ${largeur} ${hauteur}`, role: "img", "aria-label": options.libelle }, conteneur);

  // Dégradé sous la courbe
  const idDegrade = `degrade-${Math.random().toString(36).slice(2, 8)}`;
  const defs = svgEl("defs", {}, svg);
  const degrade = svgEl("linearGradient", { id: idDegrade, x1: 0, y1: 0, x2: 0, y2: 1 }, defs);
  svgEl("stop", { offset: "0%", "stop-color": teinte, "stop-opacity": 0.28 }, degrade);
  svgEl("stop", { offset: "100%", "stop-color": teinte, "stop-opacity": 0 }, degrade);

  // Graduations verticales (toutes les 6 h)
  const debut = new Date(t0);
  debut.setMinutes(0, 0, 0);
  debut.setHours(Math.ceil(debut.getHours() / 6) * 6);
  for (let t = debut.getTime(); t <= t1; t += 6 * 3600000) {
    if (t < t0) continue;
    svgEl("line", {
      x1: x(t), x2: x(t), y1: marges.haut, y2: hauteur - marges.bas,
      stroke: couleurCss("--trait"), "stroke-width": 1, "stroke-dasharray": "2 4",
    }, svg);
    const etiquette = svgEl("text", {
      x: x(t), y: hauteur - 8, "text-anchor": "middle",
      fill: couleurCss("--texte-discret"), "font-size": 11, "font-family": "IBM Plex Mono, monospace",
    }, svg);
    etiquette.textContent = `${String(new Date(t).getHours()).padStart(2, "0")} h`;
  }

  // Surface (dégradé) + ligne
  const chemin = donnees.map((p, i) => `${i ? "L" : "M"}${x(p.t).toFixed(1)},${y(p.v).toFixed(1)}`).join("");
  svgEl("path", {
    d: `${chemin}L${x(t1).toFixed(1)},${y(min)}L${x(t0).toFixed(1)},${y(min)}Z`,
    fill: `url(#${idDegrade})`,
  }, svg);
  svgEl("path", {
    d: chemin, fill: "none", stroke: teinte, "stroke-width": 2,
    "stroke-linejoin": "round", "stroke-linecap": "round",
  }, svg);

  // Dernier point mis en avant
  const dernier = donnees[donnees.length - 1];
  svgEl("circle", { cx: x(dernier.t), cy: y(dernier.v), r: 4.5, fill: teinte, stroke: couleurCss("--panneau"), "stroke-width": 2 }, svg);

  // Infobulle au survol
  const repere = svgEl("line", {
    y1: marges.haut, y2: hauteur - marges.bas, stroke: couleurCss("--texte-discret"), "stroke-width": 1, visibility: "hidden",
  }, svg);
  const pastilleSurvol = svgEl("circle", {
    r: 4, fill: teinte, stroke: couleurCss("--panneau"), "stroke-width": 2, visibility: "hidden",
  }, svg);
  const bulle = document.createElement("div");
  bulle.className = "infobulle";
  bulle.hidden = true;
  conteneur.appendChild(bulle);

  const zone = svgEl("rect", {
    x: marges.gauche, y: marges.haut,
    width: largeur - marges.gauche - marges.droite, height: hauteur - marges.haut - marges.bas,
    fill: "transparent",
  }, svg);

  const deplacer = (evenement) => {
    const rect = svg.getBoundingClientRect();
    const px = ((evenement.clientX - rect.left) / rect.width) * largeur;
    const t = t0 + ((px - marges.gauche) / (largeur - marges.gauche - marges.droite)) * (t1 - t0);
    let proche = donnees[0];
    for (const p of donnees) if (Math.abs(p.t - t) < Math.abs(proche.t - t)) proche = p;
    repere.setAttribute("x1", x(proche.t));
    repere.setAttribute("x2", x(proche.t));
    pastilleSurvol.setAttribute("cx", x(proche.t));
    pastilleSurvol.setAttribute("cy", y(proche.v));
    repere.setAttribute("visibility", "visible");
    pastilleSurvol.setAttribute("visibility", "visible");
    bulle.hidden = false;
    bulle.textContent = `${heureCourte(proche.t)}  ${proche.v.toFixed(options.decimales ?? 1)} ${options.unite}`;
    bulle.style.left = `${(x(proche.t) / largeur) * 100}%`;
    bulle.style.top = `${(y(proche.v) / hauteur) * 100}%`;
  };
  const masquer = () => {
    repere.setAttribute("visibility", "hidden");
    pastilleSurvol.setAttribute("visibility", "hidden");
    bulle.hidden = true;
  };
  zone.addEventListener("pointermove", deplacer);
  zone.addEventListener("pointerdown", deplacer);
  zone.addEventListener("pointerleave", masquer);
}
