import { useTranslation } from "react-i18next";

import LanguageSwitcher from "../layout/LanguageSwitcher.jsx";
import { useAuth } from "../auth/AuthProvider.jsx";

export default function Profile() {
  const { t } = useTranslation();
  const { me } = useAuth();
  if (!me) return null;
  return (
    <div>
      <h3 className="mb-3">{t("nav.profile")}</h3>
      <p>
        <strong>{me.display_name}</strong> ({me.username})
      </p>
      <div className="mb-3">
        <span className="me-2">{t("common.language")} :</span>
        <LanguageSwitcher />
      </div>
      <h5>{t("indicators.responsibilities")}</h5>
      <ul>
        {(me.roles || []).map((r, i) => (
          <li key={i}>{r.code}</li>
        ))}
      </ul>
      <h6 className="mt-3">Capacités</h6>
      <div style={{ fontSize: "0.8rem", color: "#64748b" }}>{(me.capabilities || []).join(", ")}</div>
    </div>
  );
}
