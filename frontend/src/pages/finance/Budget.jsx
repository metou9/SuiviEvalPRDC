import { useMemo } from "react";
import { useTranslation } from "react-i18next";

import ListPage from "../../components/ListPage.jsx";
import { useAuth } from "../../auth/AuthProvider.jsx";
import { useList } from "../../services/hooks.js";


export default function Budget() {
  const { t } = useTranslation();
  const { hasCapability } = useAuth();

  // ====================================================================
  // DONNEES DE REFERENCE
  // ====================================================================

  const activities = useList("activities", {
    page_size: 1000,
    ordering: "code",
  });

  const cats = useList("expenseCategories", {
    page_size: 1000,
  });

  const funds = useList("fundingSources", {
    page_size: 1000,
  });

  // ====================================================================
  // ENREGISTREMENTS
  // ====================================================================

  const activityRecords =
    activities.data?.results ||
    activities.data ||
    [];

  const catRecords =
    cats.data?.results ||
    cats.data ||
    [];

  const fundRecords =
    funds.data?.results ||
    funds.data ||
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
  // OPTIONS SOURCES DE FINANCEMENT
  // ====================================================================

  const fundOpts = useMemo(
    () =>
      fundRecords.map((fund) => ({
        label: fund.code
          ? `${fund.code} — ${fund.name}`
          : fund.name,

        value: fund.id,
      })),
    [fundRecords]
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

  const catLabel = (id) => {
    if (!id) {
      return "—";
    }

    return (
      catOpts.find(
        (option) =>
          Number(option.value) ===
          Number(id)
      )?.label || "—"
    );
  };

  const fundLabel = (id) => {
    if (!id) {
      return "—";
    }

    return (
      fundOpts.find(
        (option) =>
          Number(option.value) ===
          Number(id)
      )?.label || "—"
    );
  };

  // ====================================================================
  // PREPARATION AVANT ENREGISTREMENT
  //
  // La sous-composante est récupérée automatiquement depuis l'activité.
  // ====================================================================

  const prepareBody = (values) => {

    // ------------------------------------------------------------------
    // ACTIVITE
    // ------------------------------------------------------------------

    const selectedActivity =
      activityRecords.find(
        (activity) =>
          Number(activity.id) ===
          Number(values.activity)
      );

    if (!selectedActivity) {
      throw new Error(
        "Veuillez sélectionner une activité."
      );
    }

    // ------------------------------------------------------------------
    // EXERCICE
    // ------------------------------------------------------------------

    const exerciseText =
      String(
        values.fiscal_year || ""
      ).trim();

    if (!/^\d{4}$/.test(exerciseText)) {
      throw new Error(
        "L'exercice doit être une année à 4 chiffres, par exemple 2026."
      );
    }

    const fiscalYear =
      Number(exerciseText);

    if (
      fiscalYear < 2010 ||
      fiscalYear > 2090
    ) {
      throw new Error(
        "L'exercice doit être compris entre 2010 et 2090."
      );
    }

    // ------------------------------------------------------------------
    // MONTANT
    // ------------------------------------------------------------------

    if (
      values.amount === null ||
      values.amount === undefined ||
      values.amount === ""
    ) {
      throw new Error(
        "Le montant programmé est obligatoire."
      );
    }

    // ------------------------------------------------------------------
    // DONNEES ENVOYEES A L'API
    // ------------------------------------------------------------------

    return {
      activity:
        selectedActivity.id,

      // Sous-composante récupérée automatiquement depuis l'activité.
      program_node:
        selectedActivity.program_node ||
        null,

      expense_category:
        values.expense_category ||
        null,

      funding_source:
        values.funding_source ||
        null,

      fiscal_year:
        fiscalYear,

      amount:
        values.amount,

      note:
        values.note ||
        "",
    };
  };

  // ====================================================================
  // PAGE
  // ====================================================================

  return (
    <ListPage
      title="Programmation financière"
      resourceName="budgetLines"
      canManage={
        hasCapability(
          "financialtransaction.create"
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
          field: "fiscal_year",
          header: "Exercice",
        },

        {
          field: "expense_category",
          header:
            t(
              "finance.category"
            ),

          body: (row) => {
            if (
              row.expense_category_name
            ) {
              return row.expense_category_name;
            }

            return catLabel(
              row.expense_category
            );
          },
        },

        {
          field: "funding_source",
          header:
            "Source de financement",

          body: (row) => {
            if (
              row.funding_source_name
            ) {
              return row.funding_source_name;
            }

            return fundLabel(
              row.funding_source
            );
          },
        },

        {
          field: "amount",
          header:
            "Montant programmé",
        },

        {
          field: "note",
          header:
            "Observation",
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
          required: true,
          full: true,
        },

        {
          name: "fiscal_year",
          label: "Exercice",
          type: "text",
          required: true,
          placeholder: "Ex. 2026",
        },

        {
          name: "expense_category",
          label:
            t(
              "finance.category"
            ),
          type: "dropdown",
          options: catOpts,
        },

        {
          name: "funding_source",
          label:
            "Source de financement",
          type: "dropdown",
          options: fundOpts,
        },

        {
          name: "amount",
          label:
            "Montant programmé",
          type: "number",
          required: true,
        },

        {
          name: "note",
          label:
            "Observation",
          type: "text",
          full: true,
        },
      ]}
    />
  );
}