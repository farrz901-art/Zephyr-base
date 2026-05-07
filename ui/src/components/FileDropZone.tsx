interface FileDropZoneProps {
  inputPath: string;
  onInputPathChange: (value: string) => void;
  supportedFormats: string[];
}

export function FileDropZone({ inputPath, onInputPathChange, supportedFormats }: FileDropZoneProps) {
  return (
    <section className="panel-card">
      <h2>Local file input</h2>
      <p className="panel-copy">Supported first-slice formats: {supportedFormats.join(", ")}</p>
      <label className="field-label" htmlFor="inputPath">
        Local file path
      </label>
      <input
        id="inputPath"
        className="field-input"
        value={inputPath}
        onChange={(event) => onInputPathChange(event.target.value)}
        placeholder="E:/docs/example.md"
      />
      <div className="dropzone-note">Drag and drop UI polish lands later; S7 keeps this as a typed shell.</div>
    </section>
  );
}
