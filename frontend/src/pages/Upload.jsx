import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { uploadContracts } from "../api/contracts";
import FileDropzone from "../components/FileDropzone";

export default function Upload() {
  const [oldFile, setOldFile] = useState(null);
  const [newFile, setNewFile] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const handleSubmit = async () => {
    setBusy(true);
    setError(null);
    try {
      const { id } = await uploadContracts(oldFile, newFile);
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
