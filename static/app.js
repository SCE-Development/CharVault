const ADMIN_KEY_STORAGE = "adminKey";
const INTERVIEWER_NAME_STORAGE = "interviewerName";

function getAdminKey() {
  return window.localStorage.getItem(ADMIN_KEY_STORAGE) || "";
}

function setAdminKey(key) {
  window.localStorage.setItem(ADMIN_KEY_STORAGE, key);
}

function clearAdminKey() {
  window.localStorage.removeItem(ADMIN_KEY_STORAGE);
}

function getInterviewerName() {
  return window.localStorage.getItem(INTERVIEWER_NAME_STORAGE) || "";
}

function setInterviewerName(name) {
  window.localStorage.setItem(INTERVIEWER_NAME_STORAGE, name);
}

async function api(path, options = {}) {
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };
  const resp = await fetch(`api${path}`, { ...options, headers });
  const text = await resp.text();
  const body = text ? JSON.parse(text) : null;
  if (!resp.ok) {
    const msg = (body && body.detail) || resp.statusText;
    const err = new Error(msg);
    err.status = resp.status;
    throw err;
  }
  return body;
}

async function adminApi(path, options = {}) {
  const headers = {
    "X-Admin-Key": getAdminKey(),
    ...(options.headers || {}),
  };
  return api(path, { ...options, headers });
}

function showBanner(el, type, message) {
  el.className = `banner ${type}`;
  el.textContent = message;
  el.hidden = false;
}

function hideBanner(el) {
  el.hidden = true;
}

function formatSlot(iso) {
  const d = new Date(iso);
  return d.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
}

function formatDate(iso) {
  const d = new Date(iso);
  return d.toLocaleDateString([], {
    weekday: "long",
    month: "long",
    day: "numeric",
  });
}

function groupByDay(slots) {
  const groups = {};
  for (const slot of slots) {
    const day = formatDate(slot.start_time);
    if (!groups[day]) groups[day] = [];
    groups[day].push(slot);
  }
  return groups;
}
