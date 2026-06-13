import { useMemo, useRef, useState } from "react";
import { Button } from "primereact/button";
import { Column } from "primereact/column";
import { DataTable } from "primereact/datatable";
import { Dropdown } from "primereact/dropdown";
import { FileUpload } from "primereact/fileupload";
import { Toast } from "primereact/toast";
import { useTranslation } from "react-i18next";

import EntityFormDialog from "../../components/EntityFormDialog.jsx";
import WorkflowActions from "../../components/WorkflowActions.jsx";
import WorkflowBadge from "../../components/WorkflowBadge.jsx";
import { useAuth } from "../../auth/AuthProvider.jsx";
import http from "../../services/http.js";
import { useList, useSave } from "../../services/hooks.js";

const KINDS = ["ENGAGEMENT", "DISBURSEMENT", "REALIZATION"];
const KIND_LABEL = { ENGAGEMENT: "Engagement", DISBURSEMENT: "Décaissement", REALIZATION: "Réalisation" };

export default function Transactions() {
  const { t } = useTranslation();
  const { hasCapability } = useAuth();
  const canCreate = hasCapability("financialtransaction.create");
  const toast = useRef(null);
  const [kind, setKind] = useState(null);
  const [dialog, setDialog] = useState({ open: false, initial: null });

  const cats = useList("expenseCategories", { page_size: 200 });
  const nodes = useList("programNodes", { page_size: 200 });
  const catOpts = (cats.data?.results || []).map((c) => ({ label: `${c.code} — ${c.name}`, value: c.id }));
  const nodeOpts = (nodes.data?.results || []).map((n) => ({ label: `${n.code} — ${n.name}`, value: n.id }));

  const params = useMemo(() => ({ page_size: 100, ...(kind ? { kind } : {}) }), [kind]);
  const { data, isLoading, refetch } = useList("financialTransactions", params);
  const rows = data?.results || [];
  const save = useSave("financialTransactions");

  const uploadDoc = async (id, file) => {
    const fd = new FormData();
    fd.append("supporting_doc", file);
    await http.patch(`/financial-transactions/${id}/`, fd, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    toast.current?.show({ severity: "success", summary: "Justificatif ajouté" });
    refetch();
  };

  const fields = [
    { name: "kind", label: t("finance.kind"), type: "dropdown", required: true, options: KINDS.map((k) => ({ label: KIND_LABEL[k], value: k })) },
    { name: "date", label: "Date", type: "date", required: true },
    { name: "fiscal_year", label: t("finance.fiscal_year"), type: "number", required: true },
    { name: "amount", label: t("finance.amount"), type: "number", required: true },
    { name: "expense_category", label: t("finance.category"), type: "dropdown", options: catOpts },
    { name: "program_node", label: t("nav.program"), type: "dropdown", options: nodeOpts },
    { name: "reference", label: "Référence", type: "text" },
    { name: "narrative", label: "Narratif", type: "textarea", full: true },
  ];

  return (
    <div>
      <Toast ref={toast} />
      <div className="d-flex align-items-center gap-2 mb-3 flex-wrap">
        <h4 className="m-0 me-auto">{t("nav.transactions")}</h4>
        <Dropdown placeholder={t("finance.kind")} value={kind} options={KINDS.map((k) => ({ label: KIND_LABEL[k], value: k }))} onChange={(e) => setKind(e.value)} showClear />
        {canCreate && <Button label={t("common.new")} icon="pi pi-plus" onClick={() => setDialog({ open: true, initial: {} })} />}
      </div>

      <DataTable value={rows} loading={isLoading} responsiveLayout="stack" breakpoint="960px" paginator rows={25} stripedRows emptyMessage={t("common.empty")}>
        <Column header={t("finance.kind")} body={(r) => KIND_LABEL[r.kind]} />
        <Column field="date" header="Date" />
        <Column field="fiscal_year" header={t("finance.fiscal_year")} />
        <Column field="amount" header={t("finance.amount")} />
        <Column header="Justificatif" body={(r) => (r.supporting_doc ? <i className="pi pi-check text-success" /> : "—")} />
        <Column header={t("common.status")} body={(r) => <WorkflowBadge status={r.status} />} />
        <Column
          header={t("common.actions")}
          body={(r) => (
            <div className="d-flex gap-2 align-items-center">
              <WorkflowActions resourceName="financialTransactions" area="financialtransaction" record={r} onDone={refetch} />
              {canCreate && r.kind === "REALIZATION" && !r.supporting_doc && r.status === "DRAFT" && (
                <FileUpload
                  mode="basic"
                  auto
                  chooseLabel="Justif."
                  customUpload
                  uploadHandler={(e) => uploadDoc(r.id, e.files[0])}
                />
              )}
            </div>
          )}
        />
      </DataTable>

      <EntityFormDialog
        visible={dialog.open}
        onHide={() => setDialog({ open: false, initial: null })}
        fields={fields}
        initial={dialog.initial}
        title={t("nav.transactions")}
        onSubmit={async (v) => {
          await save.mutateAsync({ id: v.id, body: v });
          refetch();
        }}
      />
    </div>
  );
}
