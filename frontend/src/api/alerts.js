import client from "./client";

const USE_MOCK = import.meta.env.VITE_USE_MOCK !== "false";

// GET /alerts  (unseen first)
export async function listAlerts() {
  if (USE_MOCK) return [];
  const { data } = await client.get("/alerts");
  return data;
}

// POST /alerts/{id}/seen
export async function markAlertSeen(id) {
  if (USE_MOCK) return { id, seen: true };
  const { data } = await client.post(`/alerts/${id}/seen`);
  return data;
}