"use strict";

const COLS = [
  { id: "todo", name: "Zu erledigen", short: "Offen", c: "var(--faint)" },
  { id: "progress", name: "In Arbeit", short: "Arbeit", c: "var(--accent)" },
  { id: "review", name: "In Prüfung", short: "Prüfen", c: "var(--review)" },
  { id: "done", name: "Erledigt", short: "Fertig", c: "var(--ok)" },
];
const PRIO = { urgent: "Dringend", high: "Hoch", normal: "Normal" };
const PRIO_RANK = { urgent: 0, high: 1, normal: 2 };
const PALETTE = ["#22c55e", "#a855f7", "#ec4899", "#3b82f6", "#f97316", "#14b8a6", "#eab308", "#6366f1"];
const ICON = {
  cal: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><rect x="4" y="5" width="16" height="15" rx="3"/><path d="M4 10h16M9 3v4M15 3v4"/></svg>',
  flag: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><path d="M5 21V4M5 4h11l-2 4 2 4H5"/></svg>',
  tick: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg>',
  mail: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"><rect x="3" y="5" width="18" height="14" rx="3"/><path d="M4 7l8 6 8-6"/></svg>',
  next: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h13M13 6l6 6-6 6"/></svg>',
};
// Roaming settings sind pro Add-in auf 32 KB begrenzt; ab hier warnen.
const SOFT_LIMIT = 26000;
const LS = "aufgaben-board-v1";

const $ = (id) => document.getElementById(id);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const hue = (s) => { let h = 0; for (const ch of String(s)) h = (h * 31 + ch.charCodeAt(0)) >>> 0; return PALETTE[h % PALETTE.length]; };

let tasks = [];
let editing = null;
let draft = null;
let activeCol = "progress";
let inOutlook = false;
let currentMail = null;

/* ---------- Speicher: Outlook-Roaming-Settings, sonst localStorage ---------- */

function compact(t) {
  const o = {};
  for (const [k, v] of Object.entries(t)) if (v !== "" && v !== 0 && v != null) o[k] = v;
  return o;
}
function loadTasks() {
  if (inOutlook) {
    const v = Office.context.roamingSettings.get("tasks");
    return Array.isArray(v) ? v : [];
  }
  try { return JSON.parse(localStorage.getItem(LS) || "[]"); } catch (e) { return []; }
}
function persist() {
  const data = tasks.map(compact);
  const size = JSON.stringify(data).length;
  if (inOutlook) {
    const rs = Office.context.roamingSettings;
    rs.set("tasks", data);
    rs.saveAsync((r) => {
      if (r.status === Office.AsyncResultStatus.Failed) flash("Speichern fehlgeschlagen: " + r.error.message + " Erledigte Aufgaben aufräumen schafft Platz.");
    });
  } else {
    try { localStorage.setItem(LS, JSON.stringify(data)); } catch (e) { flash("Speichern im Browser nicht möglich."); }
  }
  if (size > SOFT_LIMIT) flash(`Speicher fast voll (${Math.round(size / 1024)} von 32 KB). Räume erledigte Aufgaben auf.`);
}
function upsert(t) {
  const i = tasks.findIndex((x) => x.id === t.id);
  if (i >= 0) tasks[i] = t; else tasks.push(t);
  persist(); render();
}
function remove(id) { tasks = tasks.filter((t) => t.id !== id); persist(); render(); }
function flash(m) { $("note").textContent = m; }
function newId() { return Date.now().toString(36) + Math.random().toString(36).slice(2, 5); }

/* ---------- Datum ---------- */

function dayDiff(iso) {
  if (!iso) return null;
  const d = new Date(iso + "T00:00:00"); const t = new Date(); t.setHours(0, 0, 0, 0);
  return Math.round((d - t) / 864e5);
}
function dueLabel(iso) {
  const n = dayDiff(iso); if (n === null) return "";
  if (n === 0) return "Heute"; if (n === 1) return "Morgen"; if (n === -1) return "Gestern";
  const d = new Date(iso + "T00:00:00");
  if (n > 1 && n < 7) return d.toLocaleDateString("de-DE", { weekday: "short" }).replace(".", "");
  return d.toLocaleDateString("de-DE", { day: "numeric", month: "short" });
}
function daysLeftInWeek() { const dow = (new Date().getDay() + 6) % 7; return 6 - dow; }

/* ---------- Darstellung ---------- */

