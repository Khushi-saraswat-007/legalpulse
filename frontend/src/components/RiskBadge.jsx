// severity: "low" | "medium" | "high" | "critical"
export default function RiskBadge({ severity }) {
  return <span className={`badge badge-${severity}`}>{severity}</span>;
}
