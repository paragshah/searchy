document.addEventListener("DOMContentLoaded", () => {
    const linksBody = document.getElementById("links-body");
    const messageDiv = document.getElementById("message");
    const importModal = document.getElementById("import-modal");
    const importFile = document.getElementById("import-file");
    const importPreview = document.getElementById("import-preview");
    const importSaveBtn = document.getElementById("import-save");
    const importSelectAllBtn = document.getElementById("import-select-all");

    let currentSort = "url";
    let currentOrder = "asc";
    let parsedBookmarks = [];

    function showMessage(text, type) {
        messageDiv.innerHTML = `<div class="message ${type}">${text}</div>`;
        setTimeout(() => { messageDiv.innerHTML = ""; }, 3000);
    }

    async function loadLinks() {
        const resp = await fetch(`/api/links?sort_by=${currentSort}&order=${currentOrder}`);
        const links = await resp.json();
        renderTable(links);
    }

    function renderTable(links) {
        linksBody.innerHTML = links.map(link => `
            <tr data-id="${link.id}">
                <td><input type="text" value="${escapeHtml(link.title)}" data-field="title"></td>
                <td><input type="text" value="${escapeHtml(link.url)}" data-field="url"></td>
                <td><input type="text" value="${escapeHtml(link.description)}" data-field="description" maxlength="256"></td>
                <td><input type="text" value="${escapeHtml(link.tags.join(", "))}" data-field="tags"></td>
                <td class="actions">
                    <button class="save-btn" onclick="saveRow(${link.id})">Save</button>
                    <button class="delete-btn" onclick="deleteRow(${link.id})">Delete</button>
                </td>
            </tr>
        `).join("");
    }

    function escapeHtml(str) {
        const div = document.createElement("div");
        div.textContent = str;
        return div.innerHTML.replace(/"/g, "&quot;");
    }

    // Sort
    document.querySelectorAll("th[data-sort]").forEach(th => {
        th.addEventListener("click", () => {
            const col = th.dataset.sort;
            if (currentSort === col) {
                currentOrder = currentOrder === "asc" ? "desc" : "asc";
            } else {
                currentSort = col;
                currentOrder = "asc";
            }
            // Update header indicators
            document.querySelectorAll("th[data-sort]").forEach(h => {
                h.textContent = h.textContent.replace(/ [▲▼]/, "");
            });
            th.textContent += currentOrder === "asc" ? " ▲" : " ▼";
            loadLinks();
        });
    });

    // Save row
    window.saveRow = async (id) => {
        const row = document.querySelector(`tr[data-id="${id}"]`);
        const title = row.querySelector('[data-field="title"]').value;
        const url = row.querySelector('[data-field="url"]').value;
        const description = row.querySelector('[data-field="description"]').value;
        const tagsStr = row.querySelector('[data-field="tags"]').value;
        const tags = tagsStr.split(",").map(t => t.trim()).filter(Boolean);

        const resp = await fetch(`/api/links/${id}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ title, url, description, tags }),
        });
        if (resp.ok) {
            showMessage("Saved.", "success");
        } else {
            const data = await resp.json();
            showMessage(data.error || "Save failed.", "error");
        }
    };

    // Delete row
    window.deleteRow = async (id) => {
        if (!confirm("Delete this bookmark?")) return;
        const resp = await fetch(`/api/links/${id}`, { method: "DELETE" });
        if (resp.ok) {
            showMessage("Deleted.", "success");
            loadLinks();
        } else {
            showMessage("Delete failed.", "error");
        }
    };

    // Import
    document.getElementById("import-btn").addEventListener("click", () => {
        importModal.classList.add("active");
        importFile.value = "";
        importPreview.style.display = "none";
        importPreview.innerHTML = "";
        importSaveBtn.style.display = "none";
        importSelectAllBtn.style.display = "none";
        parsedBookmarks = [];
    });

    document.getElementById("import-cancel").addEventListener("click", () => {
        importModal.classList.remove("active");
    });

    importModal.addEventListener("click", (e) => {
        if (e.target === importModal) importModal.classList.remove("active");
    });

    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape" && importModal.classList.contains("active")) {
            importModal.classList.remove("active");
        }
    });

    importFile.addEventListener("change", async () => {
        const file = importFile.files[0];
        if (!file) return;

        const formData = new FormData();
        formData.append("file", file);

        const resp = await fetch("/api/import/parse", { method: "POST", body: formData });
        parsedBookmarks = await resp.json();

        if (parsedBookmarks.length === 0) {
            importPreview.innerHTML = "<p>No bookmarks found in file.</p>";
            importPreview.style.display = "block";
            return;
        }

        importPreview.innerHTML = parsedBookmarks.map((bm, i) => `
            <div class="import-item">
                <input type="checkbox" id="bm-${i}" checked>
                <label for="bm-${i}" title="${escapeHtml(bm.url)}">${escapeHtml(bm.title || bm.url)}</label>
            </div>
        `).join("");
        importPreview.style.display = "block";
        importSaveBtn.style.display = "inline-block";
        importSelectAllBtn.style.display = "inline-block";
    });

    importSelectAllBtn.addEventListener("click", () => {
        const checkboxes = importPreview.querySelectorAll('input[type="checkbox"]');
        const allChecked = Array.from(checkboxes).every(cb => cb.checked);
        checkboxes.forEach(cb => { cb.checked = !allChecked; });
        importSelectAllBtn.textContent = allChecked ? "Select All" : "Deselect All";
    });

    importSaveBtn.addEventListener("click", async () => {
        const selected = [];
        parsedBookmarks.forEach((bm, i) => {
            const cb = document.getElementById(`bm-${i}`);
            if (cb && cb.checked) selected.push(bm);
        });

        if (selected.length === 0) {
            showMessage("No bookmarks selected.", "error");
            return;
        }

        const resp = await fetch("/api/import/save", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(selected),
        });
        const data = await resp.json();
        importModal.classList.remove("active");
        showMessage(`Imported ${data.imported} bookmark(s).`, "success");
        loadLinks();
    });

    // Export
    document.getElementById("export-json-btn").addEventListener("click", () => {
        window.location.href = "/api/export?format=json";
    });

    document.getElementById("export-csv-btn").addEventListener("click", () => {
        window.location.href = "/api/export?format=csv";
    });

    // Clear database
    document.getElementById("clear-db-btn").addEventListener("click", async () => {
        if (!confirm("Are you sure you want to delete ALL bookmarks? This cannot be undone.")) return;
        const resp = await fetch("/api/clear", { method: "POST" });
        if (resp.ok) {
            showMessage("Database cleared.", "success");
            loadLinks();
        } else {
            showMessage("Failed to clear database.", "error");
        }
    });

    loadLinks();
});
