import { useLanguage } from "../i18n/useLanguage";

interface NormalizedTextPreviewProps {
  preview: string;
}

export function NormalizedTextPreview({ preview }: NormalizedTextPreviewProps) {
  const { messages: m } = useLanguage();

  return (
    <section className="panel-card wide-card nested-card">
      <h3>{m.result.previewTitle}</h3>
      <pre className="preview-surface">{preview || m.result.noPreview}</pre>
    </section>
  );
}
