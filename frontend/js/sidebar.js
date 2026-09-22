// Barre latérale commune à toutes les pages.
// Un seul fichier à modifier pour ajouter/renommer une page, plutôt que de
// dupliquer ce HTML dans chaque fichier — évite que tout le monde retouche
// le même bloc à chaque fois.
const PAGES_RAIL = [
  { id: "bord", href: "index.html", label: "Bord",
    icone: '<path d="M3.5 17a8.5 8.5 0 1 1 17 0"/><path d="M12 17l4.5-6"/><path d="M6 17h.01M18 17h.01"/>' },
  { id: "navigation", href: "navigation.html", label: "Navigation",
    icone: '<circle cx="12" cy="12" r="9"/><path d="M15.5 8.5l-2.2 4.8-4.8 2.2 2.2-4.8z"/>' },
  { id: "ciel", href: "ciel.html", label: "Ciel",
    icone: '<path d="M12 3.5l2.1 5.3 5.7.4-4.4 3.6 1.4 5.6L12 15.3l-4.8 3.1 1.4-5.6-4.4-3.6 5.7-.4z"/>' },
  { id: "journal", href: "journal.html", label: "Journal",
    icone: '<path d="M5 4.5h11a3 3 0 0 1 3 3v12H8a3 3 0 0 1-3-3z"/><path d="M5 16.5a3 3 0 0 1 3-3h11M9 8h6"/>' },
  { id: "assistant", href: "assistant.html", label: "Assistant",
    icone: '<path d="M4 5h16v11H10l-5 4v-4H4z"/><path d="M8.5 10.5h.01M12 10.5h.01M15.5 10.5h.01"/>' },
  { id: "incidents", href: "incidents.html", label: "Incidents",
    icone: '<path d="M12 3.5l9.5 16.5h-19z"/><path d="M12 10v4.5M12 17.2v.3"/>' },
];

// Appelée par chaque page avec son propre id (ex: genererBarreLaterale("navigation")).
function genererBarreLaterale(pageActive) {
  const conteneur = document.getElementById("rail");
  if (!conteneur) return;

  const logo = `
    <svg class="rail-logo" viewBox="0 0 32 32" aria-hidden="true">
      <circle cx="16" cy="16" r="14.5"/>
      <path d="M16 27V8M16 14l-6-5M16 14l6-5M16 20l-5-3.5M16 20l5-3.5M11 27h10"/>
    </svg>`;

  const boutons = PAGES_RAIL.map((page) => `
    <a class="rail-bouton" href="${page.href}" ${page.id === pageActive ? 'aria-current="page"' : ""}>
      <svg viewBox="0 0 24 24" aria-hidden="true">${page.icone}</svg>
      <span>${page.label}</span>
    </a>`).join("");

  conteneur.innerHTML = logo + boutons;
}
