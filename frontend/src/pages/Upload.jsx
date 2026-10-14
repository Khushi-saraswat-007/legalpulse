import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { uploadContracts } from "../api/contracts";
import FileDropzone from "../components/FileDropzone";

// "Acme_MSA_v1.pdf" -> "Acme MSA"  (suggested name when the user has not typed one)
function suggestName(file) {
  if (!file) return "";
  return file.name
    .replace(/\.[^.]+$/, "")
    .replace(/[_-]?(v?\d+|old|new|previous|revised|final)$/i, "")
    .replace(/[_-]+/g, " ")
    .trim();
}

export default function Upload() {
  const [name, setName] = useState("");
  const [oldFile, setOldFile] = useState(null);
  const [newFile, setNewFile] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const handleSubmit = async () => {
    setBusy(true);
    setError(null);
    try {
      const { id } = await uploadContracts(oldFile, newFile, name || suggestName(oldFile));
      navigate(`/report/${id}`);
    } catch {
      setError("Upload failed. Check that both files are valid and try again.");
      setBusy(false);
    }
  };

  return (
    <section>
      <div className="page-head">
        <div>
          <h1>Upload contract versions</h1>
          <p className="muted">Add the earlier version and the revised version to compare them.</p>
        </div>
      </div>
      <label className="name-field">
        Contract name
        <input value={name} onChange={(e) => setName(e.target.value)}
               placeholder={suggestName(oldFile) || "e.g. Acme supply agreement"} maxLength={60} />
      </label>
      <div className="drop-row">
        <FileDropzone label="Previous version" file={oldFile} onFile={setOldFile} />
        <FileDropzone label="New version" file={newFile} onFile={setNewFile} />
      </div>
      {error && <p className="error">{error}</p>}
      <button className="btn btn-primary" disabled={!oldFile || !newFile || busy} onClick={handleSubmit}>
        {busy ? "Analyzing…" : "Analyze contract"}
      </button>
    </section>
  );
}
