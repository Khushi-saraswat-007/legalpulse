import client from "./client";
import sampleReport from "./sampleReport.json";

const USE_MOCK = import.meta.env.VITE_USE_MOCK !== "false";

// GET /contracts/{id}/report  (schema: schemas/risk_report.schema.json)
export async function getReport(contractId) {
  if (USE_MOCK) return sampleReport;
  const { data } = await client.get(`/contracts/${contractId}/report`);
  return data;
}

// TODO (backend not ready): GET /contracts
export async function listContracts() {
  if (USE_MOCK) {
    return [{ id: sampleReport.contract_id, name: "Supply Agreement", versions: "v1 → v2" }];
  }
  const { data } = await client.get("/contracts");
  return data;
}

// TODO (backend not ready): POST /contracts/upload (old + new files)
export async function uploadContracts(oldFile, newFile) {
  if (USE_MOCK) return { id: sampleReport.contract_id };
  const form = new FormData();
  form.append("old_file", oldFile);
  form.append("new_file", newFile);
  const { data } = await client.post("/contracts/upload", form);
  return data;
}
