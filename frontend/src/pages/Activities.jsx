import { useMemo, useState } from "react";
import { Button } from "primereact/button";
import { Column } from "primereact/column";
import { DataTable } from "primereact/datatable";
import { Dropdown } from "primereact/dropdown";
import { useTranslation } from "react-i18next";

import EntityFormDialog from "../components/EntityFormDialog.jsx";
import WorkflowActions from "../components/WorkflowActions.jsx";
import WorkflowBadge from "../components/WorkflowBadge.jsx";
import { useAuth } from "../auth/AuthProvider.jsx";
import { useList, useSave } from "../services/hooks.js";

const KINDS = [
  "TRAINING", "AWARENESS", "FIELD_VISIT", "VISIT_RECEIVED",
  "MEETING", "SUBPROJECT", "STAKEHOLDER", "OBSERVATION",
];

const KIND_LABELS = {
  TRAINING: "Formation", AWARENESS: "Sensibilisation", FIELD_VISIT: "Visite de terrain",
  VISIT_RECEIVED: "Visite reçue", MEETING: "Réunion", SUBPROJECT: "Sous-projet",
  STAKEHOLDER: "Autre intervenant", OBSERVATION: "Changement observé",
};

export default function Activities() {
  const { t } = useTranslation();
  const { hasCapability } = useAuth();
  const canCreate = hasCapability("activity.create");
  const [kind, setKind] = useState(null);
  const [programNodeFilter, setProgramNodeFilter] = useState(null);
  const [dialog, setDialog] = useState({ open: false, initial: null });

  const geoUnits = useList("geoUnits", { page_size: 1000 });
  const programNodes = useList("programNodes", { page_size: 1000, ordering: "order,code" });
  const indicators = useList("indicators", { page_size: 1000, is_active: true, ordering: "order,code" });

  const geoOptions = (geoUnits.data?.results || []).map((g) => ({ label: g.name, value: g.id }));
  const programNodeOptions = (programNodes.data?.results || []).map((n) => ({
    label: `${n.code} — ${n.name}`,
    value: n.id,
  }));

  const selectedProgramNode = dialog.initial?.program_node ?? null;
  const indicatorOptions = (indicators.data?.results || [])
    .filter((i) => !selectedProgramNode || !i.program_node || i.program_node === selectedProgramNode)
    .map((i) => ({ label: `${i.code} — ${i.name}`, value: i.id }));

  const params = useMemo(() => ({
    page_size: 100,
    ...(kind ? { kind } : {}),
    ...(programNodeFilter ? { program_node: programNodeFilter } : {}),
  }), [kind, programNodeFilter]);

  const { data, isLoading, refetch } = useList("activities", params);
  const rows = data?.results || [];
  const save = useSave("activities");

  const baseFields = (currentKind) => {
    const f = [
      { name: "kind", label: "Type", type: "dropdown", required: true, options: KINDS.map((k) => ({ label: KIND_LABELS[k], value: k })) },
      { name: "title", label: "Titre", type: "text", required: true, full: true },
      { name: "program_node", label: "Composante / sous-composante", type: "dropdown", required: true, options: programNodeOptions, full: true },
      { name: "indicator", label: "Indicateur associé", type: "dropdown", options: indicatorOptions, full: true },
      { name: "date", label: "Date", type: "date", required: true },
      { name: "geo_unit", label: t("measurements.geo_unit"), type: "dropdown", options: geoOptions },
      { name: "location", label: "Lieu", type: "text" },
      { name: "organizer", label: "Organisateur", type: "text" },
      { name: "total_participants", label: "Participants", type: "number" },
      { name: "women_count", label: "dont Femmes", type: "number" },
      { name: "youth_count", label: "dont Jeunes", type: "number" },
      { name: "objective", label: "Objectif", type: "textarea", full: true },
      { name: "description", label: "Description / observations", type: "textarea", full: true },
    ];
    if (currentKind === "SUBPROJECT") {
      f.push(
        { name: "beneficiary_org", label: "Organisation bénéficiaire", type: "text" },
        { name: "management_committee", label: "Comité de gestion", type: "text" },
        { name: "submission_date", label: "Date de soumission", type: "date" },
        { name: "funding_requested", label: "Financement demandé", type: "number" },
        { name: "funding_obtained", label: "Financement obtenu", type: "number" },
      );
    }
    if (currentKind === "STAKEHOLDER") {
      f.push(
        { name: "actor_name", label: "Nom de l'acteur", type: "text" },
        { name: "implantation_date", label: "Date d'implantation", type: "date" },
        { name: "main_actions", label: "Principales actions", type: "textarea", full: true },
      );
    }
    return f;
  };

  const [draftKind, setDraftKind] = useState("TRAINING");
  const fields = baseFields(dialog.initial?.kind || draftKind);

  return (
    <div>
      <div className="d-flex align-items-center gap-2 mb-3 flex-wrap">
        <h4 className="m-0 me-auto">{t("nav.activities")}</h4>
        <Dropdown
          placeholder="Composante / sous-composante"
          value={programNodeFilter}
          options={programNodeOptions}
          onChange={(e) => setProgramNodeFilter(e.value)}
          filter
          showClear
          style={{ minWidth: "18rem" }}
        />
        <Dropdown placeholder="Type" value={kind} options={KINDS.map((k) => ({ label: KIND_LABELS[k], value: k }))} onChange={(e) => setKind(e.value)} showClear />
        {canCreate && (
          <Button label={t("common.new")} icon="pi pi-plus" onClick={() => {
            setDraftKind(kind || "TRAINING");
            setDialog({ open: true, initial: { kind: kind || "TRAINING", program_node: programNodeFilter || null } });
          }} />
        )}
      </div>

      <DataTable value={rows} loading={isLoading} responsiveLayout="stack" breakpoint="960px" paginator rows={25} stripedRows emptyMessage={t("common.empty")}>
        <Column header="Type" body={(r) => KIND_LABELS[r.kind]} />
        <Column field="title" header="Titre" />
        <Column header="Composante / sous-composante" body={(r) => r.program_node_name ? `${r.program_node_code} — ${r.program_node_name}` : "—"} />
        <Column header="Indicateur" body={(r) => r.indicator_name ? `${r.indicator_code} — ${r.indicator_name}` : "—"} />
        <Column field="date" header="Date" />
        <Column field="total_participants" header="Participants" />
        <Column header={t("common.status")} body={(r) => <WorkflowBadge status={r.status} />} />
        <Column
          header={t("common.actions")}
          body={(r) => (
            <div className="d-flex gap-2 align-items-center">
              <WorkflowActions resourceName="activities" area="activity" record={r} onDone={refetch} />
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
        fields={fields}
        initial={dialog.initial}
        title={t("nav.activities")}
        onValuesChange={(next) => setDialog((current) => ({ ...current, initial: next }))}
        onSubmit={async (v) => {
          await save.mutateAsync({ id: v.id, body: v });
          refetch();
        }}
      />
    </div>
  );
}
