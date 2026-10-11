export default function Loader({ text = "Loading…" }) {
  return <p className="muted" role="status">{text}</p>;
}
