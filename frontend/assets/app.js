const API = "http://localhost:5001/api";

let masterTasks = [];

document.addEventListener("DOMContentLoaded", () => {
  attachFilterHandlers();
  attachCreateHandler();
  attachVolunteerHandler();
  fetchImpact();
  fetchTasks();
});

function toast(message, variant = "primary") {
  const toastEl = document.getElementById("toast");
  toastEl.className = `toast align-items-center text-bg-${variant} border-0`;
  document.getElementById("toastBody").textContent = message;
  const t = new bootstrap.Toast(toastEl);
  t.show();
}

function toastSuccess(msg) { toast(msg, "success"); }
function toastError(msg) { toast(msg, "danger"); }

async function fetchImpact() {
  try {
    const res = await fetch(`${API}/impact`);
    if (!res.ok) throw new Error("Failed to load impact");
    const data = await res.json();
    document.getElementById("openCount").textContent = data.openTasks;
    document.getElementById("completedCount").textContent = data.completedToday;
  } catch (e) {
    toastError(e.message);
  }
}

async function fetchTasks() {
  try {
    const res = await fetch(`${API}/tasks`);
    if (!res.ok) throw new Error("Failed to load tasks");
    masterTasks = await res.json();
    renderTasks();
  } catch (e) { toastError(e.message); }
}

function attachFilterHandlers() {
  ["filterCategory", "filterUrgency", "filterSearch"].forEach(id => {
    document.getElementById(id).addEventListener("input", renderTasks);
  });
  const clearBtn = document.getElementById("clearFilters");
  if (clearBtn) {
    clearBtn.addEventListener("click", () => {
      document.getElementById("filterCategory").value = "";
      document.getElementById("filterUrgency").value = "";
      document.getElementById("filterSearch").value = "";
      renderTasks();
    });
  }
}

function getUrgencyBadge(urgency) {
  const map = { Low: "secondary", Medium: "warning", High: "danger" };
  return `<span class="badge text-bg-${map[urgency] || 'secondary'}">${urgency}</span>`;
}

function getStatusBadge(status) {
  const map = { Open: "primary", Claimed: "info", Completed: "success" };
  return `<span class="badge text-bg-${map[status] || 'secondary'}">${status}</span>`;
}

function filteredTasks() {
  const cat = document.getElementById("filterCategory").value.trim();
  const urg = document.getElementById("filterUrgency").value.trim();
  const q = document.getElementById("filterSearch").value.trim().toLowerCase();
  return masterTasks.filter(t => {
    const okCat = !cat || t.category === cat;
    const okUrg = !urg || t.urgency === urg;
    const okQ = !q || (t.title + " " + t.description).toLowerCase().includes(q);
    return okCat && okUrg && okQ;
  });
}

function renderTasks() {
  const grid = document.getElementById("taskGrid");
  grid.innerHTML = "";
  const items = filteredTasks();
  const info = document.getElementById("resultsInfo");
  if (info) info.textContent = `${items.length} task${items.length === 1 ? '' : 's'} shown`;

  if (items.length === 0) {
    grid.innerHTML = `
      <div class="col-12">
        <div class="text-center text-muted py-5 border rounded bg-white">
          <i class="bi bi-emoji-smile" style="font-size:2rem"></i>
          <p class="mt-2 mb-0">No tasks match your filters.</p>
        </div>
      </div>`;
    return;
  }

  items.forEach(task => {
    const card = document.createElement("div");
    card.className = "col";
    card.innerHTML = `
      <div class="card h-100">
        <div class="card-body d-flex flex-column">
          <div class="d-flex justify-content-between align-items-start mb-2">
            <h5 class="card-title me-2">${escapeHtml(task.title)}</h5>
            <div class="text-nowrap">${getUrgencyBadge(task.urgency)} ${getStatusBadge(task.status)}</div>
          </div>
          <p class="card-text">${escapeHtml(task.description)}</p>
          <div class="mt-auto small text-muted">
            <div><i class="bi bi-geo-alt"></i> ${escapeHtml(task.location)}</div>
            <div><i class="bi bi-person"></i> Requester: ${escapeHtml(task.requesterName)}</div>
            ${task.volunteerName ? `<div><i class="bi bi-hand-thumbs-up"></i> Volunteer: ${escapeHtml(task.volunteerName)}</div>` : ""}
          </div>
        </div>
        <div class="card-footer bg-transparent border-0 d-flex justify-content-end gap-2">
          ${task.status === 'Open' ? `<button class="btn btn-sm btn-primary" data-task-id="${task.id}" onclick="openVolunteer(${task.id})"><i class=\"bi bi-heart\"></i> Volunteer</button>` : ''}
          ${task.status === 'Claimed' ? `<button class="btn btn-sm btn-success" onclick="completeTask(${task.id})"><i class=\"bi bi-check2-circle\"></i> Complete</button>` : ''}
        </div>
      </div>`;
    grid.appendChild(card);
  });
}

function attachCreateHandler() {
  document.getElementById("createForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const payload = {
      title: getVal("title"),
      description: getVal("description"),
      category: getVal("category"),
      urgency: getVal("urgency"),
      location: getVal("location"),
      requesterName: getVal("requesterName"),
    };
    try {
      const res = await fetch(`${API}/tasks`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Create failed");
      bootstrap.Modal.getInstance(document.getElementById("createModal")).hide();
      (e.target).reset();
      await refreshAll();
      toastSuccess("Request created");
    } catch (err) { toastError(err.message); }
  });
}

function openVolunteer(taskId) {
  document.getElementById("volunteerTaskId").value = String(taskId);
  document.getElementById("volunteerForm").reset();
  new bootstrap.Modal(document.getElementById("volunteerModal")).show();
}

function attachVolunteerHandler() {
  document.getElementById("volunteerForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const id = document.getElementById("volunteerTaskId").value;
    const payload = {
      volunteerName: getVal("volunteerName"),
      volunteerNote: document.getElementById("volunteerNote").value.trim(),
    };
    try {
      const res = await fetch(`${API}/tasks/${id}/volunteer`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Volunteer failed");
      bootstrap.Modal.getInstance(document.getElementById("volunteerModal")).hide();
      await refreshAll();
      toastSuccess("Task claimed");
    } catch (err) { toastError(err.message); }
  });
}

async function completeTask(id) {
  try {
    const res = await fetch(`${API}/tasks/${id}/complete`, { method: "POST" });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Complete failed");
    await refreshAll();
    toastSuccess("Great work! Task completed");
  } catch (err) { toastError(err.message); }
}

async function refreshAll() {
  await Promise.all([fetchTasks(), fetchImpact()]);
}

function getVal(id) { return document.getElementById(id).value.trim(); }

function escapeHtml(str) {
  return String(str)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}


