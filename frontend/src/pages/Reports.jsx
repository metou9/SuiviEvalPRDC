import { useState } from "react";
import { Button } from "primereact/button";
import { Column } from "primereact/column";
import { DataTable } from "primereact/datatable";
import { Dropdown } from "primereact/dropdown";
import { InputNumber } from "primereact/inputnumber";
import { InputText } from "primereact/inputtext";
import { useTranslation } from "react-i18next";

import { useAuth } from "../auth/AuthProvider.jsx";
import { api } from "../services/api.js";
import { useList, useSave } from "../services/hooks.js";

export default function Reports() {
  const { t } = useTranslation();
  const { hasCapability } = useAuth();
  const canGenerate = hasCapability("report.generate");
  const templates = useList("reportTemplates", { page_size: 50 });
  const { data, refetch } = useList("reports", { page_size: 50 });
  const save = useSave("reports");
  const rows = data?.results || [];
  const tplOpts = (templates.data?.results || []).map((x) => ({ label: x.name, value: x.id }));

  const [form, setForm] = useState({ template: null, period_year: new Date().getFullYear(), period_quarter: null, title: "" });
  const [busy, setBusy] = useState(false);

  const generate = async () => {
    setBusy(true);
    try {
      await save.mutateAsync({ body: form });
      refetch();
    } finally {
      setBusy(false);
    }
  };

  const download = (row) => {
    window.open(`${import.meta.env.VITE_API_BASE_URL || "/api/v1"}/reports/${row.id}/download/`, "_blank");
  };

  return (
    <div>
      <h3 className="mb-3">{t("nav.reports")}</h3>
      {canGenerate && (
        <div className="row g-2 align-items-end mb-4">
          <div className="col-12 col-md-3">
            <label className="form-label">{t("reports.template")}</label>
            <Dropdown className="w-100" value={form.template} options={tplOpts} onChange={(e) => setForm((f) => ({ ...f, template: e.value }))} />
          </div>
          <div className="col-6 col-md-2">
            <label className="form-label">{t("common.year")}</label>
            <InputNumber className="w-100" value={form.period_year} onValueChange={(e) => setForm((f) => ({ ...f, period_year: e.value }))} useGrouping={false} />
          </div>
          <div className="col-6 col-md-2">
            <label className="form-label">{t("common.quarter")}</label>
            <Dropdown className="w-100" value={form.period_quarter} options={[1, 2, 3, 4].map((q) => ({ label: "T" + q, value: q }))} onChange={(e) => setForm((f) => ({ ...f, period_quarter: e.value }))} showClear />
          </div>
          <div className="col-12 col-md-3">
            <label className="form-label">{t("reports.title")}</label>
            <InputText className="w-100" value={form.title} onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))} />
          </div>
          <div className="col-12 col-md-2">
            <Button label={t("reports.generate")} icon="pi pi-cog" loading={busy} disabled={!form.template} onClick={generate} className="w-100" />
          </div>
        </div>
      )}

      <DataTable value={rows} responsiveLayout="stack" breakpoint="960px" stripedRows emptyMessage={t("common.empty")}>
        <Column field="title" header={t("reports.title")} />
        <Column field="period_year" header={t("common.year")} />
        <Column field="period_quarter" header={t("common.quarter")} />
        <Column field="status" header={t("common.status")} />
        <Column header={t("common.actions")} body={(r) => r.file && <Button label={t("reports.download")} icon="pi pi-download" size="small" text onClick={() => download(r)} />} />
      </DataTable>
    </div>
  );
}
