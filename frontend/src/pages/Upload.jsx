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
    } catch (e) {
      const d = e.response?.data?.detail;
      setError(typeof d === "string" ? d : "Upload failed. Check that both files are valid and try again.");
      setBusy(false);
    }
  };

  return (
    <section>
      <div className="page-head">
        <div>
          <p className="crumb">Upload</p>
          <h1>Upload and analyse</h1>
          <p className="muted">Add the earlier version and the revised version. PDF, DOCX and TXT are supported.</p>
        </div>
      </div>

      <div className="panel light upload-panel">
        <label className="name-field">
          <span className="label">Contract name</span>
          <input value={name} onChange={(e) => setName(e.target.value)}
                 placeholder={suggestName(oldFile) || "e.g. Acme supply agreement"} maxLength={60} />
        </label>
        <div className="drop-row">
          <FileDropzone step="1" label="Previous version" file={oldFile} onFile={setOldFile} />
          <FileDropzone step="2" label="New version" file={newFile} onFile={setNewFile} />
        </div>
        {error && <p className="error">{error}</p>}
        <div className="upload-actions">
          <button className="btn btn-primary" disabled={!oldFile || !newFile || busy} onClick={handleSubmit}>
            {busy ? "Analysing…" : "Analyse contract"}
          </button>
          {busy && <span className="muted">This can take a few seconds while the models run.</span>}
        </div>
      </div>
    </section>
  );
}
