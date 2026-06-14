import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import KpiCard from "../components/KpiCard.jsx";
import MetabaseEmbed from "../components/MetabaseEmbed.jsx";
import { MB } from "../config.js";
import { dashboards } from "../services/api.js";

export default function Dashboard() {
  const { t } = useTranslation();
  const [pdo, setPdo] = useState([]);

  useEffect(() => {
    dashboards
      .indicatorProgress({ type: "PDO" })
      .then((rows) => {
        // keep latest period row per indicator
        const byCode = {};
        for (const r of rows) byCode[r.indicator_code] = r;
        setPdo(Object.values(byCode));
      })
      .catch(() => setPdo([]));
  }, []);

  return (
    <div>
      <h3 className="mb-3">{t("nav.dashboard")}</h3>
      <div className="row g-3 mb-4">
        {pdo.length === 0 && (
          <div className="col-12 text-muted">
            {t("common.empty")} — consolidez des mesures ODP pour alimenter les indicateurs.
          </div>
        )}
        {pdo.map((r) => (
          <div className="col-12 col-md-4" key={r.indicator_code}>
            <KpiCard
              title={`${r.indicator_code} — ${r.indicator_name}`}
              value={r.cumulative_value}
              target={r.target_value}
              rate={r.achievement_rate}
              rag={r.rag_status}
              unit={r.unit}
            />
          </div>
        ))}
      </div>

      <h5 className="mb-2">Résultats physiques</h5>
      <MetabaseEmbed dashboard={MB.RESULTS_PHYSICAL} />
    </div>
  );
}
