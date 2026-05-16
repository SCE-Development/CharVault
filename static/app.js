const JWT_KEY = "jwtToken";

function getToken() {
  return window.localStorage.getItem(JWT_KEY);
}

function requireAuth(loginUrl) {
  const token = getToken();
  if (!token) {
    const redirect = encodeURIComponent(window.location.href);
    window.location.href = `${loginUrl}?redirect=${redirect}`;
    return null;
  }
  return token;
}

async function api(path, options = {}) {
  const token = getToken();
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const resp = await fetch(`api${path}`, { ...options, headers });
  const text = await resp.text();
  const body = text ? JSON.parse(text) : null;
  if (!resp.ok) {
    const msg = (body && body.detail) || resp.statusText;
    throw new Error(msg);
  }
  return body;
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
