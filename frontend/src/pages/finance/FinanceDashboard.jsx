import { useEffect, useState } from "react";
import { Column } from "primereact/column";
import { DataTable } from "primereact/datatable";
import { SelectButton } from "primereact/selectbutton";
import { useTranslation } from "react-i18next";

import MetabaseEmbed from "../../components/MetabaseEmbed.jsx";
import { MB } from "../../config.js";
import { dashboards } from "../../services/api.js";

export default function FinanceDashboard() {
  const { t } = useTranslation();
  const [by, setBy] = useState("category");
  const [rows, setRows] = useState([]);

  useEffect(() => {
    dashboards.financial({ by }).then(setRows).catch(() => setRows([]));
  }, [by]);

  return (
    <div>
      <div className="d-flex align-items-center gap-3 mb-3">
        <h3 className="m-0 me-auto">{t("nav.finance_dashboard")}</h3>
        <SelectButton
          value={by}
          onChange={(e) => e.value && setBy(e.value)}
          options={[
            { label: t("finance.category"), value: "category" },
            { label: "Composante", value: "component" },
          ]}
        />
      </div>

      <DataTable value={rows} responsiveLayout="stack" breakpoint="960px" stripedRows emptyMessage={t("common.empty")} className="mb-4">
        <Column header={by === "category" ? t("finance.category") : "Composante"} body={(r) => r.category_name || r.component_name} />
        <Column field="fiscal_year" header={t("finance.fiscal_year")} />
        <Column field="budget_total" header={t("finance.budget")} />
        <Column field="disbursed_cumulative" header={`${t("finance.disbursed")} (cumul)`} />
        <Column field="disbursement_rate" header={`${t("finance.disbursement_rate")} %`} />
        <Column field="realised_cumulative" header={`${t("finance.realised")} (cumul)`} />
        <Column field="financial_realisation_rate" header={`${t("finance.realisation_rate")} %`} />
        <Column field="reliquat_disbursed" header={t("finance.reliquat")} />
      </DataTable>

      <MetabaseEmbed dashboard={by === "category" ? MB.FINANCE_CATEGORY : MB.FINANCE_COMPONENT} />
    </div>
  );
}
