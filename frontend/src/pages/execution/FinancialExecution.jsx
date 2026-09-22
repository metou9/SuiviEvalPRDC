import { useMemo, useRef, useState } from "react";
import { Button } from "primereact/button";
import { Column } from "primereact/column";
import { DataTable } from "primereact/datatable";
import { Dialog } from "primereact/dialog";
import { Dropdown } from "primereact/dropdown";
import { InputText } from "primereact/inputtext";
import { Toast } from "primereact/toast";
import EntityFormDialog from "../../components/EntityFormDialog.jsx";
import { useAuth } from "../../auth/AuthProvider.jsx";
import { useList, useRemove, useSave } from "../../services/hooks.js";

const money = (v) => `${new Intl.NumberFormat("fr-FR", { maximumFractionDigits: 2 }).format(Number(v || 0))} MRU`;
const quarterFrom = (s = "") => Number(String(s).match(/^\[T([1-4])\](?:\n|$)/)?.[1]) || null;
const observationFrom = (s = "") => String(s).replace(/^\[T[1-4]\](?:\n|$)/, "");
const isActivityFollowUp = (t) => t.kind === "REALIZATION" && /^\[T[1-4]\](?:\n|$)/.test(String(t.narrative || ""));
const errorText = (e) => {
  const data = e?.response?.data;
  return data?.detail || (data && typeof data === "object" ? Object.entries(data).map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(", ") : v}`).join(" ; ") : e?.message) || "Enregistrement impossible.";
};

export default function FinancialExecution() {
  const toast = useRef(null);
  const { hasCapability } = useAuth();
  const canManage = hasCapability("financialtransaction.create");
  const [search, setSearch] = useState("");
  const [exercise, setExercise] = useState(null);
  const [dialog, setDialog] = useState({ open: false, initial: null });
  const [detail, setDetail] = useState(null);
  const budgets = useList("budgetLines", { page_size: 2000, ordering: "-fiscal_year" });
  const transactions = useList("financialTransactions", { page_size: 5000, ordering: "-date" });
  const save = useSave("financialTransactions");
  const remove = useRemove("financialTransactions");
  const lines = budgets.data?.results || budgets.data || [];
  const allTransactions = transactions.data?.results || transactions.data || [];
  const followUps = allTransactions.filter(isActivityFollowUp);
  const years = [...new Set(lines.map((b) => Number(b.fiscal_year)).filter(Boolean))].sort((a, b) => b - a).map((y) => ({ label: String(y), value: y }));
  const activityOptions = lines.filter((b) => b.activity).map((b) => ({
    label: `${b.activity_code ? `${b.activity_code} — ` : ""}${b.activity_title || `Activité #${b.activity}`} | ${b.fiscal_year} | ${money(b.amount)}`,
    value: b.id,
  }));
  // Regrouper toutes les lignes budgétaires d'une même activité et d'un même exercice.
  const rows = useMemo(() => {
    const grouped = new Map();
    for (const b of lines) {
      if (!b.activity) continue;
      const key = `${b.activity}-${b.fiscal_year}`;
      if (!grouped.has(key)) grouped.set(key, {
        key, activity: b.activity, year: Number(b.fiscal_year),
        label: `${b.activity_code ? `${b.activity_code} — ` : ""}${b.activity_title || `Activité #${b.activity}`}`,
        budget: 0, realized: 0, lineIds: [], items: [],
      });
      const row = grouped.get(key);
      row.budget += Number(b.amount || 0);
      row.lineIds.push(Number(b.id));
    }
    for (const t of followUps) {
      const b = lines.find((line) => Number(line.id) === Number(t.budget_line));
      if (!b) continue;
      const row = grouped.get(`${b.activity}-${b.fiscal_year}`);
      if (row) { row.realized += Number(t.amount || 0); row.items.push(t); }
    }
    return [...grouped.values()].map((r) => ({ ...r, rate: r.budget > 0 ? r.realized / r.budget * 100 : 0,
      items: r.items.sort((a, b) => String(b.date || "").localeCompare(String(a.date || ""))) }));
  }, [lines, followUps]);
  const visibleRows = rows.filter((r) => (!exercise || r.year === exercise) && (!search || r.label.toLowerCase().includes(search.toLowerCase())));
  const showError = (e) => toast.current?.show({ severity: "error", summary: "Erreur", detail: errorText(e), life: 6000 });
  const close = () => setDialog({ open: false, initial: null });
  const edit = (t) => {
    setDetail(null);
    setDialog({ open: true, initial: { ...t, period_quarter: quarterFrom(t.narrative), observation: observationFrom(t.narrative) } });
  };
  const submit = async (v) => {
    const b = lines.find((x) => Number(x.id) === Number(v.budget_line));
    if (!b) return showError(new Error("Sélectionnez une activité programmée."));
    if (!v.period_quarter) return showError(new Error("Sélectionnez un trimestre."));
    if (!v.date) return showError(new Error("La date de réalisation est obligatoire."));
    if (v.amount === "" || v.amount === null || v.amount === undefined || Number(v.amount) < 0) return showError(new Error("Saisissez un montant réalisé valide."));
    const quarter = Number(v.period_quarter);
    const dateQuarter = Math.floor((Number(String(v.date).slice(5, 7)) - 1) / 3) + 1;
    if (dateQuarter !== quarter) return showError(new Error("Le trimestre doit correspondre à la date de réalisation."));
    try {
      await save.mutateAsync({ id: v.id, body: {
        budget_line: b.id, kind: "REALIZATION", date: v.date, fiscal_year: b.fiscal_year,
        amount: v.amount, narrative: `[T${quarter}]\n${v.observation || ""}`,
        ...(v.id ? {} : { reference: "" }),
      } });
      close();
      await Promise.all([transactions.refetch(), budgets.refetch()]);
      toast.current?.show({ severity: "success", summary: "Suivi financier enregistré", life: 3000 });
    } catch (e) { showError(e); }
  };
  const deleteItem = async (t) => {
    if (!window.confirm("Supprimer ce suivi financier ?")) return;
    try {
      await remove.mutateAsync(t.id);
      setDetail(null);
      await Promise.all([transactions.refetch(), budgets.refetch()]);
      toast.current?.show({ severity: "success", summary: "Suivi supprimé", life: 3000 });
    } catch (e) { showError(e); }
  };
  const fields = [
    { name: "budget_line", label: "Activité", type: "dropdown", required: true, options: activityOptions, full: true },
    { name: "period_quarter", label: "Trimestre", type: "dropdown", required: true, options: [
      { label: "1er trimestre", value: 1 }, { label: "2e trimestre", value: 2 },
      { label: "3e trimestre", value: 3 }, { label: "4e trimestre", value: 4 },
    ] },
    { name: "amount", label: "Montant réalisé", type: "number", required: true },
    { name: "date", label: "Date de réalisation", type: "date", required: true },
    { name: "observation", label: "Observation", type: "textarea", full: true },
  ];
  return <div>
    <Toast ref={toast} />
    <div className="d-flex justify-content-between align-items-center flex-wrap gap-2 mb-3">
      <div><h4 className="mb-1">Suivi financier</h4><div className="text-muted">Exécution financière par activité</div></div>
      {canManage && <Button label="Nouveau suivi" icon="pi pi-plus" onClick={() => setDialog({ open: true, initial: {} })} />}
    </div>
    <div className="d-flex gap-2 flex-wrap mb-3">
      <InputText value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Rechercher une activité" />
      <Dropdown value={exercise} options={years} onChange={(e) => setExercise(e.value)} placeholder="Exercice" showClear />
    </div>
    <DataTable value={visibleRows} dataKey="key" paginator rows={25} rowsPerPageOptions={[10, 25, 50]} loading={budgets.isLoading || transactions.isLoading} emptyMessage="Aucune activité programmée financièrement">
      <Column field="label" header="Activité" />
      <Column field="year" header="Exercice" />
      <Column field="budget" header="Montant prévu" body={(r) => money(r.budget)} />
      <Column field="realized" header="Montant réalisé" body={(r) => money(r.realized)} />
      <Column field="rate" header="Taux d’exécution" body={(r) => `${r.rate.toFixed(1)} %`} />
      <Column header="Actions" body={(r) => <Button label="Détail" icon="pi pi-eye" text onClick={() => setDetail(r)} />} />
    </DataTable>
    <Dialog visible={!!detail} onHide={() => setDetail(null)} header={detail ? `Détail — ${detail.label}` : "Détail"} style={{ width: "min(950px, 95vw)" }} modal>
      {detail && <>
        <p><strong>Montant prévu :</strong> {money(detail.budget)} &nbsp; <strong>Montant réalisé :</strong> {money(detail.realized)} &nbsp; <strong>Taux :</strong> {detail.rate.toFixed(1)} %</p>
        <DataTable value={detail.items} emptyMessage="Aucun suivi saisi" paginator rows={10}>
          <Column header="Trimestre" body={(t) => quarterFrom(t.narrative) ? `T${quarterFrom(t.narrative)}` : "—"} />
          <Column field="date" header="Date de réalisation" />
          <Column header="Montant réalisé" body={(t) => money(t.amount)} />
          <Column header="Observation" body={(t) => observationFrom(t.narrative) || "—"} />
          {canManage && <Column header="Actions" body={(t) => <div className="d-flex gap-1">
            <Button icon="pi pi-pencil" text aria-label="Modifier" onClick={() => edit(t)} />
            <Button icon="pi pi-trash" text severity="danger" aria-label="Supprimer" onClick={() => deleteItem(t)} />
          </div>} />}
        </DataTable>
      </>}
    </Dialog>
    <EntityFormDialog visible={dialog.open} onHide={close} fields={fields} initial={dialog.initial} title={dialog.initial?.id ? "Modifier le suivi financier" : "Nouveau suivi financier"} onSubmit={submit} />
  </div>;
}
