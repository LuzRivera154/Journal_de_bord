document.getElementById("capture-manuelle").addEventListener("click", async () => {
  const message = document.getElementById("message-capture");

  try {
    const response = await fetch("/api/capture/manuelle", {
      method: "POST"
    });

    const resultat = await response.json();

    if (resultat.success) {
      message.textContent = "Capture effectuée avec succès.";
    } else {
      message.textContent = "Échec de la capture.";
    }
  } catch (erreur) {
    message.textContent = "Erreur lors de la capture.";
  }
});
