async function like(id) {
    await fetch(`/like/${id}`, { method: "POST" });
    location.reload();
}

async function comment(id) {
    const input = document.getElementById(`comment-${id}`);
    const text = input.value.trim();

    if (!text) return;

    await fetch(`/comment/${id}`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: `text=${encodeURIComponent(text)}`
    });

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
