interface NormalizedTextPreviewProps {
  preview: string;
}

export function NormalizedTextPreview({ preview }: NormalizedTextPreviewProps) {
  return (
    <section className="panel-card wide-card">
      <h2>Normalized text preview</h2>
      <pre className="preview-surface">{preview || "No normalized preview available."}</pre>
    </section>
  );
}
