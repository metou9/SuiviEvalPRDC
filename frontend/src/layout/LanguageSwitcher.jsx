import { Dropdown } from "primereact/dropdown";
import { useTranslation } from "react-i18next";

export default function LanguageSwitcher() {
  const { i18n } = useTranslation();
  const options = [
    { label: "FR", value: "fr" },
    { label: "EN", value: "en" },
  ];
  return (
    <Dropdown
      value={i18n.resolvedLanguage}
      options={options}
      onChange={(e) => i18n.changeLanguage(e.value)}
      className="p-inputtext-sm"
      style={{ width: "5rem" }}
    />
  );
}
