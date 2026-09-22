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


  // ====================================================================
  // FILTRES
  // ====================================================================

  const [componentFilter, setComponentFilter] = useState(null);
  const [programNodeFilter, setProgramNodeFilter] = useState(null);
  const [search, setSearch] = useState("");


  // ====================================================================
  // PAGINATION SERVEUR
  // ====================================================================

  const [page, setPage] = useState(1);
  const [rowsPerPage, setRowsPerPage] = useState(25);

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
  // HIERARCHIE GEOGRAPHIQUE
  //
  // 0 = Wilaya
  // 1 = Moughataa
  // 2 = Commune
  // 3 = Village / Localité
  // ====================================================================

  const getGeoRank = (geo) => {
    if (!geo) {
      return null;
    }

    if (
      geo.geo_level_rank !== undefined &&
      geo.geo_level_rank !== null
    ) {
      return Number(geo.geo_level_rank);
    }

    const levelName = String(
      geo.geo_level_name ||
      geo.level_name ||
      ""
    ).toLowerCase();

    if (levelName.includes("wilaya")) {
      return 0;
    }

    if (levelName.includes("moughataa")) {
      return 1;
    }

    if (levelName.includes("commune")) {
      return 2;
    }

    if (
      levelName.includes("village") ||
      levelName.includes("localité") ||
      levelName.includes("localite")
    ) {
      return 3;
    }

    return null;
  };


  // ====================================================================
  // RETROUVER UNE GEO UNIT
  // ====================================================================

  const getGeoUnit = (id) => {
    if (!id) {
      return null;
    }

    return (
      geoRecords.find(
        (geo) =>
          Number(geo.id) ===
          Number(id)
      ) || null
    );
  };


  // ====================================================================
  // RECONSTRUIRE LA HIERARCHIE GEOGRAPHIQUE
  // ====================================================================

  const getGeoHierarchy = (geoUnitId) => {
    const result = {
      wilaya: null,
      moughataa: null,
      commune: null,
      village: null,
    };

    if (!geoUnitId) {
      return result;
    }

    let current = getGeoUnit(geoUnitId);

    while (current) {
      const rank = getGeoRank(current);

      if (rank === 0) {
        result.wilaya = current.id;
      }

      if (rank === 1) {
        result.moughataa = current.id;
      }

      if (rank === 2) {
        result.commune = current.id;
      }

      if (rank === 3) {
        result.village = current.id;
      }

      if (!current.parent) {
        break;
      }

      current = getGeoUnit(current.parent);
    }

    return result;
  };


  // ====================================================================
  // OPTIONS WILAYA
  // ====================================================================

  const wilayaOptions = geoRecords
    .filter(
      (geo) =>
        getGeoRank(geo) === 0
    )
    .map((geo) => ({
      label: geo.name,
      value: geo.id,
    }));


  // ====================================================================
  // OPTIONS MOUGHATAA
  // ====================================================================

  const selectedWilaya =
    dialog.initial?.wilaya ?? null;

  const moughataaOptions = geoRecords
    .filter(
      (geo) =>
        getGeoRank(geo) === 1 &&
        selectedWilaya &&
        Number(geo.parent) ===
          Number(selectedWilaya)
    )
    .map((geo) => ({
      label: geo.name,
      value: geo.id,
    }));


  // ====================================================================
  // OPTIONS COMMUNE
  // ====================================================================

  const selectedMoughataa =
    dialog.initial?.moughataa ?? null;

  const communeOptions = geoRecords
    .filter(
      (geo) =>
        getGeoRank(geo) === 2 &&
        selectedMoughataa &&
        Number(geo.parent) ===
          Number(selectedMoughataa)
    )
    .map((geo) => ({
      label: geo.name,
      value: geo.id,
    }));


  // ====================================================================
  // OPTIONS VILLAGE / LOCALITE
  // ====================================================================

  const selectedCommune =
    dialog.initial?.commune ?? null;

  const villageOptions = geoRecords
    .filter(
      (geo) =>
        getGeoRank(geo) === 3 &&
        selectedCommune &&
        Number(geo.parent) ===
          Number(selectedCommune)
    )
    .map((geo) => ({
      label: geo.name,
      value: geo.id,
    }));


  // ====================================================================
  // OPTIONS COMPOSANTES
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

  const allComponentOptions = componentOptions;


  // ====================================================================
  // OPTIONS SOUS-COMPOSANTES DU FORMULAIRE
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
  // OPTIONS SOUS-COMPOSANTES DU FILTRE
  // ====================================================================

  const allSubcomponentOptions = programNodeRecords
    .filter((node) => {
      if (node.node_type !== "SUBCOMPONENT") {
        return false;
      }

      if (!componentFilter) {
        return true;
      }

      return (
        Number(node.parent) ===
        Number(componentFilter)
      );
    })
    .map((node) => ({
      label: `${node.code} — ${node.name}`,
      value: node.id,
    }));


  // ====================================================================
  // RESPONSABLES
  // ====================================================================

  const partnerOptions = partnerRecords.map(
    (partner) => ({
      label: partner.name,
      value: partner.id,
    })
  );


  // ====================================================================
  // UNITES
  // ====================================================================

  const unitOptions = unitRecords.map(
    (unit) => ({
      label: unit.symbol
        ? `${unit.name} (${unit.symbol})`
        : unit.name,
      value: unit.id,
    })
  );


  // ====================================================================
  // INDICATEURS
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
  // SOUS-COMPOSANTES DE LA COMPOSANTE FILTREE
  // ====================================================================

  const filteredSubcomponentIds = useMemo(() => {
    if (!componentFilter) {
      return [];
    }

    return programNodeRecords
      .filter(
        (node) =>
          node.node_type === "SUBCOMPONENT" &&
          Number(node.parent) ===
            Number(componentFilter)
      )
      .map(
        (node) =>
          Number(node.id)
      );
  }, [
    componentFilter,
    programNodeRecords,
  ]);


  // ====================================================================
  // PARAMETRES ACTIVITES
  // ====================================================================

  const params = useMemo(
    () => ({
      page,
      page_size: rowsPerPage,

      ...(programNodeFilter
        ? {
            program_node:
              programNodeFilter,
          }
        : {}),

      ...(search.trim()
        ? {
            search:
              search.trim(),
          }
        : {}),
    }),
    [
      page,
      rowsPerPage,
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

  const apiRows =
    data?.results ||
    data ||
    [];


  // ====================================================================
  // FILTRAGE COMPOSANTE
  // ====================================================================

  const rows = useMemo(() => {
    if (programNodeFilter) {
      return apiRows;
    }

    if (!componentFilter) {
      return apiRows;
    }

    return apiRows.filter(
      (activity) =>
        filteredSubcomponentIds.includes(
          Number(activity.program_node)
        )
    );
  }, [
    apiRows,
    componentFilter,
    programNodeFilter,
    filteredSubcomponentIds,
  ]);

  const totalRecords =
    data?.count ??
    rows.length;


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
    // IDENTIFICATION
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
    // ZONE D'INTERVENTION
    //
    // Tous ces champs sont FACULTATIFS.
    //
    // Aucun choix = Global.
    // Wilaya seulement = niveau Wilaya.
    // Moughataa = niveau Moughataa.
    // Commune = niveau Commune.
    // Village = niveau Village.
    // ------------------------------------------------------------------

    {
      name: "wilaya",
      label: "Wilaya",
      type: "dropdown",
      options: wilayaOptions,
      full: true,
    },

    {
      name: "moughataa",
      label: "Moughataa",
      type: "dropdown",
      options: moughataaOptions,
      full: true,
    },

    {
      name: "commune",
      label: "Commune",
      type: "dropdown",
      options: communeOptions,
      full: true,
    },

    {
      name: "village",
      label: "Village / Localité",
      type: "dropdown",
      options: villageOptions,
      full: true,
    },


    // ------------------------------------------------------------------
    // RESPONSABILITE
    // ------------------------------------------------------------------

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
    // PROGRAMMATION
    // ------------------------------------------------------------------

    {
      name: "exercise",
      label: "Exercice",
      type: "text",
      required: true,
      placeholder: "Ex. 2026",
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

    /*
     * Modalités de mise en œuvre
     * Extrant attendu
     * Observation
     *
     * NE SONT PLUS AFFICHES DANS LE FORMULAIRE.
     * Les champs restent dans le modèle et la base.
     */
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

    if (row.geo_unit_name) {
      return row.geo_unit_name;
    }

    const geo =
      getGeoUnit(row.geo_unit);

    return geo?.name || "Global";
  };


  // ====================================================================
  // RESPONSABLE
  // ====================================================================

  const responsibleBody = (row) => {
    return row.responsible_name || "—";
  };


  // ====================================================================
  // UNITE
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
  // INDICATEUR
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
  // EXERCICE
  // ====================================================================

  const exerciseBody = (row) => {
    const plan =
      technicalPlanRecords.find(
        (technicalPlan) =>
          Number(technicalPlan.activity) ===
          Number(row.id)
      );

    if (!plan) {
      return "—";
    }

    if (plan.workplan_year) {
      return String(
        plan.workplan_year
      );
    }

    const workplan =
      workplanRecords.find(
        (item) =>
          Number(item.id) ===
          Number(plan.workplan)
      );

    return workplan?.year
      ? String(workplan.year)
      : "—";
  };


  // ====================================================================
  // QUANTITE
  // ====================================================================

  const quantityBody = (row) => {
    const plan =
      technicalPlanRecords.find(
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
  // RETROUVER LA COMPOSANTE
  // ====================================================================

  const getComponentId = (programNodeId) => {
    if (!programNodeId) {
      return null;
    }

    const node =
      programNodeRecords.find(
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
      initialProgramNode
        ? getComponentId(
            initialProgramNode
          )
        : componentFilter || null;

    setDialog({
      open: true,

      initial: {
        component:
          initialComponent,

        program_node:
          initialProgramNode,

        wilaya:
          null,

        moughataa:
          null,

        commune:
          null,

        village:
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
              Number(
                technicalPlan.workplan
              )
          )
        : null;

    const geoHierarchy =
      getGeoHierarchy(
        row.geo_unit
      );

    setDialog({
      open: true,

      initial: {
        ...row,

        component:
          getComponentId(
            row.program_node
          ),

        ...geoHierarchy,

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
      },
    });
  };


  // ====================================================================
  // ENREGISTREMENT
  // ====================================================================

  const saveAll = async (values) => {

    // ------------------------------------------------------------------
    // EXERCICE
    // ------------------------------------------------------------------

    const exerciseText =
      String(
        values.exercise || ""
      ).trim();

    if (!/^\d{4}$/.test(exerciseText)) {
      throw new Error(
        "L'exercice doit être une année à 4 chiffres, par exemple 2026."
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


    // ------------------------------------------------------------------
    // DATES
    // ------------------------------------------------------------------

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


    // ------------------------------------------------------------------
    // COMPOSANTE / SOUS-COMPOSANTE
    // ------------------------------------------------------------------

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
      Number(
        selectedSubcomponent.parent
      ) !==
        Number(values.component)
    ) {
      throw new Error(
        "La sous-composante sélectionnée n'appartient pas à la composante choisie."
      );
    }


    // ------------------------------------------------------------------
    // ZONE D'INTERVENTION
    //
    // Règle :
    //
    // rien              => Global
    // Wilaya             => Wilaya
    // Moughataa          => Moughataa
    // Commune            => Commune
    // Village / Localité => Village / Localité
    //
    // On enregistre donc toujours le niveau le plus précis.
    // ------------------------------------------------------------------

    const selectedGeoUnit =
      values.village ||
      values.commune ||
      values.moughataa ||
      values.wilaya ||
      null;


    // ------------------------------------------------------------------
    // WORKPLAN / EXERCICE
    // ------------------------------------------------------------------

    let selectedWorkplan =
      workplanRecords.find(
        (workplan) =>
          Number(workplan.year) ===
          exercise
      );

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

      await workplans.refetch?.();
    }


    // ------------------------------------------------------------------
    // ACTIVITY
    // ------------------------------------------------------------------

    const activityBody = {
      code:
        values.code,

      title:
        values.title,

      program_node:
        values.program_node,

      geo_unit:
        selectedGeoUnit,

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
    // ENREGISTRER ACTIVITY
    // ------------------------------------------------------------------

    const savedActivity =
      await saveActivity.mutateAsync({
        id:
          values.id,

        body:
          activityBody,
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
    // PRESERVER LES CHAMPS TECHNIQUES CACHES
    //
    // Ils ne sont plus modifiables depuis ce formulaire,
    // mais on ne supprime pas leurs valeurs existantes.
    // ------------------------------------------------------------------

    const existingTechnicalPlan =
      technicalPlanRecords.find(
        (plan) =>
          Number(plan.id) ===
            Number(values.technical_plan_id) ||
          (
            !values.technical_plan_id &&
            Number(plan.activity) ===
              Number(activityId)
          )
      );


    // ------------------------------------------------------------------
    // TECHNICAL PLAN
    // ------------------------------------------------------------------

    const technicalPlanBody = {
      workplan:
        selectedWorkplan.id,

      activity:
        activityId,

      planned_quantity:
        values.planned_quantity ??
        null,

      unit:
        values.unit ||
        null,

      geo_unit:
        selectedGeoUnit,

      responsible:
        values.responsible ||
        null,

      planned_start_date:
        values.planned_start_date ||
        null,

      planned_end_date:
        values.planned_end_date ||
        null,

      /*
       * Ces trois champs restent dans la base.
       * On conserve leurs valeurs existantes.
       */
      implementation_modality:
        existingTechnicalPlan?.implementation_modality ||
        "",

      expected_output:
        existingTechnicalPlan?.expected_output ||
        "",

      observations:
        existingTechnicalPlan?.observations ||
        "",
    };


    // ------------------------------------------------------------------
    // ENREGISTRER PROGRAMMATION
    // ------------------------------------------------------------------

    await saveTechnicalPlan.mutateAsync({
      id:
        values.technical_plan_id ||
        undefined,

      body:
        technicalPlanBody,
    });


    // ------------------------------------------------------------------
    // RAFRAICHIR
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
  // CHANGEMENT DES VALEURS
  // ====================================================================

  const handleValuesChange = (next) => {
    setDialog((current) => {
      const previous =
        current.initial || {};


      // ----------------------------------------------------------------
      // WILAYA CHANGE
      // ----------------------------------------------------------------

      if (
        Number(
          previous.wilaya || 0
        ) !==
        Number(
          next.wilaya || 0
        )
      ) {
        return {
          ...current,

          initial: {
            ...next,

            moughataa:
              null,

            commune:
              null,

            village:
              null,
          },
        };
      }


      // ----------------------------------------------------------------
      // MOUGHATAA CHANGE
      // ----------------------------------------------------------------

      if (
        Number(
          previous.moughataa || 0
        ) !==
        Number(
          next.moughataa || 0
        )
      ) {
        return {
          ...current,

          initial: {
            ...next,

            commune:
              null,

            village:
              null,
          },
        };
      }


      // ----------------------------------------------------------------
      // COMMUNE CHANGE
      // ----------------------------------------------------------------

      if (
        Number(
          previous.commune || 0
        ) !==
        Number(
          next.commune || 0
        )
      ) {
        return {
          ...current,

          initial: {
            ...next,

            village:
              null,
          },
        };
      }


      // ----------------------------------------------------------------
      // COMPOSANTE CHANGE
      // ----------------------------------------------------------------

      if (
        Number(
          previous.component || 0
        ) !==
        Number(
          next.component || 0
        )
      ) {
        return {
          ...current,

          initial: {
            ...next,

            program_node:
              null,

            indicator:
              null,
          },
        };
      }


      // ----------------------------------------------------------------
      // SOUS-COMPOSANTE CHANGE
      // ----------------------------------------------------------------

      if (
        Number(
          previous.program_node || 0
        ) !==
        Number(
          next.program_node || 0
        )
      ) {
        return {
          ...current,

          initial: {
            ...next,

            indicator:
              null,
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


        <span className="p-input-icon-left">
          <i className="pi pi-search" />

          <InputText
            value={search}

            onChange={(e) => {
              setSearch(
                e.target.value
              );

              setPage(1);
            }}

            placeholder="Rechercher une activité..."

            style={{
              minWidth:
                "16rem",
            }}
          />
        </span>


        {/* FILTRE COMPOSANTE */}

        <Dropdown
          placeholder="Composante"

          value={componentFilter}

          options={allComponentOptions}

          onChange={(e) => {
            setComponentFilter(
              e.value
            );

            setProgramNodeFilter(
              null
            );

            setPage(1);
          }}

          filter
          showClear

          style={{
            minWidth:
              "17rem",
          }}
        />


        {/* FILTRE SOUS-COMPOSANTE */}

        <Dropdown
          placeholder="Sous-composante"

          value={programNodeFilter}

          options={allSubcomponentOptions}

          onChange={(e) => {
            setProgramNodeFilter(
              e.value
            );

            if (e.value) {
              const selectedNode =
                programNodeRecords.find(
                  (node) =>
                    Number(node.id) ===
                    Number(e.value)
                );

              if (selectedNode?.parent) {
                setComponentFilter(
                  selectedNode.parent
                );
              }
            }

            setPage(1);
          }}

          filter
          showClear

          style={{
            minWidth:
              "18rem",
          }}
        />


        {/* NOUVELLE ACTIVITE */}

        {canCreate && (
          <Button
            label={
              t("common.new")
            }

            icon="pi pi-plus"

            onClick={
              openNew
            }
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
        lazy

        first={
          (page - 1) *
          rowsPerPage
        }

        rows={
          rowsPerPage
        }

        totalRecords={
          totalRecords
        }

        rowsPerPageOptions={[
          25,
          50,
          100,
        ]}

        onPage={(event) => {
          setPage(
            event.page + 1
          );

          setRowsPerPage(
            event.rows
          );
        }}

        paginatorTemplate={
          "FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink RowsPerPageDropdown CurrentPageReport"
        }

        currentPageReportTemplate={
          "{first} - {last} sur {totalRecords} activités"
        }

        stripedRows

        emptyMessage={
          t("common.empty")
        }
      >

        <Column
          field="code"
          header="Code"

          style={{
            minWidth:
              "7rem",
          }}
        />

        <Column
          field="title"
          header="Intitulé activité"

          style={{
            minWidth:
              "16rem",
          }}
        />

        <Column
          header="Sous-composante"
          body={
            programNodeBody
          }

          style={{
            minWidth:
              "16rem",
          }}
        />

        <Column
          header="Exercice"
          body={
            exerciseBody
          }

          style={{
            minWidth:
              "8rem",
          }}
        />

        <Column
          header="Quantité prévue"
          body={
            quantityBody
          }

          style={{
            minWidth:
              "9rem",
          }}
        />

        <Column
          header="Zone d’intervention"
          body={
            geoBody
          }

          style={{
            minWidth:
              "12rem",
          }}
        />

        <Column
          header="Responsable"
          body={
            responsibleBody
          }

          style={{
            minWidth:
              "12rem",
          }}
        />

        <Column
          header="Unité"
          body={
            unitBody
          }

          style={{
            minWidth:
              "10rem",
          }}
        />

        <Column
          header="Indicateur"
          body={
            indicatorBody
          }

          style={{
            minWidth:
              "15rem",
          }}
        />


        {/* ACTIONS */}

        <Column
          header={
            t("common.actions")
          }

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
                    position:
                      "top",
                  }}

                  onClick={() =>
                    openEdit(row)
                  }
                />
              )}

            </div>
          )}

          style={{
            width:
              "6rem",
          }}
        />

      </DataTable>


      {/* ============================================================= */}
      {/* FORMULAIRE */}
      {/* ============================================================= */}

      <EntityFormDialog
        visible={
          dialog.open
        }

        onHide={() =>
          setDialog({
            open:
              false,

            initial:
              null,
          })
        }

        fields={
          fields
        }

        initial={
          dialog.initial
        }

        title={
          dialog.initial?.id
            ? "Modifier l’activité et sa programmation"
            : "Nouvelle activité et programmation"
        }

        onValuesChange={
          handleValuesChange
        }

        onSubmit={
          saveAll
        }
      />

    </div>
  );
}