import { useLanguage } from "../i18n/useLanguage";

interface FileDropZoneProps {
  inputPath: string;
  onInputPathChange: (value: string) => void;
  supportedFormats: string[];
}

export function FileDropZone({ inputPath, onInputPathChange, supportedFormats }: FileDropZoneProps) {
  const { messages: m } = useLanguage();

  return (
    <section className="panel-card nested-card">
      <h3>{m.input.fileTitle}</h3>
      <p className="panel-copy">
        {m.supportedFormats.current}: {supportedFormats.join(", ")}
      </p>
      <label className="field-label" htmlFor="inputPath">
        {m.input.fileLabel}
      </label>
      <input
        id="inputPath"
        className="field-input"
        value={inputPath}
        onChange={(event) => onInputPathChange(event.target.value)}
        placeholder={m.input.filePlaceholder}
      />
      <div className="dropzone-note">{m.input.helper}</div>
    </section>
  );
}
