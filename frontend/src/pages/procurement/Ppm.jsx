import { useMemo } from "react";
import { useTranslation } from "react-i18next";

import ListPage from "../../components/ListPage.jsx";
import { useAuth } from "../../auth/AuthProvider.jsx";
import { useList } from "../../services/hooks.js";


export default function Ppm() {
  const { t } = useTranslation();
  const { hasCapability } = useAuth();

  // ====================================================================
  // DONNEES DE REFERENCE
  // ====================================================================

  const activities = useList("activities", {
    page_size: 1000,
    ordering: "code",
  });

  const methods = useList("procurementMethods", {
    page_size: 1000,
  });

  const cats = useList("expenseCategories", {
    page_size: 1000,
  });

  // ====================================================================
  // ENREGISTREMENTS
  // ====================================================================

  const activityRecords =
    activities.data?.results ||
    activities.data ||
    [];

  const methodRecords =
    methods.data?.results ||
    methods.data ||
    [];

  const catRecords =
    cats.data?.results ||
    cats.data ||
    [];

  // ====================================================================
  // OPTIONS ACTIVITES
  // ====================================================================

  const activityOpts = useMemo(
    () =>
      activityRecords.map((activity) => ({
        label: activity.code
          ? `${activity.code} — ${activity.title}`
          : activity.title,

        value: activity.id,
      })),
    [activityRecords]
  );

  // ====================================================================
  // OPTIONS METHODES DE PASSATION
  // ====================================================================

  const methodOpts = useMemo(
    () =>
      methodRecords.map((method) => ({
        label: method.code
          ? `${method.code} — ${method.name}`
          : method.name,

        value: method.id,
      })),
    [methodRecords]
  );

  // ====================================================================
  // OPTIONS CATEGORIES DE DEPENSE
  // ====================================================================

  const catOpts = useMemo(
    () =>
      catRecords.map((category) => ({
        label: category.code
          ? `${category.code} — ${category.name}`
          : category.name,

        value: category.id,
      })),
    [catRecords]
  );

  // ====================================================================
  // HELPERS AFFICHAGE
  // ====================================================================

  const activityLabel = (id) => {
    if (!id) {
      return "—";
    }

    return (
      activityOpts.find(
        (option) =>
          Number(option.value) ===
          Number(id)
      )?.label || "—"
    );
  };

  const methodLabel = (id) => {
    if (!id) {
      return "—";
    }

    return (
      methodOpts.find(
        (option) =>
          Number(option.value) ===
          Number(id)
      )?.label || "—"
    );
  };

  // ====================================================================
  // PREPARATION AVANT ENREGISTREMENT
  // ====================================================================

  const prepareBody = (values) => {

    // ------------------------------------------------------------------
    // ACTIVITE FACULTATIVE
    // ------------------------------------------------------------------

    const selectedActivity =
      values.activity
        ? activityRecords.find(
            (activity) =>
              Number(activity.id) ===
              Number(values.activity)
          )
        : null;

    // ------------------------------------------------------------------
    // EXERCICE
    // ------------------------------------------------------------------

    const yearText =
      String(
        values.planned_year || ""
      ).trim();

    if (!/^\d{4}$/.test(yearText)) {
      throw new Error(
        "L'exercice doit être une année à 4 chiffres, par exemple 2026."
      );
    }

    const plannedYear =
      Number(yearText);

    if (
      plannedYear < 2010 ||
      plannedYear > 2090
    ) {
      throw new Error(
        "L'exercice doit être compris entre 2010 et 2090."
      );
    }

    // ------------------------------------------------------------------
    // INTITULE
    // ------------------------------------------------------------------

    const designation =
      String(
        values.designation || ""
      ).trim();

    if (!designation) {
      throw new Error(
        "L'intitulé du marché est obligatoire."
      );
    }

    // ------------------------------------------------------------------
    // COUT ESTIMATIF
    // ------------------------------------------------------------------

    if (
      values.planned_amount === null ||
      values.planned_amount === undefined ||
      values.planned_amount === ""
    ) {
      throw new Error(
        "Le coût estimatif est obligatoire."
      );
    }

    // ------------------------------------------------------------------
    // VALIDATION DES DATES
    // ------------------------------------------------------------------

    if (
      values.planned_contract_signature_date &&
      values.planned_contract_end_date
    ) {
      const signatureDate =
        new Date(
          values.planned_contract_signature_date
        );

      const endDate =
        new Date(
          values.planned_contract_end_date
        );

      if (
        endDate <
        signatureDate
      ) {
        throw new Error(
          "La date prévue de fin du contrat doit être postérieure ou égale à la date prévue de signature du contrat."
        );
      }
    }

    // ------------------------------------------------------------------
    // DONNEES ENVOYEES A L'API
    // ------------------------------------------------------------------

    return {
      ppm_ref:
        values.ppm_ref ||
        "",

      activity:
        selectedActivity
          ? selectedActivity.id
          : null,

      designation,

      program_node:
        selectedActivity
          ? selectedActivity.program_node || null
          : null,

      expense_category:
        values.expense_category ||
        null,

      procurement_method:
        values.procurement_method ||
        null,

      planned_amount:
        values.planned_amount,

      planned_year:
        plannedYear,

      planned_contract_signature_date:
        values.planned_contract_signature_date ||
        null,

      planned_contract_end_date:
        values.planned_contract_end_date ||
        null,

      is_active:
        values.is_active ?? true,
    };
  };

  // ====================================================================
  // PAGE
  // ====================================================================

  return (
    <ListPage
      title="Programmation des marchés"
      resourceName="ppmItems"
      canManage={
        hasCapability(
          "procurementprocess.create"
        )
      }

      // ---------------------------------------------------------------
      // PREPARATION AVANT SAUVEGARDE
      // ---------------------------------------------------------------

      prepareBody={prepareBody}

      // ---------------------------------------------------------------
      // TABLEAU
      // ---------------------------------------------------------------

      columns={[
        {
          field: "activity",
          header: "Activité",

          body: (row) => {
            if (row.activity_title) {
              return row.activity_code
                ? `${row.activity_code} — ${row.activity_title}`
                : row.activity_title;
            }

            return activityLabel(
              row.activity
            );
          },
        },

        {
          field: "designation",
          header: "Intitulé du marché",
        },

        {
          field: "planned_amount",
          header: "Coût estimatif",
        },

        {
          field: "planned_year",
          header: "Exercice",
        },

        {
          field: "planned_contract_signature_date",
          header: "Date prévue de signature",
        },

        {
          field: "planned_contract_end_date",
          header: "Date prévue de fin",
        },

        {
          field: "procurement_method",
          header: t(
            "procurement.method"
          ),

          body: (row) =>
            row.procurement_method_name
              ? row.procurement_method_name
              : methodLabel(
                  row.procurement_method
                ),
        },
      ]}

      // ---------------------------------------------------------------
      // FORMULAIRE
      // ---------------------------------------------------------------

      fields={[
        {
          name: "activity",
          label: "Activité",
          type: "dropdown",
          options: activityOpts,
          full: true,
        },

        {
          name: "designation",
          label: "Intitulé du marché",
          type: "text",
          required: true,
          full: true,
        },

        {
          name: "planned_amount",
          label: "Coût estimatif",
          type: "number",
          required: true,
        },

        {
          name: "planned_year",
          label: "Exercice",
          type: "text",
          required: true,
          placeholder: "Ex. 2026",
        },

        {
          name: "planned_contract_signature_date",
          label:
            "Date prévue de signature du contrat",
          type: "date",
        },

        {
          name: "planned_contract_end_date",
          label:
            "Date prévue de fin du contrat",
          type: "date",
        },

        {
          name: "procurement_method",
          label: t(
            "procurement.method"
          ),
          type: "dropdown",
          options: methodOpts,
        },

        {
          name: "expense_category",
          label: t(
            "finance.category"
          ),
          type: "dropdown",
          options: catOpts,
        },

        {
          name: "ppm_ref",
          label: "Réf PPM",
          type: "text",
        },
      ]}
    />
  );
}