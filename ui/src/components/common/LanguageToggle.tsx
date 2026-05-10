import { useLanguage } from "../../i18n/useLanguage";

export function LanguageToggle() {
  const { language, setLanguage, messages: m } = useLanguage();

  return (
    <div className="language-toggle" role="group" aria-label="language switch">
      <button
        type="button"
        className={`ghost-button language-button ${language === "en" ? "is-selected" : ""}`}
        onClick={() => setLanguage("en")}
      >
        {m.common.english}
      </button>
      <button
        type="button"
        className={`ghost-button language-button ${language === "zh" ? "is-selected" : ""}`}
        onClick={() => setLanguage("zh")}
      >
        {m.common.chinese}
      </button>
    </div>
  );
}
