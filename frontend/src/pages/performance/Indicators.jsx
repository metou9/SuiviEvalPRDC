import { useEffect, useState } from "react";
import { Column } from "primereact/column";
import { DataTable } from "primereact/datatable";
import { TabPanel, TabView } from "primereact/tabview";
import { useTranslation } from "react-i18next";

import RagIndicator from "../../components/RagIndicator.jsx";
import { dashboards } from "../../services/api.js";
import { useList } from "../../services/hooks.js";

const TYPES = [
  { code: "PDO", label: "ODP" },
  { code: "INTERMEDIATE", label: "Intermédiaires" },
  { code: "IMPACT", label: "Impact" },
  { code: "EXECUTION", label: "Exécution" },
];

export default function Indicators() {
  const { t } = useTranslation();
  const indicators = useList("indicators", { page_size: 500 });
  const [progress, setProgress] = useState({});

  useEffect(() => {
    dashboards
      .indicatorProgress({})
      .then((rows) => {
        const byId = {};
        for (const r of rows) byId[r.indicator_id] = r; // latest period wins (ordered)
        setProgress(byId);
      })
      .catch(() => setProgress({}));
  }, []);

  const all = indicators.data?.results || [];

  const targetFor = (ind, code) => {
    const tg = (ind.targets || []).find((x) => x.milestone_code === code);
    return tg ? tg.value : "—";
  };

  return (
    <div>
      <h3 className="mb-3">{t("nav.indicators")}</h3>
      <TabView>
        {TYPES.map((ty) => {
          const rows = all.filter((i) => i.indicator_type_code === ty.code);
          return (
            <TabPanel header={ty.label} key={ty.code}>
              <DataTable value={rows} responsiveLayout="stack" breakpoint="960px" paginator rows={25} stripedRows emptyMessage={t("common.empty")}>
                <Column field="code" header={t("common.code")} sortable />
                <Column field="name" header={t("common.name")} />
                <Column field="unit" header={t("indicators.unit")} />
                <Column header={t("indicators.baseline")} body={(r) => targetFor(r, "BASELINE")} />
                <Column header={t("indicators.midterm")} body={(r) => targetFor(r, "MIDTERM")} />
                <Column header={t("indicators.closing")} body={(r) => targetFor(r, "CLOSING")} />
                <Column header={t("indicators.latest")} body={(r) => progress[r.id]?.cumulative_value ?? "—"} />
                <Column
                  header={t("indicators.achievement")}
                  body={(r) =>
                    progress[r.id] ? (
                      <RagIndicator status={progress[r.id].rag_status} rate={progress[r.id].achievement_rate} />
                    ) : (
                      "—"
                    )
                  }
                />
              </DataTable>
            </TabPanel>
          );
        })}
      </TabView>
    </div>
  );
}
