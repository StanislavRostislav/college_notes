// ❤️ лайк без перезагрузки
async function like(id) {
    await fetch(`/like/${id}`, { method: "POST" });
    location.reload();
}

// 💬 комментарий
async function comment(id) {
    const input = document.getElementById(`comment-${id}`);
    const text = input.value;

    if (!text) return;

    await fetch(`/comment/${id}`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: `text=${text}`
    });

    location.reload();
}

// 🔍 поиск
function searchNotes() {
    const input = document.getElementById("search").value.toLowerCase();
    const cards = document.querySelectorAll(".card");

    cards.forEach(card => {
        const text = card.innerText.toLowerCase();
        card.style.display = text.includes(input) ? "block" : "none";
    });
}