function filtered() {
  const p = $("fProject").value, pr = $("fPrio").value, du = $("fDue").value, q = $("fText").value.trim().toLowerCase();
  const we = daysLeftInWeek();
  return tasks.filter((t) => {
    if (p && (t.project || "Allgemein") !== p) return false;
    if (pr && (t.priority || "normal") !== pr) return false;
    const n = dayDiff(t.due);
    if (du === "today" && n !== 0) return false;
    if (du === "week" && (n === null || n < 0 || n > we)) return false;
    if (du === "late" && !(n !== null && n < 0 && t.status !== "done")) return false;
    if (q && !`${t.title} ${t.project || ""} ${t.who || ""}`.toLowerCase().includes(q)) return false;
    return true;
  }).sort((a, b) => (PRIO_RANK[a.priority] ?? 2) - (PRIO_RANK[b.priority] ?? 2) || (a.due || "9").localeCompare(b.due || "9"));
}

function cardHTML(t) {
  const status = t.status || "todo", done = status === "done";
  const project = t.project || "Allgemein", pc = hue(project);
  const n = dayDiff(t.due);
  const dueCls = done ? "" : n === 0 ? "today" : n !== null && n < 0 ? "late" : "";
  const prio = t.priority && t.priority !== "normal" ? `<span class="tag ${t.priority}">${t.priority === "urgent" ? ICON.flag : ""}${PRIO[t.priority]}</span>` : "";
  const tot = +t.subTotal || 0, sd = Math.min(+t.subDone || 0, tot);
  const prog = tot ? `<div class="prog" style="--c:${pc}"><div class="bar"><i style="width:${(sd / tot) * 100}%"></i></div>${sd}/${tot}</div>` : "";
  const idx = COLS.findIndex((c) => c.id === status);
  const next = COLS[idx + 1];
  return `<div class="card${done ? " done" : ""}" draggable="true" tabindex="0" role="button" data-id="${esc(t.id)}">
    <div class="tags"><span class="tag" style="--c:${pc}"><span class="dot"></span>${esc(project)}</span>${prio}</div>
    <div class="title">${done ? `<span class="check">${ICON.tick}</span>` : ""}<span>${esc(t.title)}</span></div>
    ${prog}
    <div class="meta">
      ${t.due ? `<span class="${dueCls}">${ICON.cal} ${dueLabel(t.due)}</span>` : ""}
      <span class="right">
        ${t.mailId && inOutlook ? `<button class="mini" data-mail="${esc(t.id)}" title="E-Mail öffnen" aria-label="Verknüpfte E-Mail öffnen">${ICON.mail}</button>` : ""}
        ${next ? `<button class="mini" data-next="${esc(t.id)}" title="Nach „${next.name}“ schieben" aria-label="Nach ${next.name} schieben">${ICON.next}</button>` : ""}
        ${t.who ? `<span class="avatar" style="--c:${hue(t.who)}" title="${esc(t.who)}">${esc(t.who.toUpperCase())}</span>` : ""}
      </span>
    </div>
  </div>`;
}

