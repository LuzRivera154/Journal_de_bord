// Page Assistant : chat en langage naturel sur l'état du vaisseau (US-6.x).
//
// ATTENTION : le backend n'existe pas encore (pas de routers/assistant.py).
// Ce fichier appelle déjà POST /api/assistant/demander avec le contrat des
// schémas AskRequest/AskResponse déjà présents dans backend/schemas.py :
//   requête  { "question": "..." }
//   réponse  { "reponse": "...", "source": "ollama" | "repli" }
// Il ne reste qu'à créer le router côté backend (voir services/journal.py
// pour le même genre d'appel à Ollama, avec repli si ça ne répond pas).
genererBarreLaterale("assistant");
genererEntete();

const zoneMessages = document.getElementById("assistant-messages");
const formulaire = document.getElementById("assistant-formulaire");
const champQuestion = document.getElementById("assistant-question");

function ajouterMessage(texte, role) {
  const bulle = document.createElement("div");
  bulle.className = "assistant-message assistant-message-" + role;
  bulle.textContent = texte;
  zoneMessages.appendChild(bulle);
  zoneMessages.scrollTop = zoneMessages.scrollHeight;
}

async function poserQuestion(question) {
  ajouterMessage(question, "utilisateur");

  const bulleAttente = document.createElement("div");
  bulleAttente.className = "assistant-message assistant-message-bot assistant-message-attente";
  bulleAttente.textContent = "…";
  zoneMessages.appendChild(bulleAttente);
  zoneMessages.scrollTop = zoneMessages.scrollHeight;

  try {
    const reponse = await fetch("/api/assistant/demander", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: question }),
    });
    if (!reponse.ok) throw new Error("HTTP " + reponse.status);

    const donnees = await reponse.json();
    bulleAttente.remove();
    ajouterMessage(donnees.reponse, "bot");
  } catch (erreur) {
    bulleAttente.remove();
    ajouterMessage("Impossible de contacter l'assistant pour le moment.", "bot");
    console.error(erreur);
  }
}

formulaire.addEventListener("submit", (evenement) => {
  evenement.preventDefault();
  const question = champQuestion.value.trim();
  if (!question) return;

  champQuestion.value = "";
  poserQuestion(question);
});

document.getElementById("assistant-suggestions").addEventListener("click", (evenement) => {
  const bouton = evenement.target.closest(".bouton-suggestion");
  if (!bouton) return;
  poserQuestion(bouton.textContent);
});
