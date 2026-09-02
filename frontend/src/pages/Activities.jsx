import { useMemo, useState } from "react";
import { Button } from "primereact/button";
import { Column } from "primereact/column";
import { DataTable } from "primereact/datatable";
import { Dropdown } from "primereact/dropdown";
import { InputText } from "primereact/inputtext";
import { useTranslation } from "react-i18next";

import EntityFormDialog from "../components/EntityFormDialog.jsx";
import { useAuth } from "../auth/AuthProvider.jsx";
import { useList, useSave } from "../services/hooks.js";


export default function Activities() {
  const { t } = useTranslation();
  const { hasCapability } = useAuth();

  const canCreate = hasCapability("activity.create");

  const currentYear = new Date().getFullYear();

  const [programNodeFilter, setProgramNodeFilter] = useState(null);
  const [search, setSearch] = useState("");

  const [dialog, setDialog] = useState({
    open: false,
    initial: null,
  });


  // ====================================================================
  // DONNEES DE REFERENCE
  // ====================================================================

  const geoUnits = useList("geoUnits", {
    page_size: 1000,
    ordering: "geo_level__rank,name",
  });

  const programNodes = useList("programNodes", {
    page_size: 1000,
    ordering: "order,code",
  });

  const indicators = useList("indicators", {
    page_size: 1000,
    is_active: true,
    ordering: "order,code",
  });

  const partners = useList("partners", {
    page_size: 1000,
    ordering: "name",
  });

  const units = useList("unitsOfMeasure", {
    page_size: 1000,
    ordering: "name",
  });

  /*
   * On conserve WorkPlan/PTBA dans la structure existante.
   * L'utilisateur ne choisit cependant plus un PTBA :
   * il saisit simplement l'année de l'exercice.
   *
   * On charge tous les exercices, actifs ou non,
   * afin d'éviter de recréer un exercice déjà existant.
   */
  const workplans = useList("workplans", {
    page_size: 1000,
    ordering: "-year,name",
  });

  const technicalPlans = useList("technicalPlans", {
    page_size: 1000,
    ordering: "-workplan__year,activity__code",
  });


  // ====================================================================
  // DONNEES NORMALISEES
  // ====================================================================

  const geoRecords =
    geoUnits.data?.results ||
    geoUnits.data ||
    [];

  const programNodeRecords =
    programNodes.data?.results ||
    programNodes.data ||
    [];

  const indicatorRecords =
    indicators.data?.results ||
    indicators.data ||
    [];

  const partnerRecords =
    partners.data?.results ||
    partners.data ||
    [];

  const unitRecords =
    units.data?.results ||
    units.data ||
    [];

  const workplanRecords =
    workplans.data?.results ||
    workplans.data ||
    [];

  const technicalPlanRecords =
    technicalPlans.data?.results ||
    technicalPlans.data ||
    [];


  // ====================================================================
  // OPTIONS - ZONES D'INTERVENTION
  // ====================================================================

  /*
   * Global n'est PAS créé comme GeoUnit.
   * Une activité globale est enregistrée avec geo_unit = null.
   */
  const geoOptions = [
    {
      label: "Global",
      value: null,
    },

    ...geoRecords.map((g) => {
      const level = g.geo_level_name
        ? `${g.geo_level_name} — `
        : "";

      return {
        label: `${level}${g.name}`,
        value: g.id,
      };
    }),
  ];


  // ====================================================================
  // OPTIONS - COMPOSANTES
  // ====================================================================

  const componentOptions = programNodeRecords
    .filter(
      (node) =>
        node.node_type === "COMPONENT"
    )
    .map((node) => ({
      label: `${node.code} — ${node.name}`,
      value: node.id,
    }));


  // ====================================================================
  // OPTIONS - SOUS-COMPOSANTES SELON COMPOSANTE
  // ====================================================================

  const selectedComponent =
    dialog.initial?.component ?? null;

  const subcomponentOptions = programNodeRecords
    .filter((node) => {
      if (node.node_type !== "SUBCOMPONENT") {
        return false;
      }

      if (!selectedComponent) {
        return false;
      }

      return (
        Number(node.parent) ===
        Number(selectedComponent)
      );
    })
    .map((node) => ({
      label: `${node.code} — ${node.name}`,
      value: node.id,
    }));


  // ====================================================================
  // OPTIONS - TOUTES LES SOUS-COMPOSANTES POUR LE FILTRE TABLEAU
  // ====================================================================

  const allSubcomponentOptions = programNodeRecords
    .filter(
      (node) =>
        node.node_type === "SUBCOMPONENT"
    )
    .map((node) => ({
      label: `${node.code} — ${node.name}`,
      value: node.id,
    }));


  // ====================================================================
  // OPTIONS - RESPONSABLES / PARTENAIRES
  // ====================================================================

  const partnerOptions = partnerRecords.map((partner) => ({
    label: partner.name,
    value: partner.id,
  }));


  // ====================================================================
  // OPTIONS - UNITES DE MESURE
  // ====================================================================

  const unitOptions = unitRecords.map((unit) => ({
    label: unit.symbol
      ? `${unit.name} (${unit.symbol})`
      : unit.name,
    value: unit.id,
  }));


  // ====================================================================
  // OPTIONS - INDICATEURS
  // ====================================================================

  const selectedProgramNode =
    dialog.initial?.program_node ?? null;

  const indicatorOptions = indicatorRecords
    .filter((indicator) => {
      if (!selectedProgramNode) {
        return true;
      }

      if (!indicator.program_node) {
        return true;
      }

      return (
        Number(indicator.program_node) ===
        Number(selectedProgramNode)
      );
    })
    .map((indicator) => ({
      label: `${indicator.code} — ${indicator.name}`,
      value: indicator.id,
    }));


  // ====================================================================
  // PARAMETRES DE RECHERCHE ACTIVITES
  // ====================================================================

  const params = useMemo(
    () => ({
      page_size: 100,

      ...(programNodeFilter
        ? {
            program_node: programNodeFilter,
          }
        : {}),

      ...(search.trim()
        ? {
            search: search.trim(),
          }
        : {}),
    }),
    [
      programNodeFilter,
      search,
    ]
  );


  // ====================================================================
  // ACTIVITES
  // ====================================================================

  const {
    data,
    isLoading,
    refetch,
  } = useList(
    "activities",
    params
  );

  const rows =
    data?.results ||
    data ||
    [];


  // ====================================================================
  // SAUVEGARDE
  // ====================================================================

  const saveActivity =
    useSave("activities");

  const saveWorkplan =
    useSave("workplans");

  const saveTechnicalPlan =
    useSave("technicalPlans");


  // ====================================================================
  // FORMULAIRE
  // ====================================================================

  const fields = [

    // ------------------------------------------------------------------
    // IDENTIFICATION DE L'ACTIVITE
    // ------------------------------------------------------------------

    {
      name: "code",
      label: "Code",
      type: "text",
      required: true,
    },

    {
      name: "title",
      label: "Intitulé activité",
      type: "text",
      required: true,
      full: true,
    },


    // ------------------------------------------------------------------
    // COMPOSANTE / SOUS-COMPOSANTE
    // ------------------------------------------------------------------

    {
      name: "component",
      label: "Composante",
      type: "dropdown",
      required: true,
      options: componentOptions,
      full: true,
    },

    {
      name: "program_node",
      label: "Sous-composante",
      type: "dropdown",
      required: true,
      options: subcomponentOptions,
      full: true,
    },

    {
      name: "indicator",
      label: "Indicateur associé",
      type: "dropdown",
      options: indicatorOptions,
      full: true,
    },


    // ------------------------------------------------------------------
    // LOCALISATION / RESPONSABILITE
    // ------------------------------------------------------------------

    {
      name: "geo_unit",
      label: "Zone d’intervention",
      type: "dropdown",
      options: geoOptions,
      full: true,
    },

    {
      name: "responsible",
      label: "Responsable",
      type: "dropdown",
      options: partnerOptions,
    },

    {
      name: "unit",
      label: "Unité de mesure",
      type: "dropdown",
      options: unitOptions,
    },


    // ------------------------------------------------------------------
    // INFORMATIONS GENERALES
    // ------------------------------------------------------------------

    {
      name: "objective",
      label: "Objectif",
      type: "textarea",
      full: true,
    },

    {
      name: "description",
      label: "Description",
      type: "textarea",
      full: true,
    },


    // ------------------------------------------------------------------
    // PROGRAMMATION / EXERCICE
    // ------------------------------------------------------------------

    {
      name: "exercise",
      label: "Exercice",
      type: "text",
      required: true,
      placeholder: "Ex. 2025",
    },

    {
      name: "planned_quantity",
      label: "Quantité prévue",
      type: "number",
      required: true,
    },

    {
      name: "planned_start_date",
      label: "Date prévue de début",
      type: "date",
      required: true,
    },

    {
      name: "planned_end_date",
      label: "Date prévue de fin",
      type: "date",
      required: true,
    },

    {
      name: "implementation_modality",
      label: "Modalités de mise en œuvre",
      type: "textarea",
      full: true,
    },

    {
      name: "expected_output",
      label: "Extrant attendu",
      type: "textarea",
      full: true,
    },

    {
      name: "observations",
      label: "Observation",
      type: "textarea",
      full: true,
    },
  ];


  // ====================================================================
  // AFFICHAGE SOUS-COMPOSANTE
  // ====================================================================

  const programNodeBody = (row) => {
    if (!row.program_node_name) {
      return "—";
    }

    if (row.program_node_code) {
      return (
        `${row.program_node_code} — ` +
        `${row.program_node_name}`
      );
    }

    return row.program_node_name;
  };


  // ====================================================================
  // AFFICHAGE ZONE
  // ====================================================================

  const geoBody = (row) => {
    if (!row.geo_unit) {
      return "Global";
    }

    if (!row.geo_unit_name) {
      return "Global";
    }

    if (row.geo_level_name) {
      return (
        `${row.geo_level_name} — ` +
        `${row.geo_unit_name}`
      );
    }

    return row.geo_unit_name;
  };


  // ====================================================================
  // AFFICHAGE RESPONSABLE
  // ====================================================================

  const responsibleBody = (row) => {
    return row.responsible_name || "—";
  };


  // ====================================================================
  // AFFICHAGE UNITE
  // ====================================================================

  const unitBody = (row) => {
    if (!row.unit_name) {
      return "—";
    }

    if (row.unit_symbol) {
      return (
        `${row.unit_name} ` +
        `(${row.unit_symbol})`
      );
    }

    return row.unit_name;
  };


  // ====================================================================
  // AFFICHAGE INDICATEUR
  // ====================================================================

  const indicatorBody = (row) => {
    if (!row.indicator_name) {
      return "—";
    }

    if (row.indicator_code) {
      return (
        `${row.indicator_code} — ` +
        `${row.indicator_name}`
      );
    }

    return row.indicator_name;
  };


  // ====================================================================
  // AFFICHAGE EXERCICE
  // ====================================================================

  const exerciseBody = (row) => {
    const plan = technicalPlanRecords.find(
      (technicalPlan) =>
        Number(technicalPlan.activity) ===
        Number(row.id)
    );

    if (!plan) {
      return "—";
    }

    if (plan.workplan_year) {
      return String(plan.workplan_year);
    }

    const workplan = workplanRecords.find(
      (item) =>
        Number(item.id) ===
        Number(plan.workplan)
    );

    return workplan?.year
      ? String(workplan.year)
      : "—";
  };


  // ====================================================================
  // AFFICHAGE QUANTITE
  // ====================================================================

  const quantityBody = (row) => {
    const plan = technicalPlanRecords.find(
      (technicalPlan) =>
        Number(technicalPlan.activity) ===
        Number(row.id)
    );

    if (!plan) {
      return "—";
    }

    return (
      plan.planned_quantity ??
      "—"
    );
  };


  // ====================================================================
  // RETROUVER LA COMPOSANTE D'UNE SOUS-COMPOSANTE
  // ====================================================================

  const getComponentId = (programNodeId) => {
    if (!programNodeId) {
      return null;
    }

    const node = programNodeRecords.find(
      (item) =>
        Number(item.id) ===
        Number(programNodeId)
    );

    return node?.parent || null;
  };


  // ====================================================================
  // NOUVELLE ACTIVITE
  // ====================================================================

  const openNew = () => {
    const initialProgramNode =
      programNodeFilter || null;

    const initialComponent =
      getComponentId(initialProgramNode);

    setDialog({
      open: true,

      initial: {
        component:
          initialComponent,

        program_node:
          initialProgramNode,

        geo_unit:
          null,

        exercise:
          String(currentYear),
      },
    });
  };


  // ====================================================================
  // MODIFICATION
  // ====================================================================

  const openEdit = (row) => {

    const technicalPlan =
      technicalPlanRecords.find(
        (plan) =>
          Number(plan.activity) ===
          Number(row.id)
      );


    const associatedWorkplan =
      technicalPlan
        ? workplanRecords.find(
            (workplan) =>
              Number(workplan.id) ===
              Number(technicalPlan.workplan)
          )
        : null;


    setDialog({
      open: true,

      initial: {
        ...row,

        component:
          getComponentId(
            row.program_node
          ),

        technical_plan_id:
          technicalPlan?.id || null,

        exercise:
          String(
            technicalPlan?.workplan_year ||
            associatedWorkplan?.year ||
            currentYear
          ),

        planned_quantity:
          technicalPlan?.planned_quantity ??
          null,

        planned_start_date:
          technicalPlan?.planned_start_date ||
          null,

        planned_end_date:
          technicalPlan?.planned_end_date ||
          null,

        implementation_modality:
          technicalPlan?.implementation_modality ||
          "",

        expected_output:
          technicalPlan?.expected_output ||
          "",

        observations:
          technicalPlan?.observations ||
          "",
      },
    });
  };


  // ====================================================================
  // ENREGISTREMENT
  // ====================================================================

  const saveAll = async (values) => {

    // ------------------------------------------------------------------
    // 0. VALIDATIONS
    // ------------------------------------------------------------------

    const exerciseText =
      String(values.exercise || "").trim();


    if (!/^\d{4}$/.test(exerciseText)) {
      throw new Error(
        "L'exercice doit être une année à 4 chiffres, par exemple 2025."
      );
    }


    const exercise =
      Number(exerciseText);


    if (
      exercise < 2010 ||
      exercise > 2090
    ) {
      throw new Error(
        "L'exercice doit être compris entre 2010 et 2090."
      );
    }


    /*
     * La date de fin ne peut pas précéder
     * la date de début.
     */
    if (
      values.planned_start_date &&
      values.planned_end_date &&
      values.planned_end_date <
        values.planned_start_date
    ) {
      throw new Error(
        "La date de fin doit être postérieure ou égale à la date de début."
      );
    }


    if (!values.component) {
      throw new Error(
        "La composante est obligatoire."
      );
    }


    if (!values.program_node) {
      throw new Error(
        "La sous-composante est obligatoire."
      );
    }


    /*
     * Vérifier que la sous-composante appartient
     * réellement à la composante sélectionnée.
     */
    const selectedSubcomponent =
      programNodeRecords.find(
        (node) =>
          Number(node.id) ===
          Number(values.program_node)
      );


    if (
      !selectedSubcomponent ||
      selectedSubcomponent.node_type !==
        "SUBCOMPONENT" ||
      Number(selectedSubcomponent.parent) !==
        Number(values.component)
    ) {
      throw new Error(
        "La sous-composante sélectionnée n'appartient pas à la composante choisie."
      );
    }


    // ------------------------------------------------------------------
    // 1. RETROUVER OU CREER LE WORKPLAN CORRESPONDANT A L'EXERCICE
    // ------------------------------------------------------------------

    let selectedWorkplan =
      workplanRecords.find(
        (workplan) =>
          Number(workplan.year) ===
          exercise
      );


    /*
     * Si aucun WorkPlan n'existe pour l'année saisie,
     * on le crée automatiquement.
     *
     * La structure WorkPlan/PTBA de la base est conservée.
     * L'utilisateur ne manipule que l'année "Exercice".
     */
    if (!selectedWorkplan) {

      const createdWorkplan =
        await saveWorkplan.mutateAsync({
          body: {
            code:
              `EX-${exercise}`,

            name:
              `Exercice ${exercise}`,

            year:
              exercise,

            version:
              "",

            is_current:
              false,

            is_active:
              true,
          },
        });


      if (!createdWorkplan?.id) {
        throw new Error(
          `Impossible de créer l'exercice ${exercise}.`
        );
      }


      selectedWorkplan =
        createdWorkplan;


      /*
       * On rafraîchit la liste des exercices
       * afin que le nouvel exercice soit immédiatement
       * disponible dans l'interface.
       */
      await workplans.refetch?.();
    }


    // ------------------------------------------------------------------
    // 2. DONNEES ACTIVITY
    // ------------------------------------------------------------------

    const activityBody = {
      code:
        values.code,

      title:
        values.title,

      program_node:
        values.program_node,

      geo_unit:
        values.geo_unit || null,

      responsible:
        values.responsible || null,

      unit:
        values.unit || null,

      indicator:
        values.indicator || null,

      objective:
        values.objective || "",

      description:
        values.description || "",
    };


    // ------------------------------------------------------------------
    // 3. ENREGISTRER L'ACTIVITE
    // ------------------------------------------------------------------

    const savedActivity =
      await saveActivity.mutateAsync({
        id: values.id,
        body: activityBody,
      });


    const activityId =
      savedActivity?.id ||
      values.id;


    if (!activityId) {
      throw new Error(
        "Impossible de récupérer l'identifiant de l'activité."
      );
    }


    // ------------------------------------------------------------------
    // 4. DONNEES TECHNICAL PLAN
    // ------------------------------------------------------------------

    const technicalPlanBody = {
      workplan:
        selectedWorkplan.id,

      activity:
        activityId,

      planned_quantity:
        values.planned_quantity ?? null,

      unit:
        values.unit || null,

      geo_unit:
        values.geo_unit || null,

      responsible:
        values.responsible || null,

      planned_start_date:
        values.planned_start_date || null,

      planned_end_date:
        values.planned_end_date || null,

      implementation_modality:
        values.implementation_modality || "",

      expected_output:
        values.expected_output || "",

      observations:
        values.observations || "",
    };


    // ------------------------------------------------------------------
    // 5. ENREGISTRER LA PROGRAMMATION
    // ------------------------------------------------------------------

    await saveTechnicalPlan.mutateAsync({
      id:
        values.technical_plan_id ||
        undefined,

      body:
        technicalPlanBody,
    });


    // ------------------------------------------------------------------
    // 6. RAFRAICHIR
    // ------------------------------------------------------------------

    await refetch();

    await technicalPlans.refetch?.();

    await workplans.refetch?.();


    setDialog({
      open: false,
      initial: null,
    });
  };


  // ====================================================================
  // CHANGEMENT DES VALEURS DU FORMULAIRE
  // ====================================================================

  const handleValuesChange = (next) => {
    setDialog((current) => {

      const previousComponent =
        current.initial?.component ??
        null;

      const newComponent =
        next.component ??
        null;


      if (
        Number(previousComponent || 0) !==
        Number(newComponent || 0)
      ) {
        return {
          ...current,

          initial: {
            ...next,
            program_node: null,
            indicator: null,
          },
        };
      }


      const previousProgramNode =
        current.initial?.program_node ??
        null;

      const newProgramNode =
        next.program_node ??
        null;


      if (
        Number(previousProgramNode || 0) !==
        Number(newProgramNode || 0)
      ) {
        return {
          ...current,

          initial: {
            ...next,
            indicator: null,
          },
        };
      }


      return {
        ...current,
        initial: next,
      };
    });
  };


  // ====================================================================
  // RENDER
  // ====================================================================

  return (
    <div>

      {/* ============================================================= */}
      {/* ENTETE + FILTRES */}
      {/* ============================================================= */}

      <div className="d-flex align-items-center gap-2 mb-3 flex-wrap">

        <h4 className="m-0 me-auto">
          {t("nav.activities")}
        </h4>


        {/* Recherche */}

        <span className="p-input-icon-left">
          <i className="pi pi-search" />

          <InputText
            value={search}
            onChange={(e) =>
              setSearch(
                e.target.value
              )
            }
            placeholder="Rechercher une activité..."
            style={{
              minWidth: "16rem",
            }}
          />
        </span>


        {/* Filtre sous-composante */}

        <Dropdown
          placeholder="Sous-composante"
          value={programNodeFilter}
          options={allSubcomponentOptions}
          onChange={(e) =>
            setProgramNodeFilter(
              e.value
            )
          }
          filter
          showClear
          style={{
            minWidth: "18rem",
          }}
        />


        {/* Nouvelle activité */}

        {canCreate && (
          <Button
            label={t("common.new")}
            icon="pi pi-plus"
            onClick={openNew}
          />
        )}

      </div>


      {/* ============================================================= */}
      {/* TABLEAU */}
      {/* ============================================================= */}

      <DataTable
        value={rows}
        loading={isLoading}
        responsiveLayout="scroll"
        paginator
        rows={25}
        stripedRows
        emptyMessage={t("common.empty")}
      >

        <Column
          field="code"
          header="Code"
          style={{
            minWidth: "7rem",
          }}
        />

        <Column
          field="title"
          header="Intitulé activité"
          style={{
            minWidth: "16rem",
          }}
        />

        <Column
          header="Sous-composante"
          body={programNodeBody}
          style={{
            minWidth: "16rem",
          }}
        />

        <Column
          header="Exercice"
          body={exerciseBody}
          style={{
            minWidth: "8rem",
          }}
        />

        <Column
          header="Quantité prévue"
          body={quantityBody}
          style={{
            minWidth: "9rem",
          }}
        />

        <Column
          header="Zone d’intervention"
          body={geoBody}
          style={{
            minWidth: "12rem",
          }}
        />

        <Column
          header="Responsable"
          body={responsibleBody}
          style={{
            minWidth: "12rem",
          }}
        />

        <Column
          header="Unité"
          body={unitBody}
          style={{
            minWidth: "10rem",
          }}
        />

        <Column
          header="Indicateur"
          body={indicatorBody}
          style={{
            minWidth: "15rem",
          }}
        />


        {/* Actions */}

        <Column
          header={t("common.actions")}

          body={(row) => (
            <div className="d-flex gap-2 align-items-center">

              {canCreate && (
                <Button
                  icon="pi pi-pencil"
                  text
                  rounded
                  size="small"
                  tooltip="Modifier"
                  tooltipOptions={{
                    position: "top",
                  }}
                  onClick={() =>
                    openEdit(row)
                  }
                />
              )}

            </div>
          )}

          style={{
            width: "6rem",
          }}
        />

      </DataTable>


      {/* ============================================================= */}
      {/* FORMULAIRE UNIQUE ACTIVITE + PROGRAMMATION */}
      {/* ============================================================= */}

      <EntityFormDialog
        visible={dialog.open}

        onHide={() =>
          setDialog({
            open: false,
            initial: null,
          })
        }

        fields={fields}

        initial={dialog.initial}

        title={
          dialog.initial?.id
            ? "Modifier l’activité et sa programmation"
            : "Nouvelle activité et programmation"
        }

        onValuesChange={handleValuesChange}

        onSubmit={saveAll}
      />

    </div>
  );
}