function render() {
  const list = filtered();
  const open = tasks.filter((t) => t.status !== "done");
  const we = daysLeftInWeek();
  $("sOpen").textContent = open.length;
  $("sWeek").textContent = open.filter((t) => { const n = dayDiff(t.due); return n !== null && n >= 0 && n <= we; }).length;
  const late = open.filter((t) => { const n = dayDiff(t.due); return n !== null && n < 0; }).length;
  $("sLate").textContent = late; $("sLateBox").classList.toggle("warn", late > 0);
  $("sDone").textContent = tasks.filter((t) => t.status === "done" && t.doneAt && Date.now() - t.doneAt < 7 * 864e5).length;

  const projects = [...new Set(tasks.map((t) => t.project || "Allgemein"))].sort((a, b) => a.localeCompare(b, "de"));
  $("subline").textContent = `${open.length} offen in ${projects.length} ${projects.length === 1 ? "Projekt" : "Projekten"}`;
  const cur = $("fProject").value;
  $("fProject").innerHTML = '<option value="">Alle Projekte</option>' + projects.map((p) => `<option${p === cur ? " selected" : ""}>${esc(p)}</option>`).join("");
  $("projList").innerHTML = projects.map((p) => `<option value="${esc(p)}">`).join("");
  ["fProject", "fPrio", "fDue"].forEach((id) => $(id).parentElement.classList.toggle("on", !!$(id).value));

  if (currentMail) $("fromMail").textContent = tasks.some((t) => t.mailId === currentMail.id) ? "Aufgabe öffnen" : "Als Aufgabe";

  const byCol = Object.fromEntries(COLS.map((c) => [c.id, list.filter((t) => (t.status || "todo") === c.id)]));
  $("tabs").innerHTML = COLS.map((c) => `<button data-tab="${c.id}" class="${c.id === activeCol ? "on" : ""}" aria-pressed="${c.id === activeCol}"><span class="dot" style="--c:${c.c}"></span><span class="lbl">${c.short}</span><span class="count">${byCol[c.id].length}</span></button>`).join("");
  $("board").innerHTML = COLS.map((c) => {
    const items = byCol[c.id];
    const oldDone = c.id === "done" && tasks.some((t) => t.status === "done" && Date.now() - (t.doneAt || 0) > 14 * 864e5);
    return `<div class="col${c.id === activeCol ? " active" : ""}" data-col="${c.id}">
      <div class="col-h"><span class="dot" style="--c:${c.c}"></span>${c.name}<span class="count">${items.length}</span><button class="add" data-add="${c.id}" aria-label="Aufgabe in ${c.name} anlegen">+</button></div>
      ${items.map(cardHTML).join("") || `<div class="empty">${tasks.length ? "Keine Aufgaben hier" : "Noch leer. Lege mit „Neu“ deine erste Aufgabe an."}</div>`}
      ${oldDone ? `<div class="col-foot"><button data-cleanup>Erledigte älter als 14 Tage entfernen</button></div>` : ""}
    </div>`;
  }).join("");
}

/* ---------- Dialog ---------- */

$("tStatus").innerHTML = COLS.map((c) => `<option value="${c.id}">${c.name}</option>`).join("");

function openDlg(t, preset) {
  editing = t || null;
  draft = preset || {};
  const v = t || draft;
  $("dlgTitle").textContent = t ? "Aufgabe bearbeiten" : "Neue Aufgabe";
  $("tTitle").value = v.title || "";
  $("tProject").value = v.project || $("fProject").value || "";
  $("tWho").value = v.who || "";
  $("tStatus").value = v.status || activeCol || "todo";
  $("tPrio").value = v.priority || "normal";
  $("tDue").value = v.due || "";
  $("tSubDone").value = v.subDone || "";
  $("tSubTotal").value = v.subTotal || "";
  $("tMail").hidden = !v.mailId;
  $("tMail").innerHTML = v.mailId ? `${ICON.mail} Mit einer E-Mail verknüpft` : "";
  $("tDelete").hidden = !t; $("tDelete").classList.remove("armed"); $("tDelete").textContent = "Löschen";
  $("dlg").showModal(); $("tTitle").focus();
}
$("form").addEventListener("submit", (e) => {
  e.preventDefault();
  const title = $("tTitle").value.trim(); if (!title) return;
  const status = $("tStatus").value, prev = editing;
  upsert({
    id: prev?.id || newId(),
    title,
    project: $("tProject").value.trim() || "Allgemein",
    who: $("tWho").value.trim(),
    status,
    priority: $("tPrio").value,
    due: $("tDue").value || "",
    subDone: +$("tSubDone").value || 0,
    subTotal: +$("tSubTotal").value || 0,
    mailId: prev?.mailId || draft?.mailId || "",
    doneAt: status === "done" ? prev?.doneAt || Date.now() : 0,
  });
  activeCol = status; saveUi();
  $("dlg").close(); render();
});
$("tCancel").onclick = () => $("dlg").close();
$("tDelete").onclick = () => {
  const b = $("tDelete");
  if (!b.classList.contains("armed")) { b.classList.add("armed"); b.textContent = "Wirklich löschen?"; return; }
  $("dlg").close(); remove(editing.id);
};
$("newTask").onclick = () => openDlg(null);
$("fromMail").onclick = () => {
  if (!currentMail) return;
  const existing = tasks.find((t) => t.mailId && t.mailId === currentMail.id);
  if (existing) return openDlg(existing);
  openDlg(null, { title: currentMail.subject.slice(0, 140), mailId: currentMail.id, status: "todo" });
};

/* ---------- Board-Interaktion ---------- */

function moveTo(t, s) {
  if (!t || t.status === s) return;
  const u = { ...t, status: s, doneAt: s === "done" ? Date.now() : 0 };
  if (s === "done" && u.subTotal) u.subDone = u.subTotal;
  upsert(u);
}
function openMail(t) {
  try {
    Office.context.mailbox.displayMessageForm(t.mailId);
  } catch (e) {
    flash("Die E-Mail ließ sich nicht öffnen. Wurde sie gelöscht oder verschoben?");
  }
}

