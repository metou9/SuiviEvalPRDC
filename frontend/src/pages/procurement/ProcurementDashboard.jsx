import { useEffect, useState } from "react";
import { Column } from "primereact/column";
import { DataTable } from "primereact/datatable";
import { useTranslation } from "react-i18next";

import MetabaseEmbed from "../../components/MetabaseEmbed.jsx";
import { MB } from "../../config.js";
import { dashboards } from "../../services/api.js";

export default function ProcurementDashboard() {
  const { t } = useTranslation();
  const [rows, setRows] = useState([]);

  useEffect(() => {
    dashboards.procurement({}).then(setRows).catch(() => setRows([]));
  }, []);

  return (
    <div>
      <h3 className="mb-3">{t("nav.procurement_dashboard")}</h3>
      <DataTable value={rows} responsiveLayout="stack" breakpoint="960px" stripedRows emptyMessage={t("common.empty")} className="mb-4">
        <Column field="category_name" header={t("finance.category")} />
        <Column field="method_name" header={t("procurement.method")} />
        <Column field="planned_count" header={t("procurement.planned")} />
        <Column field="completed_count" header={t("procurement.completed")} />
        <Column field="in_progress_count" header={t("procurement.in_progress")} />
        <Column field="realisation_rate_count" header="Taux réal. %" />
      </DataTable>
      <MetabaseEmbed dashboard={MB.PROCUREMENT} />
    </div>
  );
}
