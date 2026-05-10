import { useLanguage } from "../i18n/useLanguage";

interface SupportedFormatsNoticeProps {
  supportedFormats: readonly string[];
}

export function SupportedFormatsNotice({ supportedFormats }: SupportedFormatsNoticeProps) {
  const { messages: m } = useLanguage();

  return (
    <section className="panel-card nested-card">
      <p className="eyebrow">{m.supportedFormats.title}</p>
      <h3>{m.supportedFormats.subtitle}</h3>
      <p className="panel-copy">
        {m.supportedFormats.current}: {supportedFormats.join(", ")}
      </p>
      <p className="toolbar-note">{m.supportedFormats.unsupported}</p>
    </section>
  );
}