$("tabs").addEventListener("click", (e) => {
  const b = e.target.closest("[data-tab]"); if (!b) return;
  activeCol = b.dataset.tab; saveUi(); render();
});
$("board").addEventListener("click", (e) => {
  const byId = (id) => tasks.find((t) => t.id === id);
  const nx = e.target.closest("[data-next]");
  if (nx) { const t = byId(nx.dataset.next); const i = COLS.findIndex((c) => c.id === (t.status || "todo")); return moveTo(t, COLS[i + 1].id); }
  const ml = e.target.closest("[data-mail]");
  if (ml) return openMail(byId(ml.dataset.mail));
  if (e.target.closest("[data-cleanup]")) {
    tasks = tasks.filter((t) => !(t.status === "done" && Date.now() - (t.doneAt || 0) > 14 * 864e5));
    persist(); flash("Alte erledigte Aufgaben entfernt."); return render();
  }
  const add = e.target.closest("[data-add]"); if (add) return openDlg(null, { status: add.dataset.add });
  const c = e.target.closest(".card"); if (c) openDlg(byId(c.dataset.id));
});
$("board").addEventListener("keydown", (e) => {
  if ((e.key === "Enter" || e.key === " ") && e.target.classList.contains("card")) { e.preventDefault(); openDlg(tasks.find((t) => t.id === e.target.dataset.id)); }
});

let dragId = null;
$("board").addEventListener("dragstart", (e) => { const c = e.target.closest(".card"); if (!c) return; dragId = c.dataset.id; c.classList.add("dragging"); e.dataTransfer.effectAllowed = "move"; e.dataTransfer.setData("text/plain", dragId); });
$("board").addEventListener("dragend", () => { dragId = null; document.querySelectorAll(".col.drop,.dragging").forEach((x) => x.classList.remove("drop", "dragging")); });
$("board").addEventListener("dragover", (e) => { const col = e.target.closest(".col"); if (!col || !dragId) return; e.preventDefault(); document.querySelectorAll(".col.drop").forEach((x) => x !== col && x.classList.remove("drop")); col.classList.add("drop"); });
$("board").addEventListener("drop", (e) => { const col = e.target.closest(".col"); if (!col || !dragId) return; e.preventDefault(); moveTo(tasks.find((x) => x.id === dragId), col.dataset.col); });

["fProject", "fPrio", "fDue"].forEach((id) => $(id).addEventListener("change", render));
$("fText").addEventListener("input", render);

function saveUi() { try { localStorage.setItem(LS + "-tab", activeCol); } catch (e) {} }
try { activeCol = localStorage.getItem(LS + "-tab") || activeCol; } catch (e) {}

/* ---------- Outlook ---------- */

function readMail() {
  const item = Office.context.mailbox.item;
  currentMail = item && item.itemId ? { id: item.itemId, subject: item.subject || "(ohne Betreff)" } : null;
  $("mailBox").hidden = !currentMail;
  if (currentMail) $("mailSubject").textContent = currentMail.subject;
}
function applyOfficeTheme() {
  try {
    const bg = Office.context.officeTheme && Office.context.officeTheme.bodyBackgroundColor;
    if (!bg) return;
    const h = bg.replace("#", "");
    const lum = (0.299 * parseInt(h.slice(0, 2), 16) + 0.587 * parseInt(h.slice(2, 4), 16) + 0.114 * parseInt(h.slice(4, 6), 16)) / 255;
    document.documentElement.dataset.theme = lum > 0.5 ? "light" : "dark";
  } catch (e) {}
}

function start() {
  tasks = loadTasks();
  render();
  if (inOutlook) {
    applyOfficeTheme();
    readMail();
    // Angeheftete Seitenleiste: beim Wechsel der E-Mail aktualisieren
    if (Office.context.requirements.isSetSupported("Mailbox", "1.5")) {
      Office.context.mailbox.addHandlerAsync(Office.EventType.ItemChanged, () => { readMail(); render(); });
    }
  } else {
    flash("Außerhalb von Outlook geöffnet: Aufgaben werden nur in diesem Browser gespeichert.");
  }
}

if (window.Office && Office.onReady) {
  Office.onReady((info) => { inOutlook = info.host === Office.HostType.Outlook; start(); });
} else {
  start();
}
