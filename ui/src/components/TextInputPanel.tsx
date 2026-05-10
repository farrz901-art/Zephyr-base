import { useLanguage } from "../i18n/useLanguage";

interface TextInputPanelProps {
  inlineText: string;
  onInlineTextChange: (value: string) => void;
}

export function TextInputPanel({ inlineText, onInlineTextChange }: TextInputPanelProps) {
  const { messages: m } = useLanguage();

  return (
    <section className="panel-card nested-card">
      <h3>{m.input.textTitle}</h3>
      <label className="field-label" htmlFor="inlineText">
        {m.input.textLabel}
      </label>
      <textarea
        id="inlineText"
        className="field-textarea"
        value={inlineText}
        onChange={(event) => onInlineTextChange(event.target.value)}
        placeholder={m.input.textPlaceholder}
        rows={8}
      />
    </section>
  );
}
