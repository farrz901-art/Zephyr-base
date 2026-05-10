import { useLanguage } from "../../i18n/useLanguage";
import { FileDropZone } from "../FileDropZone";
import { SupportedFormatsNotice } from "../SupportedFormatsNotice";
import { TextInputPanel } from "../TextInputPanel";

interface InputCardProps {
  inputMode: "text" | "file";
  inputPath: string;
  inlineText: string;
  onInputModeChange: (mode: "text" | "file") => void;
  onInputPathChange: (value: string) => void;
  onInlineTextChange: (value: string) => void;
  supportedFormats: string[];
}

export function InputCard({
  inputMode,
  inputPath,
  inlineText,
  onInputModeChange,
  onInputPathChange,
  onInlineTextChange,
  supportedFormats,
}: InputCardProps) {
  const { messages: m } = useLanguage();

  return (
    <section className="panel-card wide-card">
      <div className="section-heading">
        <div>
          <p className="eyebrow">{m.input.title}</p>
          <h2>{m.input.subtitle}</h2>
        </div>
        <div className="tab-row" role="tablist" aria-label="input mode">
          <button
            type="button"
            className={`tab-button ${inputMode === "text" ? "is-selected" : ""}`}
            onClick={() => onInputModeChange("text")}
          >
            {m.input.pasteTab}
          </button>
          <button
            type="button"
            className={`tab-button ${inputMode === "file" ? "is-selected" : ""}`}
            onClick={() => onInputModeChange("file")}
          >
            {m.input.fileTab}
          </button>
        </div>
      </div>
      <p className="panel-copy">{m.input.helper}</p>
      <div className="result-grid">
        {inputMode === "text" ? (
          <TextInputPanel inlineText={inlineText} onInlineTextChange={onInlineTextChange} />
        ) : (
          <FileDropZone
            inputPath={inputPath}
            onInputPathChange={onInputPathChange}
            supportedFormats={supportedFormats}
          />
        )}
        <SupportedFormatsNotice supportedFormats={supportedFormats} />
      </div>
    </section>
  );
}
