async function like(id) {
    await fetch(`/like/${id}`, { method: "POST" });
    location.reload();
}

function searchNotes() {
    const input = document.getElementById("search");
    if (!input) return;

    const value = input.value.toLowerCase();
    const cards = document.querySelectorAll(".card");

    cards.forEach(card => {
        const text = card.innerText.toLowerCase();
        card.style.display = text.includes(value) ? "" : "none";
    });
}
