import { useMemo, useState } from "react";
import { Button } from "primereact/button";
import { Column } from "primereact/column";
import { DataTable } from "primereact/datatable";
import { Dialog } from "primereact/dialog";
import { Dropdown } from "primereact/dropdown";
import { InputNumber } from "primereact/inputnumber";
import { useTranslation } from "react-i18next";

import EntityFormDialog from "../components/EntityFormDialog.jsx";
import WorkflowActions from "../components/WorkflowActions.jsx";
import WorkflowBadge from "../components/WorkflowBadge.jsx";
import { useAuth } from "../auth/AuthProvider.jsx";
import http from "../services/http.js";
import { useList, useSave } from "../services/hooks.js";

export default function Measurements() {
  const { t } = useTranslation();
  const { hasCapability } = useAuth();
  const canCreate = hasCapability("measurement.create");
  const [filters, setFilters] = useState({ status: null, indicator: null });
  const [dialog, setDialog] = useState({ open: false, initial: null });
  const [grid, setGrid] = useState(false);

  const indicators = useList("indicators", { page_size: 500, is_active: true });
  const geoUnits = useList("geoUnits", { page_size: 1000 });
  const save = useSave("measurements");

  const indOptions = (indicators.data?.results || []).map((i) => ({
    label: `${i.code} — ${i.name}`,
    value: i.id,
  }));
  const geoOptions = (geoUnits.data?.results || []).map((g) => ({ label: g.name, value: g.id }));

  const params = useMemo(() => {
    const p = { page_size: 100 };
    if (filters.status) p.status = filters.status;
    if (filters.indicator) p.indicator = filters.indicator;
    return p;
  }, [filters]);
  const { data, isLoading, refetch } = useList("measurements", params);
  const rows = data?.results || [];

  const formFields = [
    { name: "indicator", label: t("measurements.indicator"), type: "dropdown", options: indOptions, required: true },
    { name: "geo_unit", label: t("measurements.geo_unit"), type: "dropdown", options: geoOptions },
    { name: "period_year", label: t("common.year"), type: "number", required: true },
    { name: "period_quarter", label: t("common.quarter"), type: "number" },
    { name: "value", label: t("common.value"), type: "number", required: true },
    { name: "narrative", label: t("measurements.narrative"), type: "textarea", full: true },
  ];

  const statusOptions = ["DRAFT", "SUBMITTED", "VALIDATED", "AUDITED", "CONSOLIDATED", "REJECTED"].map(
    (s) => ({ label: t(`workflow.${s}`), value: s }),
  );

  return (
    <div>
      <div className="d-flex align-items-center gap-2 mb-3 flex-wrap">
        <h4 className="m-0 me-auto">{t("nav.measurements")}</h4>
        <Dropdown
          placeholder={t("measurements.indicator")}
          value={filters.indicator}
          options={indOptions}
          onChange={(e) => setFilters((f) => ({ ...f, indicator: e.value }))}
          showClear
          filter
          style={{ minWidth: "16rem" }}
        />
        <Dropdown
          placeholder={t("common.status")}
          value={filters.status}
          options={statusOptions}
          onChange={(e) => setFilters((f) => ({ ...f, status: e.value }))}
          showClear
        />
        {canCreate && (
          <>
            <Button label={t("measurements.grid_entry")} icon="pi pi-table" outlined onClick={() => setGrid(true)} />
            <Button label={t("common.new")} icon="pi pi-plus" onClick={() => setDialog({ open: true, initial: {} })} />
          </>
        )}
      </div>

      <DataTable value={rows} loading={isLoading} responsiveLayout="stack" breakpoint="960px" paginator rows={25} stripedRows emptyMessage={t("common.empty")}>
        <Column field="indicator_code" header={t("measurements.indicator")} />
        <Column header={t("measurements.period")} body={(r) => `${r.period_year}${r.period_quarter ? " T" + r.period_quarter : ""}`} />
        <Column field="value" header={t("common.value")} />
        <Column header={t("common.status")} body={(r) => <WorkflowBadge status={r.status} />} />
        <Column
          header={t("common.actions")}
          body={(r) => (
            <div className="d-flex gap-2 align-items-center">
              <WorkflowActions resourceName="measurements" area="measurement" record={r} onDone={refetch} />
              {canCreate && r.status === "DRAFT" && (
                <Button icon="pi pi-pencil" text rounded size="small" onClick={() => setDialog({ open: true, initial: r })} />
              )}
            </div>
          )}
        />
      </DataTable>

      <EntityFormDialog
        visible={dialog.open}
        onHide={() => setDialog({ open: false, initial: null })}
        fields={formFields}
        initial={dialog.initial}
        title={t("nav.measurements")}
        onSubmit={async (v) => {
          await save.mutateAsync({ id: v.id, body: v });
          refetch();
        }}
      />

      <GridEntry
        visible={grid}
        onHide={() => setGrid(false)}
        indicators={indicators.data?.results || []}
        geoOptions={geoOptions}
        onSaved={() => {
          setGrid(false);
          refetch();
        }}
      />
    </div>
  );
}

function GridEntry({ visible, onHide, indicators, geoOptions, onSaved }) {
  const { t } = useTranslation();
  const [year, setYear] = useState(new Date().getFullYear());
  const [quarter, setQuarter] = useState(null);
  const [geo, setGeo] = useState(null);
  const [values, setValues] = useState({});
  const [saving, setSaving] = useState(false);

  const save = async () => {
    setSaving(true);
    const payload = Object.entries(values)
      .filter(([, v]) => v != null)
      .map(([indicator, value]) => ({
        indicator: Number(indicator),
        geo_unit: geo,
        period_year: year,
        period_quarter: quarter,
        value,
      }));
    if (payload.length) await http.post("/measurements/bulk/", payload).catch(() => {});
    setSaving(false);
    setValues({});
    onSaved();
  };

  return (
    <Dialog header={t("measurements.grid_entry")} visible={visible} onHide={onHide} style={{ width: "44rem" }} maximizable>
      <div className="row g-2 mb-3">
        <div className="col-4">
          <label className="form-label">{t("common.year")}</label>
          <InputNumber value={year} onValueChange={(e) => setYear(e.value)} useGrouping={false} className="w-100" />
        </div>
        <div className="col-4">
          <label className="form-label">{t("common.quarter")}</label>
          <Dropdown value={quarter} options={[1, 2, 3, 4].map((q) => ({ label: "T" + q, value: q }))} onChange={(e) => setQuarter(e.value)} showClear className="w-100" />
        </div>
        <div className="col-4">
          <label className="form-label">{t("measurements.geo_unit")}</label>
          <Dropdown value={geo} options={geoOptions} onChange={(e) => setGeo(e.value)} filter showClear className="w-100" />
        </div>
      </div>
      <DataTable value={indicators} responsiveLayout="stack" breakpoint="640px" scrollable scrollHeight="40vh">
        <Column field="code" header={t("common.code")} style={{ width: "6rem" }} />
        <Column field="name" header={t("common.name")} />
        <Column
          header={t("common.value")}
          body={(r) => (
            <InputNumber
              value={values[r.id] ?? null}
              onValueChange={(e) => setValues((s) => ({ ...s, [r.id]: e.value }))}
              className="w-100"
            />
          )}
          style={{ width: "10rem" }}
        />
      </DataTable>
      <div className="d-flex justify-content-end gap-2 mt-3">
        <Button label={t("common.cancel")} text onClick={onHide} />
        <Button label={t("measurements.save_all_draft")} loading={saving} onClick={save} />
      </div>
    </Dialog>
  );
}
