import { useEffect } from "react";
import { useTranslation } from "react-i18next";


export default function LanguageSwitcher() {
  const {
    i18n,
  } = useTranslation();


  const currentLanguage =
    i18n.resolvedLanguage?.startsWith("ar")
      ? "ar"
      : "fr";


  useEffect(() => {
    document.documentElement.lang =
      currentLanguage;

    document.documentElement.dir =
      currentLanguage === "ar"
        ? "rtl"
        : "ltr";
  }, [currentLanguage]);


  const changeLanguage = (language) => {
    i18n.changeLanguage(language);
  };


  return (
    <div
      className="language-switcher"
      role="group"
      aria-label="Choisir la langue"
    >

      <button
        type="button"
        className={
          `language-switcher-option ${
            currentLanguage === "fr"
              ? "active"
              : ""
          }`
        }
        onClick={() =>
          changeLanguage("fr")
        }
      >
        FR
      </button>


      <button
        type="button"
        className={
          `language-switcher-option language-ar ${
            currentLanguage === "ar"
              ? "active"
              : ""
          }`
        }
        onClick={() =>
          changeLanguage("ar")
        }
      >
        العربية
      </button>

    </div>
  );
}