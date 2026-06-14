import { useMemo, useState } from "react";
import { Button } from "primereact/button";
import { Card } from "primereact/card";
import { Column } from "primereact/column";
import { DataTable } from "primereact/datatable";
import { SelectButton } from "primereact/selectbutton";
import { useTranslation } from "react-i18next";

import EntityFormDialog from "../../components/EntityFormDialog.jsx";
import WorkflowActions from "../../components/WorkflowActions.jsx";
import WorkflowBadge from "../../components/WorkflowBadge.jsx";
import { useAuth } from "../../auth/AuthProvider.jsx";
import { api } from "../../services/api.js";
import { useList, useSave } from "../../services/hooks.js";

export default function Processes() {
  const { t } = useTranslation();
  const { hasCapability } = useAuth();
  const canCreate = hasCapability("procurementprocess.create");
  const [view, setView] = useState("list");
  const [dialog, setDialog] = useState({ open: false, initial: null });

  const methods = useList("procurementMethods", { page_size: 200 });
  const stages = useList("procurementStages", { page_size: 50 });
  const methodOpts = (methods.data?.results || []).map((m) => ({ label: `${m.code} — ${m.name}`, value: m.id }));
  const stageList = (stages.data?.results || []).slice().sort((a, b) => a.order - b.order);

  const { data, isLoading, refetch } = useList("procurementProcesses", { page_size: 200 });
  const rows = data?.results || [];
  const save = useSave("procurementProcesses");

  const advance = async (row) => {
    await api.procurementProcesses.action(row.id, "advance", {});
    refetch();
  };

  const fields = [
    { name: "designation", label: t("procurement.designation"), type: "text", required: true, full: true },
    { name: "procurement_method", label: t("procurement.method"), type: "dropdown", options: methodOpts },
    { name: "estimated_amount", label: "Montant estimé", type: "number" },
    { name: "awarded_amount", label: "Montant attribué", type: "number" },
    { name: "supplier", label: "Fournisseur", type: "text" },
  ];

  const board = useMemo(() => {
    const cols = {};
    for (const s of stageList) cols[s.id] = { stage: s, items: [] };
    const none = [];
    for (const p of rows) {
      if (p.current_stage && cols[p.current_stage]) cols[p.current_stage].items.push(p);
      else none.push(p);
    }
    return { cols: Object.values(cols), none };
  }, [rows, stageList]);

  return (
    <div>
      <div className="d-flex align-items-center gap-2 mb-3 flex-wrap">
        <h4 className="m-0 me-auto">{t("nav.processes")}</h4>
        <SelectButton
          value={view}
          onChange={(e) => e.value && setView(e.value)}
          options={[
            { label: "Liste", value: "list" },
            { label: "Tableau d'étapes", value: "board" },
          ]}
        />
        {canCreate && <Button label={t("common.new")} icon="pi pi-plus" onClick={() => setDialog({ open: true, initial: {} })} />}
      </div>

      {view === "list" ? (
        <DataTable value={rows} loading={isLoading} responsiveLayout="stack" breakpoint="960px" paginator rows={25} stripedRows emptyMessage={t("common.empty")}>
          <Column field="designation" header={t("procurement.designation")} />
          <Column field="current_stage_name" header={t("procurement.stage")} />
          <Column field="awarded_amount" header="Attribué" />
          <Column header="Terminé" body={(r) => (r.is_completed ? t("common.yes") : t("common.no"))} />
          <Column header={t("common.status")} body={(r) => <WorkflowBadge status={r.status} />} />
          <Column
            header={t("common.actions")}
            body={(r) => (
              <div className="d-flex gap-2 align-items-center">
                {canCreate && !r.is_completed && (
                  <Button label={t("procurement.advance")} size="small" outlined onClick={() => advance(r)} />
                )}
                <WorkflowActions resourceName="procurementProcesses" area="procurementprocess" record={r} onDone={refetch} />
              </div>
            )}
          />
        </DataTable>
      ) : (
        <div className="d-flex gap-3" style={{ overflowX: "auto" }}>
          {board.cols.map((col) => (
            <div key={col.stage.id} style={{ minWidth: 220 }}>
              <div className="fw-semibold mb-2">
                {col.stage.order}. {col.stage.name}
              </div>
              {col.items.map((p) => (
                <Card key={p.id} className="mb-2">
                  <div style={{ fontSize: "0.85rem" }}>{p.designation}</div>
                  <div className="mt-1">
                    <WorkflowBadge status={p.status} />
                  </div>
                  {canCreate && !p.is_completed && (
                    <Button label={t("procurement.advance")} size="small" text className="mt-1" onClick={() => advance(p)} />
                  )}
                </Card>
              ))}
              {col.items.length === 0 && <div className="text-muted small">—</div>}
            </div>
          ))}
        </div>
      )}

      <EntityFormDialog
        visible={dialog.open}
        onHide={() => setDialog({ open: false, initial: null })}
        fields={fields}
        initial={dialog.initial}
        title={t("nav.processes")}
        onSubmit={async (v) => {
          await save.mutateAsync({ id: v.id, body: v });
          refetch();
        }}
      />
    </div>
  );
}
