const BASE = "/api";

export const STATUSES = [
  { value: "open", label: "Open" },
  { value: "in_progress", label: "In progress" },
  { value: "closed", label: "Closed" },
];

export const PRIORITIES = [
  { value: "low", label: "Low" },
  { value: "medium", label: "Medium" },
  { value: "high", label: "High" },
];

export class ApiError extends Error {
  constructor(status, body) {
    super(describe(status, body));
    this.status = status;
  }
}

// Turns DRF's {"field": ["message"]} error bodies into one readable sentence.
function describe(status, body) {
  if (body && typeof body === "object") {
    const parts = Object.entries(body).map(([field, messages]) => {
      const text = Array.isArray(messages) ? messages.join(" ") : String(messages);
      return field === "non_field_errors" || field === "detail" ? text : `${field}: ${text}`;
    });
    if (parts.length) return parts.join(" ");
  }
  return `Request failed (${status}).`;
}

async function request(path, options = {}) {
  let res;
  try {
    res = await fetch(`${BASE}${path}`, {
      headers: { "Content-Type": "application/json" },
      ...options,
    });
  } catch {
    throw new ApiError(0, { detail: "Can't reach the server. Check your connection and try again." });
  }
  if (!res.ok) {
    let body = null;
    try {
      body = await res.json();
    } catch {
      /* non-JSON error body */
    }
    throw new ApiError(res.status, body);
  }
  return res.json();
}

export function listTickets({ status = "", page = 1, limit = 10 } = {}) {
  const params = new URLSearchParams({ page, limit });
  if (status) params.set("status", status);
  return request(`/tickets?${params}`);
}

export const createTicket = (payload) =>
  request("/tickets", { method: "POST", body: JSON.stringify(payload) });

export const updateTicket = (id, changes) =>
  request(`/tickets/${id}`, { method: "PATCH", body: JSON.stringify(changes) });

export const getStats = () => request("/tickets/stats");
