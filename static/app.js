function setTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("theme", theme);
}

function toggleTheme() {
    const current = document.documentElement.getAttribute("data-theme") || "dark";
    setTheme(current === "dark" ? "light" : "dark");
}

async function toggleLike(noteId) {
    const btn = document.querySelector(`[data-like-btn="${noteId}"]`);
    const countEl = document.querySelector(`[data-like-count="${noteId}"]`);
    if (!btn || !countEl) return;

    const liked = btn.dataset.liked === "true";
    const url = liked ? `/api/unlike/${noteId}` : `/api/like/${noteId}`;

    const res = await fetch(url, { method: "POST" });

    if (res.status === 401) {
        window.location.href = "/login";
        return;
    }

    const data = await res.json();
    if (!data.ok) return;

    btn.dataset.liked = data.liked ? "true" : "false";
    countEl.textContent = data.likes;

    if (data.liked) {
        btn.innerHTML = `💔 Убрать лайк <span data-like-count="${noteId}">${data.likes}</span>`;
        btn.classList.add("btn-like");
    } else {
        btn.innerHTML = `❤️ <span data-like-count="${noteId}">${data.likes}</span>`;
        btn.classList.add("btn-like");
    }
}

async function submitComment(noteId) {
    const input = document.querySelector(`[data-comment-input="${noteId}"]`);
    const list = document.querySelector(`[data-comment-list="${noteId}"]`);
    if (!input || !list) return;

    const text = input.value.trim();
    if (!text) return;

    const formData = new FormData();
    formData.append("text", text);

    const res = await fetch(`/api/comment/${noteId}`, {
        method: "POST",
        body: formData
    });

    if (res.status === 401) {
        window.location.href = "/login";
        return;
    }

    const data = await res.json();
    if (!data.ok) return;

    input.value = "";
    list.innerHTML = "";

    data.comments.forEach(comment => {
        const div = document.createElement("div");
        div.className = "comment";
        div.textContent = `💬 ${comment.text}`;
        list.appendChild(div);
    });
}

async function toggleFavorite(noteId) {
    const btn = document.querySelector(`[data-favorite-btn="${noteId}"]`);
    if (!btn) return;

    const res = await fetch(`/api/favorite/${noteId}`, { method: "POST" });

    if (res.status === 401) {
        window.location.href = "/login";
        return;
    }

    const data = await res.json();
    if (!data.ok) return;

    btn.dataset.favorited = data.favorited ? "true" : "false";
    btn.textContent = data.favorited ? "⭐ В избранном" : "⭐ Избранное";
}

async function approveNote(noteId) {
    const card = document.querySelector(`[data-note-card="${noteId}"]`);
    const res = await fetch(`/api/approve/${noteId}`, { method: "POST" });

    if (res.status === 403) return;

    const data = await res.json();
    if (!data.ok) return;

    if (card) {
        const badge = card.querySelector(".badge-pending");
        if (badge) {
            badge.textContent = "Одобрено";
            badge.classList.remove("badge-pending");
        }

        const approveBtn = card.querySelector(`[data-approve-btn="${noteId}"]`);
        if (approveBtn) {
            approveBtn.remove();
        }
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const saved = localStorage.getItem("theme") || "dark";
    setTheme(saved);
});
