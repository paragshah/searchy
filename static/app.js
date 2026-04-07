document.addEventListener("DOMContentLoaded", () => {
    const searchForm = document.getElementById("search-form");
    const searchInput = document.getElementById("search-input");
    const searchClear = document.getElementById("search-clear");
    const searchMode = document.getElementById("search-mode");
    const resultsDiv = document.getElementById("results");
    const resultsHeader = document.getElementById("results-header");
    const messageDiv = document.getElementById("message");
    const addBtn = document.getElementById("add-btn");
    const historySection = document.getElementById("history-section");
    const historyDiv = document.getElementById("history");

    function showMessage(text, type) {
        messageDiv.innerHTML = `<div class="message ${type}">${text}</div>`;
        setTimeout(() => { messageDiv.innerHTML = ""; }, 3000);
    }

    function renderLink(link) {
        const tags = link.tags.map(t =>
            `<span class="tag" data-tag="${t}">${t}<span class="tag-remove" data-link-id="${link.id}" data-tag="${t}">&times;</span></span>`
        ).join("");

        const meta = [];
        if (link.date_added) meta.push(`added ${link.date_added}`);
        if (link.last_clicked) meta.push(`last clicked ${link.last_clicked}`);

        const desc = link.description
            ? `<div class="link-description">${link.description}</div>`
            : "";

        return `
            <div class="link-item">
                <button class="link-delete-btn" data-id="${link.id}" title="Delete">&times;</button>
                <div class="link-title">
                    <a href="${link.url}" target="_blank" data-id="${link.id}" class="link-click">${link.title || link.url}</a>
                </div>
                ${desc}
                <div class="link-url">${link.url}<span class="link-copy" data-url="${link.url}" title="Copy URL">&#x2398;</span></div>
                <div class="link-tags">${tags}<span class="tag tag-add" data-link-id="${link.id}">+ add</span></div>
                <div class="link-meta">${meta.join(" &middot; ")}</div>
            </div>
        `;
    }

    function renderResults(links) {
        if (links.length === 0) {
            resultsHeader.textContent = "No results found.";
            resultsDiv.innerHTML = "";
            return;
        }
        resultsHeader.textContent = `${links.length} result${links.length !== 1 ? "s" : ""}`;
        resultsDiv.innerHTML = links.map(renderLink).join("");
        attachClickHandlers();
        attachDeleteHandlers();
        attachTagDeleteHandlers();
        attachTagClickHandlers();
        attachAddTagHandlers();
        attachCopyHandlers();
    }

    function attachClickHandlers() {
        document.querySelectorAll(".link-click").forEach(el => {
            el.addEventListener("click", (e) => {
                const id = el.dataset.id;
                fetch(`/api/links/${id}/click`, { method: "POST" });
                loadHistory();
            });
        });
    }

    function attachCopyHandlers() {
        document.querySelectorAll(".link-copy").forEach(el => {
            el.addEventListener("click", async () => {
                try {
                    await navigator.clipboard.writeText(el.dataset.url);
                    el.textContent = "\u2713";
                    setTimeout(() => { el.innerHTML = "&#x2398;"; }, 1500);
                } catch {
                    showMessage("Failed to copy URL.", "error");
                }
            });
        });
    }

    function attachDeleteHandlers() {
        document.querySelectorAll(".link-delete-btn").forEach(el => {
            el.addEventListener("click", async () => {
                if (!confirm("Delete this bookmark?")) return;
                const id = el.dataset.id;
                const resp = await fetch(`/api/links/${id}`, { method: "DELETE" });
                if (resp.ok) {
                    showMessage("Deleted.", "success");
                    doSearch();
                    loadHistory();
                } else {
                    showMessage("Delete failed.", "error");
                }
            });
        });
    }

    function attachTagDeleteHandlers() {
        document.querySelectorAll(".tag-remove").forEach(el => {
            el.addEventListener("click", async (e) => {
                e.stopPropagation();
                const tag = el.dataset.tag;
                const linkId = el.dataset.linkId;
                if (!confirm(`Remove tag "${tag}" from this bookmark?`)) return;
                const linkItem = el.closest(".link-item");
                const currentTags = Array.from(linkItem.querySelectorAll(".tag:not(.tag-add)"))
                    .map(t => t.dataset.tag)
                    .filter(t => t !== tag);
                const resp = await fetch(`/api/links/${linkId}`, {
                    method: "PUT",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ tags: currentTags }),
                });
                if (resp.ok) {
                    showMessage(`Tag "${tag}" removed.`, "success");
                    doSearch();
                } else {
                    showMessage("Failed to remove tag.", "error");
                }
            });
        });
    }

    function attachTagClickHandlers() {
        document.querySelectorAll(".tag:not(.tag-add)").forEach(el => {
            el.addEventListener("click", (e) => {
                if (e.target.classList.contains("tag-remove")) return;
                searchInput.value = el.dataset.tag;
                searchForm.dispatchEvent(new Event("submit"));
            });
        });
    }

    const addTagModal = document.getElementById("add-tag-modal");
    const addTagInput = document.getElementById("add-tag-input");
    const addTagConfirm = document.getElementById("add-tag-confirm");
    const addTagCancel = document.getElementById("add-tag-cancel");
    let addTagLinkId = null;

    function attachAddTagHandlers() {
        document.querySelectorAll(".tag-add").forEach(el => {
            el.addEventListener("click", (e) => {
                e.stopPropagation();
                addTagLinkId = el.dataset.linkId;
                addTagInput.value = "";
                addTagModal.classList.add("active");
                addTagInput.focus();
            });
        });
    }

    addTagCancel.addEventListener("click", () => {
        addTagModal.classList.remove("active");
        addTagLinkId = null;
    });

    addTagModal.addEventListener("click", (e) => {
        if (e.target === addTagModal) {
            addTagModal.classList.remove("active");
            addTagLinkId = null;
        }
    });

    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape" && addTagModal.classList.contains("active")) {
            addTagModal.classList.remove("active");
            addTagLinkId = null;
        }
    });

    addTagInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
            e.preventDefault();
            addTagConfirm.click();
        }
    });

    addTagConfirm.addEventListener("click", async () => {
        const raw = addTagInput.value.trim();
        if (!raw || !addTagLinkId) return;

        const newTags = raw.split(/[,\s]+/).filter(Boolean);
        if (newTags.length === 0) return;

        const linkItem = document.querySelector(`.tag-add[data-link-id="${addTagLinkId}"]`).closest(".link-item");
        const currentTags = Array.from(linkItem.querySelectorAll(".tag:not(.tag-add)"))
            .map(t => t.dataset.tag);
        for (const t of newTags) {
            if (!currentTags.includes(t)) currentTags.push(t);
        }

        const resp = await fetch(`/api/links/${addTagLinkId}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ tags: currentTags }),
        });

        addTagModal.classList.remove("active");

        if (resp.ok) {
            const label = newTags.length === 1 ? `Tag "${newTags[0]}"` : `Tags "${newTags.join('", "')}"`;
            showMessage(`${label} added.`, "success");
            doSearch();
        } else {
            showMessage("Failed to add tags.", "error");
        }
        addTagLinkId = null;
    });

    function updateURL(q, mode, replace) {
        const url = new URL(window.location);
        if (q) {
            url.searchParams.set("q", q);
            if (mode && mode !== "and") {
                url.searchParams.set("mode", mode);
            } else {
                url.searchParams.delete("mode");
            }
        } else {
            url.searchParams.delete("q");
            url.searchParams.delete("mode");
        }
        if (replace) {
            history.replaceState(null, "", url);
        } else {
            history.pushState(null, "", url);
        }
    }

    async function doSearch(options = {}) {
        const q = searchInput.value.trim();
        const mode = searchMode.value;

        if (options.pushHistory) {
            updateURL(q, mode, false);
        }

        if (!q) {
            resultsHeader.textContent = "";
            resultsDiv.innerHTML = "";
            return;
        }
        resultsHeader.textContent = "Searching...";
        const resp = await fetch(`/api/search?q=${encodeURIComponent(q)}&mode=${mode}`);
        const data = await resp.json();
        renderResults(data);
    }

    function updateClearButton() {
        searchClear.style.display = searchInput.value ? "block" : "none";
    }

    searchInput.addEventListener("input", updateClearButton);

    searchClear.addEventListener("click", () => {
        searchInput.value = "";
        updateClearButton();
        searchInput.focus();
        doSearch({ pushHistory: true });
    });

    searchForm.addEventListener("submit", (e) => {
        e.preventDefault();
        doSearch({ pushHistory: true });
    });

    addBtn.addEventListener("click", async () => {
        const url = document.getElementById("add-url").value.trim();
        const title = document.getElementById("add-title").value.trim();
        const description = document.getElementById("add-description").value.trim();
        const tagsStr = document.getElementById("add-tags").value.trim();
        const tags = tagsStr ? tagsStr.split(",").map(t => t.trim()).filter(Boolean) : [];

        if (!url) {
            showMessage("URL is required.", "error");
            return;
        }

        const resp = await fetch("/api/links", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ url, title, description, tags }),
        });
        const data = await resp.json();
        if (resp.ok) {
            showMessage("Bookmark added!", "success");
            document.getElementById("add-url").value = "";
            document.getElementById("add-title").value = "";
            document.getElementById("add-description").value = "";
            document.getElementById("add-tags").value = "";
            if (searchInput.value.trim()) doSearch();
        } else {
            showMessage(data.error || "Failed to add bookmark.", "error");
        }
    });

    async function loadHistory() {
        const resp = await fetch("/api/history");
        const data = await resp.json();
        if (data.length === 0) {
            historySection.style.display = "none";
            return;
        }
        historySection.style.display = "block";
        historyDiv.innerHTML = data.map(link => `
            <div class="history-item">
                <a href="${link.url}" target="_blank">${link.title || link.url}</a>
            </div>
        `).join("");
    }

    window.addEventListener("popstate", () => {
        const params = new URLSearchParams(window.location.search);
        searchInput.value = params.get("q") || "";
        searchMode.value = params.get("mode") || "and";
        updateClearButton();
        doSearch();
    });

    // On page load, populate from URL params and auto-search
    const initParams = new URLSearchParams(window.location.search);
    const initQ = initParams.get("q") || "";
    const initMode = initParams.get("mode") || "and";
    if (initQ) {
        searchInput.value = initQ;
        searchMode.value = initMode;
        updateClearButton();
        doSearch();
    }

    loadHistory();
});
