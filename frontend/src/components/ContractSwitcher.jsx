import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { listContracts } from "../api/contracts";

// Dropdown to jump to another analysed contract while staying on the same kind of page.
// `to(id)` builds the destination path, e.g. (id) => `/graph/${id}`.
export default function ContractSwitcher({ current, to }) {
  const [contracts, setContracts] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    listContracts().then(setContracts).catch(() => {});
  }, []);

  if (contracts.length < 2) return null;

  return (
    <label className="switcher">
      Contract
      <select value={String(current)} onChange={(e) => navigate(to(e.target.value))} aria-label="Choose another contract">
        {contracts.map((c) => (
          <option key={c.id} value={String(c.id)}>{c.name}{c.versions ? ` · ${c.versions}` : ""}</option>
        ))}
      </select>
    </label>
  );
}
