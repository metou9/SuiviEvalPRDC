import { useMemo, useState } from "react";
import { Dropdown } from "primereact/dropdown";
import { Tag } from "primereact/tag";

import ListPage from "../../components/ListPage.jsx";
import { useAuth } from "../../auth/AuthProvider.jsx";
import { useList } from "../../services/hooks.js";


// ======================================================================
// STATUTS D'EXECUTION
// ======================================================================

const EXECUTION_STATUS_OPTIONS = [
  {
    label: "Non démarré",
    value: "NOT_STARTED",
  },
  {
    label: "En cours",
    value: "IN_PROGRESS",
  },
  {
    label: "Suspendu",
    value: "SUSPENDED",
  },
  {
    label: "Terminé",
    value: "COMPLETED",
  },
];


const EXECUTION_STATUS_LABELS = {
  NOT_STARTED: "Non démarré",
  IN_PROGRESS: "En cours",
  SUSPENDED: "Suspendu",
  COMPLETED: "Terminé",
};


// ======================================================================
// MOIS
// ======================================================================

const MONTH_OPTIONS = [
  { label: "Janvier", value: 1 },
  { label: "Février", value: 2 },
  { label: "Mars", value: 3 },
  { label: "Avril", value: 4 },
  { label: "Mai", value: 5 },
  { label: "Juin", value: 6 },
  { label: "Juillet", value: 7 },
  { label: "Août", value: 8 },
  { label: "Septembre", value: 9 },
  { label: "Octobre", value: 10 },
  { label: "Novembre", value: 11 },
  { label: "Décembre", value: 12 },
];


const QUARTER_OPTIONS = [
  { label: "1er trimestre", value: 1 },
  { label: "2e trimestre", value: 2 },
  { label: "3e trimestre", value: 3 },
  { label: "4e trimestre", value: 4 },
];


// ======================================================================
// COMPOSANT
// ======================================================================

