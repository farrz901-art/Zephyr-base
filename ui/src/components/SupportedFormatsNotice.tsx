interface SupportedFormatsNoticeProps {
  supportedFormats: readonly string[];
}

export function SupportedFormatsNotice({ supportedFormats }: SupportedFormatsNoticeProps) {
  return (
    <section className="panel-card">
      <p className="eyebrow">Supported formats</p>
      <h2>Base first-slice format boundary</h2>
      <p className="panel-copy">
        Current support is intentionally limited to {supportedFormats.join(", ")}.
      </p>
      <p className="toolbar-note">
        `.pdf`, `.docx`, and image-style inputs are not supported in Base first slice. The
        UI does not claim cloud processing, paid upgrade paths, or Pro-only unlocks.
      </p>
    </section>
  );
}
