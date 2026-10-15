// Small helpers shared by the dashboard, report, changes and graph pages.

export const SEVERITY_ORDER = ["critical", "high", "medium", "low"];

export const SEV_COLOR = { critical: "#e5484d", high: "#e27a3b", medium: "#e0b33a", low: "#4fb98a" };

// soft fill + strong outline for graph nodes
export const SEV_NODE = {
  critical: { bg: "#fbe9ec", border: "#a61e36" },
  high: { bg: "#fdefe3", border: "#b9540b" },
  medium: { bg: "#fbf3d9", border: "#8f6a00" },
  low: { bg: "#e3f4eb", border: "#1f6f4d" },
};

// "Nova-Orbit-Servicesv2_10" -> "C10"   |   "Nova-Orbit-Servicesv1_7" -> "v1 · C7"
export function shortId(id) {
  if (!id) return "—";
  const m = String(id).match(/v([12])_(\d+)$/);
  if (!m) return String(id);
  return m[1] === "2" ? `C${m[2]}` : `v1 · C${m[2]}`;
}

// "Nova-Orbit-Servicesv2" -> "Nova-Orbit-Services"
export function cleanName(contractId = "") {
  return String(contractId).replace(/v[12]$/, "");
}

// The backend appends "(score parts: {...})" to every explanation. Split it into plain text + numbers.
export function parseExplanation(raw = "") {
  const m = raw.match(/\s*\(score parts:\s*(\{.*\})\)\s*$/);
  const text = (m ? raw.slice(0, m.index) : raw).replace(/ -> /g, " → ");
  if (!m) return { text, parts: null };
  const body = m[1];
  const num = (key) => {
    const r = body.match(new RegExp(`'${key}':\\s*([0-9.]+)`));
    return r ? Number(r[1]) : null;
  };
  return {
    text,
    parts: {
      change: num("change_weight"),
      impact: num("impact_breadth"),
      contradiction: /'contradiction':\s*True/.test(body),
    },
  };
}

export function countBySeverity(risks) {
  return SEVERITY_ORDER.map((s) => ({ name: s, value: risks.filter((r) => r.severity === s).length }));
}
