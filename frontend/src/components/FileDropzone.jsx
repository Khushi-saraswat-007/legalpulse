import { useRef, useState } from "react";
import { FileUp } from "lucide-react";

const fmtSize = (n) => (n < 1024 * 1024 ? `${Math.max(1, Math.round(n / 1024))} KB` : `${(n / 1024 / 1024).toFixed(1)} MB`);

// Click or drag a file in. Calls onFile(file).
export default function FileDropzone({ label, step, file, onFile }) {
  const inputRef = useRef(null);
  const [over, setOver] = useState(false);

  const handleDrop = (e) => {
    e.preventDefault();
    setOver(false);
    if (e.dataTransfer.files[0]) onFile(e.dataTransfer.files[0]);
  };

  return (
    <div
      className={`dropzone ${over ? "over" : ""} ${file ? "has-file" : ""}`}
      role="button"
      tabIndex={0}
      onClick={() => inputRef.current.click()}
      onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && (e.preventDefault(), inputRef.current.click())}
      onDragOver={(e) => { e.preventDefault(); setOver(true); }}
      onDragLeave={() => setOver(false)}
      onDrop={handleDrop}
    >
      <span className="dz-step">{step}</span>
      <FileUp size={22} aria-hidden="true" />
      <strong>{label}</strong>
      {file ? (
        <span className="dz-file"><span className="mono">{file.name}</span> · {fmtSize(file.size)}</span>
      ) : (
        <span className="muted">Drop a PDF, DOCX or TXT here, or click to browse</span>
      )}
      <input
        ref={inputRef}
        type="file"
        accept=".pdf,.docx,.txt"
        hidden
        onChange={(e) => e.target.files[0] && onFile(e.target.files[0])}
      />
    </div>
  );
}
