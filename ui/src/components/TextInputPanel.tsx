interface TextInputPanelProps {
  inlineText: string;
  onInlineTextChange: (value: string) => void;
}

export function TextInputPanel({ inlineText, onInlineTextChange }: TextInputPanelProps) {
  return (
    <section className="panel-card">
      <h2>Local text input</h2>
      <label className="field-label" htmlFor="inlineText">
        Inline text
      </label>
      <textarea
        id="inlineText"
        className="field-textarea"
        value={inlineText}
        onChange={(event) => onInlineTextChange(event.target.value)}
        rows={6}
      />
    </section>
  );
}