export default function TechnicalExecution() {
  const { hasCapability } = useAuth();

  /*
   * On conserve la même capacité fonctionnelle que les activités.
   *
   * Le backend utilise également workflow_area = "activity".
   */
  const canManage = hasCapability("activity.create");


  // ====================================================================
  // FILTRES
  // ====================================================================

  const [responsibleFilter, setResponsibleFilter] =
    useState(null);

  const [yearFilter, setYearFilter] =
    useState(null);

  const [statusFilter, setStatusFilter] =
    useState(null);


  // ====================================================================
  // DONNEES DE REFERENCE
  // ====================================================================

  /*
   * On charge les programmations techniques.
   *
   * La saisie d'exécution ne porte PAS directement sur Activity.
   * Elle porte sur une activité déjà programmée dans TechnicalPlan.
   */
  const technicalPlans = useList(
    "technicalPlans",
    {
      page_size: 1000,
      ordering:
        "-workplan__year,activity__code",
    }
  );


  /*
   * Les responsables sont actuellement des partenaires
   * liés à TechnicalPlan.responsible.
   */
  const partners = useList(
    "partners",
    {
      page_size: 1000,
      ordering: "name",
    }
  );


  /*
   * Les exercices permettent de préparer le filtre Exercice.
   */
  const workplans = useList(
    "workplans",
    {
      page_size: 1000,
      is_active: true,
      ordering: "-year,name",
    }
  );


  // ====================================================================
  // NORMALISATION DES DONNEES
  // ====================================================================

  const technicalPlanRecords =
    technicalPlans.data?.results ||
    technicalPlans.data ||
    [];

  const partnerRecords =
    partners.data?.results ||
    partners.data ||
    [];

  const workplanRecords =
    workplans.data?.results ||
    workplans.data ||
    [];


  // ====================================================================
  // OPTIONS - PROGRAMMATIONS TECHNIQUES
  // ====================================================================

  const technicalPlanOptions =
    technicalPlanRecords.map((plan) => {
      const activity =
        plan.activity_code
          ? `${plan.activity_code} — ${plan.activity_title}`
          : plan.activity_title ||
            `Activité #${plan.activity}`;

      const year =
        plan.workplan_year ||
        "";

      const quantity =
        plan.planned_quantity !== null &&
        plan.planned_quantity !== undefined
          ? ` | Prévu : ${plan.planned_quantity}${
              plan.unit_symbol
                ? ` ${plan.unit_symbol}`
                : ""
            }`
          : "";

      return {
        label:
          `${year} — ${activity}${quantity}`,
        value: plan.id,
      };
    });


  // ====================================================================
  // OPTIONS - RESPONSABLES
  // ====================================================================

  const responsibleOptions =
    partnerRecords.map((partner) => ({
      label: partner.name,
      value: partner.id,
    }));


  // ====================================================================
  // OPTIONS - EXERCICES
  // ====================================================================

  /*
   * On déduplique les années.
   */
  const yearOptions = Array.from(
    new Set(
      workplanRecords
        .map((item) => item.year)
        .filter(Boolean)
    )
  )
    .sort((a, b) => b - a)
    .map((year) => ({
      label: String(year),
      value: year,
    }));


  // ====================================================================
  // PARAMETRES DE FILTRAGE API
  // ====================================================================

  const extraParams = useMemo(
    () => ({
      ...(responsibleFilter
        ? {
            responsible:
              responsibleFilter,
          }
        : {}),

      ...(yearFilter
        ? {
            year:
              yearFilter,
          }
        : {}),

      ...(statusFilter
        ? {
            execution_status:
              statusFilter,
          }
        : {}),
    }),
    [
      responsibleFilter,
      yearFilter,
      statusFilter,
    ]
  );


  // ====================================================================
  // LIBELLES
  // ====================================================================

  const executionStatusLabel = (
    value
  ) => {
    return (
      EXECUTION_STATUS_LABELS[value] ||
      value ||
      "—"
    );
  };


  const monthLabel = (value) => {
    return (
      MONTH_OPTIONS.find(
        (option) =>
          Number(option.value) ===
          Number(value)
      )?.label || "—"
    );
  };


  const quarterLabel = (value) => {
    if (!value) {
      return "—";
    }

    return `T${value}`;
  };


  // ====================================================================
  // AFFICHAGE DU STATUT
  // ====================================================================

  const statusBody = (row) => {
    const value =
      row.execution_status;

    let severity = "secondary";

    if (value === "IN_PROGRESS") {
      severity = "info";
    }

    if (value === "COMPLETED") {
      severity = "success";
    }

    if (value === "SUSPENDED") {
      severity = "warning";
    }

    return (
      <Tag
        value={
          row.execution_status_label ||
          executionStatusLabel(value)
        }
        severity={severity}
      />
    );
  };


  // ====================================================================
  // AFFICHAGE QUANTITE PREVUE
  // ====================================================================

  const plannedQuantityBody = (
    row
  ) => {
    if (
      row.planned_quantity === null ||
      row.planned_quantity === undefined
    ) {
      return "—";
    }

    return `${row.planned_quantity}${
      row.unit_symbol
        ? ` ${row.unit_symbol}`
        : ""
    }`;
  };


  // ====================================================================
  // AFFICHAGE QUANTITE REALISEE
  // ====================================================================

  const actualQuantityBody = (
    row
  ) => {
    if (
      row.actual_quantity === null ||
      row.actual_quantity === undefined
    ) {
      return "—";
    }

    return `${row.actual_quantity}${
      row.unit_symbol
        ? ` ${row.unit_symbol}`
        : ""
    }`;
  };


  // ====================================================================
  // AFFICHAGE TAUX PHYSIQUE
  // ====================================================================

  const progressBody = (row) => {
    if (
      row.physical_progress_percent ===
        null ||
      row.physical_progress_percent ===
        undefined
    ) {
      return "—";
    }

    return `${row.physical_progress_percent} %`;
  };


  // ====================================================================
  // TRANSFORMATION AVANT MODIFICATION
  // ====================================================================

  /*
   * Certains champs du serializer sont seulement destinés
   * à l'affichage.
   *
   * On conserve uniquement les champs réellement éditables
   * dans la fenêtre de modification.
   */
  const toForm = (row) => ({
    id: row.id,

    technical_plan:
      row.technical_plan,

    reporting_date:
      row.reporting_date,

    period_year:
      row.period_year,

    period_quarter:
      row.period_quarter,

    period_month:
      row.period_month,

    actual_quantity:
      row.actual_quantity,

    execution_status:
      row.execution_status,

    actual_start_date:
      row.actual_start_date,

    actual_end_date:
      row.actual_end_date,

    difficulties:
      row.difficulties || "",

    corrective_actions:
      row.corrective_actions || "",

    observations:
      row.observations || "",
  });


  // ====================================================================
  // PREPARATION AVANT ENREGISTREMENT
  // ====================================================================

  const fromForm = (values) => {

    // ------------------------------------------------------------------
    // PROGRAMMATION TECHNIQUE
    // ------------------------------------------------------------------

    const selectedPlan =
      technicalPlanRecords.find(
        (plan) =>
          Number(plan.id) ===
          Number(
            values.technical_plan
          )
      );

    if (!selectedPlan) {
      throw new Error(
        "Veuillez sélectionner une activité programmée."
      );
    }


    // ------------------------------------------------------------------
    // EXERCICE
    // ------------------------------------------------------------------

    /*
     * L'exercice n'est pas saisi librement.
     * Il est récupéré automatiquement depuis le PTBA
     * associé à TechnicalPlan.
     */
    const periodYear =
      Number(
        selectedPlan.workplan_year
      );

    if (
      !periodYear ||
      periodYear < 2010 ||
      periodYear > 2090
    ) {
      throw new Error(
        "L'exercice de la programmation technique est invalide."
      );
    }


    // ------------------------------------------------------------------
    // DATE DE SUIVI
    // ------------------------------------------------------------------

    if (!values.reporting_date) {
      throw new Error(
        "La date de suivi est obligatoire."
      );
    }


    // ------------------------------------------------------------------
    // QUANTITE REALISEE
    // ------------------------------------------------------------------

    if (
      values.actual_quantity !== null &&
      values.actual_quantity !==
        undefined &&
      values.actual_quantity !== "" &&
      Number(
        values.actual_quantity
      ) < 0
    ) {
      throw new Error(
        "La quantité réalisée ne peut pas être négative."
      );
    }


    // ------------------------------------------------------------------
    // MOIS / TRIMESTRE
    // ------------------------------------------------------------------

    let periodMonth =
      values.period_month
        ? Number(
            values.period_month
          )
        : null;

    let periodQuarter =
      values.period_quarter
        ? Number(
            values.period_quarter
          )
        : null;


    /*
     * Si le mois est renseigné,
     * on calcule automatiquement le trimestre.
     *
     * Cela évite les incohérences :
     * Mars = T1
     * Avril = T2
     * etc.
     */
    if (periodMonth) {
      periodQuarter =
        Math.floor(
          (periodMonth - 1) / 3
        ) + 1;
    }


    // ------------------------------------------------------------------
    // COHERENCE DATES REELLES
    // ------------------------------------------------------------------

    if (
      values.actual_start_date &&
      values.actual_end_date &&
      values.actual_end_date <
        values.actual_start_date
    ) {
      throw new Error(
        "La date réelle de fin ne peut pas être antérieure à la date réelle de début."
      );
    }


    // ------------------------------------------------------------------
    // DONNEES ENVOYEES AU BACKEND
    // ------------------------------------------------------------------

    return {
      technical_plan:
        selectedPlan.id,

      reporting_date:
        values.reporting_date,

      period_year:
        periodYear,

      period_quarter:
        periodQuarter,

      period_month:
        periodMonth,

      actual_quantity:
        values.actual_quantity ===
          "" ||
        values.actual_quantity ===
          undefined
          ? null
          : values.actual_quantity,

      execution_status:
        values.execution_status ||
        "NOT_STARTED",

      actual_start_date:
        values.actual_start_date ||
        null,

      actual_end_date:
        values.actual_end_date ||
        null,

      difficulties:
        values.difficulties ||
        "",

      corrective_actions:
        values.corrective_actions ||
        "",

      observations:
        values.observations ||
        "",
    };
  };


  // ====================================================================
  // PAGE
  // ====================================================================

  return (
    <div>

      {/* ============================================================ */}
      {/* FILTRES */}
      {/* ============================================================ */}

      <div className="d-flex align-items-center gap-2 mb-3 flex-wrap">

        {/* ---------------------------------------------------------- */}
        {/* PAR RESPONSABLE */}
        {/* ---------------------------------------------------------- */}

        <Dropdown
          value={responsibleFilter}
          options={responsibleOptions}
          onChange={(e) =>
            setResponsibleFilter(
              e.value
            )
          }
          placeholder="Par responsable"
          filter
          showClear
          style={{
            minWidth: "15rem",
          }}
        />


        {/* ---------------------------------------------------------- */}
        {/* EXERCICE */}
        {/* ---------------------------------------------------------- */}

        <Dropdown
          value={yearFilter}
          options={yearOptions}
          onChange={(e) =>
            setYearFilter(
              e.value
            )
          }
          placeholder="Exercice"
          showClear
          style={{
            minWidth: "10rem",
          }}
        />


        {/* ---------------------------------------------------------- */}
        {/* STATUT */}
        {/* ---------------------------------------------------------- */}

        <Dropdown
          value={statusFilter}
          options={
            EXECUTION_STATUS_OPTIONS
          }
          onChange={(e) =>
            setStatusFilter(
              e.value
            )
          }
          placeholder="Statut"
          showClear
          style={{
            minWidth: "12rem",
          }}
        />

      </div>


      {/* ============================================================ */}
      {/* LISTE DES EXECUTIONS */}
      {/* ============================================================ */}

      <ListPage
        title="Suivi technique"
        resourceName="technicalExecutions"

        canManage={canManage}

        extraParams={extraParams}

        toForm={toForm}

        fromForm={fromForm}


        // ============================================================
        // COLONNES
        // ============================================================

        columns={[
          {
            field: "activity_title",
            header: "Activité",

            body: (row) => {
              if (!row.activity_title) {
                return "—";
              }

              return row.activity_code
                ? `${row.activity_code} — ${row.activity_title}`
                : row.activity_title;
            },
          },

          {
            field: "workplan_year",
            header: "Exercice",
          },

          {
            field: "component_name",
            header: "Composante",
          },

          {
            field:
              "program_node_name",
            header: "Sous-composante",
          },

          {
            field:
              "responsible_name",
            header: "Responsable",

            body: (row) =>
              row.responsible_name ||
              "—",
          },

          {
            field:
              "planned_quantity",
            header: "Quantité prévue",
            body:
              plannedQuantityBody,
          },

          {
            field:
              "actual_quantity",
            header:
              "Quantité réalisée",
            body:
              actualQuantityBody,
          },

          {
            field:
              "physical_progress_percent",
            header:
              "Taux réalisation",
            body:
              progressBody,
          },

          {
            field:
              "execution_status",
            header: "Statut",
            body: statusBody,
          },

          {
            field:
              "reporting_date",
            header:
              "Date de suivi",
          },

          {
            field:
              "period_quarter",
            header: "Trimestre",

            body: (row) =>
              quarterLabel(
                row.period_quarter
              ),
          },

          {
            field:
              "period_month",
            header: "Mois",

            body: (row) =>
              monthLabel(
                row.period_month
              ),
          },
        ]}


        // ============================================================
        // FORMULAIRE
        // ============================================================

        fields={[
          // ----------------------------------------------------------
          // ACTIVITE PROGRAMMEE
          // ----------------------------------------------------------

          {
            name:
              "technical_plan",
            label:
              "Activité programmée",
            type: "dropdown",
            required: true,
            options:
              technicalPlanOptions,
            full: true,
          },


          // ----------------------------------------------------------
          // DATE DE SUIVI
          // ----------------------------------------------------------

          {
            name:
              "reporting_date",
            label: "Date de suivi",
            type: "date",
            required: true,
          },


          // ----------------------------------------------------------
          // QUANTITE REALISEE
          // ----------------------------------------------------------

          {
            name:
              "actual_quantity",
            label:
              "Quantité réalisée",
            type: "number",
          },


          // ----------------------------------------------------------
          // STATUT
          // ----------------------------------------------------------

          {
            name:
              "execution_status",
            label:
              "Statut d'exécution",
            type: "dropdown",
            required: true,
            options:
              EXECUTION_STATUS_OPTIONS,
          },


          // ----------------------------------------------------------
          // TRIMESTRE
          // ----------------------------------------------------------

          {
            name:
              "period_quarter",
            label: "Trimestre",
            type: "dropdown",
            options:
              QUARTER_OPTIONS,
          },


          // ----------------------------------------------------------
          // MOIS
          // ----------------------------------------------------------

          {
            name:
              "period_month",
            label: "Mois",
            type: "dropdown",
            options:
              MONTH_OPTIONS,
          },


          // ----------------------------------------------------------
          // DATE REELLE DE DEBUT
          // ----------------------------------------------------------

          {
            name:
              "actual_start_date",
            label:
              "Date réelle de début",
            type: "date",
          },


          // ----------------------------------------------------------
          // DATE REELLE DE FIN
          // ----------------------------------------------------------

          {
            name:
              "actual_end_date",
            label:
              "Date réelle de fin",
            type: "date",
          },


          // ----------------------------------------------------------
          // DIFFICULTES
          // ----------------------------------------------------------

          {
            name:
              "difficulties",
            label:
              "Difficultés rencontrées",
            type: "textarea",
            full: true,
          },


          // ----------------------------------------------------------
          // ACTIONS CORRECTIVES
          // ----------------------------------------------------------

          {
            name:
              "corrective_actions",
            label:
              "Actions correctives",
            type: "textarea",
            full: true,
          },


          // ----------------------------------------------------------
          // OBSERVATIONS
          // ----------------------------------------------------------

          {
            name:
              "observations",
            label: "Observations",
            type: "textarea",
            full: true,
          },
        ]}
      />
    </div>
  );
}