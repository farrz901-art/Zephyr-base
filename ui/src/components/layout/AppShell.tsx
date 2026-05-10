import type { ReactNode } from "react";

import { useLanguage } from "../../i18n/useLanguage";
import { LanguageToggle } from "../common/LanguageToggle";

export function AppShell({ children }: { children: ReactNode }) {
  const { messages: m } = useLanguage();

  return (
    <main className="app-shell">
      <header className="top-band">
        <div className="hero-card shell-hero">
          <div className="hero-row">
            <div>
              <p className="eyebrow">{m.header.privacy}</p>
              <h1>{m.app.title}</h1>
              <p className="hero-copy">{m.app.subtitle}</p>
            </div>
            <LanguageToggle />
          </div>
          <div className="top-band-meta">
            <span>{m.app.localOnlyBadge}</span>
            <span>{m.app.portableBadge}</span>
            <span>{m.app.packageBadge}</span>
          </div>
        </div>
      </header>
      {children}
      <footer className="footer-note">{m.app.footer}</footer>
    </main>
  );
}
