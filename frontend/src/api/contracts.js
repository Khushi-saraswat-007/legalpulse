import client from "./client";
import sampleReport from "./sampleReport.json";

const USE_MOCK = import.meta.env.VITE_USE_MOCK !== "false";

// GET /contracts/{analysis_id}  (saved report)
export async function getReport(analysisId) {
  if (USE_MOCK) return sampleReport;
  const { data } = await client.get(`/contracts/${analysisId}`);
  return data;
}

// GET /contracts  (list of saved analyses)
export async function listContracts() {
  if (USE_MOCK) {
    return [{ id: sampleReport.contract_id, name: "Supply Agreement", versions: "v1 to v2" }];
  }
  const { data } = await client.get("/contracts");
  return data.map((r) => ({
    id: r.id,
    name: r.contract_key,
    versions: `${r.old_filename} to ${r.new_filename}`,
    n_changes: r.n_changes,
    n_risks: r.n_risks,
    top_severity: r.top_severity,
    created_at: r.created_at,
  }));
}

// POST /contracts/analyze  (old + new .txt files)
export async function uploadContracts(oldFile, newFile) {
  if (USE_MOCK) return { id: sampleReport.contract_id };
  const form = new FormData();
  form.append("old_file", oldFile);
  form.append("new_file", newFile);
  const { data } = await client.post("/contracts/analyze", form);
  return { id: data.analysis_id };
}

// GET /contracts/stats  (totals across all of the user's analyses)
export async function getStats() {
  if (USE_MOCK) return { contracts: 1, high_risk: 1, changes: 1, clauses: 3 };
  const { data } = await client.get("/contracts/stats");
  return data;
}