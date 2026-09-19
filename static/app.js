const $ = (id) => document.getElementById(id);

async function request(url, options) {
  const response = await fetch(url, options);
  if (!response.ok) throw new Error("Request failed");
  return response.json();
}

function showError() {
  $("attentionText").textContent = "Could not load data. Check the server and refresh.";
  toast("Could not reach the app. Try again.");
}

function escapeHtml(value = "") {
  return String(value).replace(/[&<>"']/g, ch => ({
    "&":"&amp;", "<":"&lt;", ">":"&gt;", '"':"&quot;", "'":"&#039;"
  }[ch]));
}

function daypart() {
  const hour = new Date().getHours();
  return hour < 12 ? "morning" : hour < 18 ? "afternoon" : "evening";
}

function niceTime(value) {
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return d.toLocaleString([], { weekday:"short", hour:"numeric", minute:"2-digit" });
}

function emailCard(email) {
  const reasons = email.reasons?.join(", ") || "";
  return `
    <article class="item">
      <div class="item-top">
        <div>
          <div class="sender">${escapeHtml(email.sender)}</div>
          <h3>${escapeHtml(email.subject)}</h3>
        </div>
        <span class="badge ${email.priority}">${email.priority}</span>
      </div>
      <p>${escapeHtml(email.summary)}</p>
      <div class="reason">${escapeHtml(reasons)} · ${escapeHtml(niceTime(email.received))}</div>
    </article>`;
}

function eventCard(event) {
  return `
    <article class="item">
      <div class="item-top">
        <div>
          <h3>${escapeHtml(event.title)}</h3>
          <div class="sender">${escapeHtml(event.location || "No location")}</div>
        </div>
        <div class="time">${escapeHtml(niceTime(event.start))}</div>
      </div>
    </article>`;
}

function empty(text) {
  return `<div class="empty">${escapeHtml(text)}</div>`;
}

async function loadDashboard() {
  const data = await request("/api/dashboard");

  $("highCount").textContent = data.counts.high;
  $("attentionText").textContent =
    data.counts.high === 0 ? "Nothing urgent right now." :
    data.counts.high === 1 ? "1 message deserves your attention." :
    `${data.counts.high} messages deserve your attention.`;

  $("inboxCount").textContent = `${data.emails.length} messages`;

  const priority = data.emails.filter(x => x.priority !== "low").slice(0, 5);
  $("priorityList").innerHTML = priority.length ? priority.map(emailCard).join("") : empty("No priority messages.");
  $("allEmails").innerHTML = data.emails.length ? data.emails.map(emailCard).join("") : empty("No messages yet.");
  $("todayEvents").innerHTML = data.calendar.length ? data.calendar.slice(0, 3).map(eventCard).join("") : empty("Nothing coming up.");
  $("allEvents").innerHTML = data.calendar.length ? data.calendar.map(eventCard).join("") : empty("No calendar events yet.");
}

async function loadConnections() {
  const data = await request("/api/connections");
  $("connectionList").innerHTML = Object.entries(data).map(([name, info]) => `
    <div class="item connection-row">
      <strong>${escapeHtml(name[0].toUpperCase() + name.slice(1))}</strong>
      <span class="status">${escapeHtml(info.status)}</span>
    </div>`).join("");
}

function toast(message) {
  $("toast").textContent = message;
  $("toast").classList.add("show");
  setTimeout(() => $("toast").classList.remove("show"), 1800);
}

document.querySelectorAll(".tab").forEach(button => {
  button.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach(x => x.classList.remove("active"));
    document.querySelectorAll(".view").forEach(x => x.classList.remove("active"));
    button.classList.add("active");
    $(button.dataset.view).classList.add("active");
  });
});

$("refresh").addEventListener("click", async () => {
  try {
    await loadDashboard();
    toast("Updated");
  } catch { showError(); }
});

$("demoButton").addEventListener("click", async () => {
  try {
    await request("/api/demo/reset", { method: "POST" });
    await loadDashboard();
    toast("Demo data loaded");
  } catch { showError(); }
});

$("daypart").textContent = daypart();

if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("/sw.js").catch(() => {});
}

Promise.all([loadDashboard(), loadConnections()]).catch(showError);
