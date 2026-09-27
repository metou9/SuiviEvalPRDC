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

  const programNodes = useList("programNodes", {
    page_size: 1000,
    ordering: "order,code",
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

  const programNodeRecords =
    programNodes.data?.results ||
    programNodes.data ||
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
  // COMPOSANTES
  // ====================================================================

  const componentRecords = useMemo(
    () =>
      programNodeRecords.filter(
        (node) => node.node_type === "COMPONENT"
      ),
    [programNodeRecords]
  );

  const componentOpts = useMemo(
    () =>
      componentRecords.map((node) => ({
        label: node.code
          ? `${node.code} — ${node.name}`
          : node.name,
        value: node.id,
      })),
    [componentRecords]
  );

  // ====================================================================
  // SOUS-COMPOSANTES SELON LA COMPOSANTE
  // ====================================================================

  const getSubcomponentOpts = (values) => {
    if (!values.component) {
      return [];
    }

    return programNodeRecords
      .filter(
        (node) =>
          node.node_type === "SUBCOMPONENT" &&
          Number(node.parent) === Number(values.component)
      )
      .map((node) => ({
        label: node.code
          ? `${node.code} — ${node.name}`
          : node.name,
        value: node.id,
      }));
  };

  // ====================================================================
  // ACTIVITES SELON LA SOUS-COMPOSANTE
  // ====================================================================

  const getActivityOpts = (values) => {
    if (!values.program_node) {
      return [];
    }

    return activityRecords
      .filter(
        (activity) =>
          Number(activity.program_node) ===
          Number(values.program_node)
      )
      .map((activity) => ({
        label: activity.code
          ? `${activity.code} — ${activity.title}`
          : activity.title,
        value: activity.id,
      }));
  };

  // ====================================================================
  // OPTIONS ACTIVITES (AFFICHAGE TABLEAU)
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
    if (!id) return "—";

    return (
      activityOpts.find(
        (option) =>
          Number(option.value) === Number(id)
      )?.label || "—"
    );
  };

  const catLabel = (id) => {
    if (!id) return "—";

    return (
      catOpts.find(
        (option) =>
          Number(option.value) === Number(id)
      )?.label || "—"
    );
  };

  const fundLabel = (id) => {
    if (!id) return "—";

    return (
      fundOpts.find(
        (option) =>
          Number(option.value) === Number(id)
      )?.label || "—"
    );
  };

  // ====================================================================
  // PREPARATION POUR MODIFICATION
  // ====================================================================

  const toForm = (row) => {
    const selectedActivity =
      activityRecords.find(
        (activity) =>
          Number(activity.id) === Number(row.activity)
      );

    const subcomponentId =
      selectedActivity?.program_node ||
      row.program_node ||
      null;

    const selectedSubcomponent =
      programNodeRecords.find(
        (node) =>
          Number(node.id) === Number(subcomponentId)
      );

    return {
      ...row,
      component:
        selectedSubcomponent?.parent ||
        row.component_id ||
        null,
      program_node: subcomponentId,
    };
  };

  // ====================================================================
  // PREPARATION AVANT ENREGISTREMENT
  // ====================================================================

  const fromForm = (values) => {
    const selectedActivity =
      activityRecords.find(
        (activity) =>
          Number(activity.id) === Number(values.activity)
      );

    if (!values.component) {
      throw new Error(
        "Veuillez sélectionner une composante."
      );
    }

    if (!values.program_node) {
      throw new Error(
        "Veuillez sélectionner une sous-composante."
      );
    }

    if (!selectedActivity) {
      throw new Error(
        "Veuillez sélectionner une activité."
      );
    }

    if (
      Number(selectedActivity.program_node) !==
      Number(values.program_node)
    ) {
      throw new Error(
        "L'activité sélectionnée n'appartient pas à la sous-composante choisie."
      );
    }

    const selectedSubcomponent =
      programNodeRecords.find(
        (node) =>
          Number(node.id) === Number(values.program_node)
      );

    if (
      !selectedSubcomponent ||
      Number(selectedSubcomponent.parent) !==
        Number(values.component)
    ) {
      throw new Error(
        "La sous-composante sélectionnée n'appartient pas à la composante choisie."
      );
    }

    const exerciseText =
      String(values.fiscal_year || "").trim();

    if (!/^\d{4}$/.test(exerciseText)) {
      throw new Error(
        "L'exercice doit être une année à 4 chiffres, par exemple 2026."
      );
    }

    const fiscalYear = Number(exerciseText);

    if (
      fiscalYear < 2010 ||
      fiscalYear > 2090
    ) {
      throw new Error(
        "L'exercice doit être compris entre 2010 et 2090."
      );
    }

    if (
      values.amount === null ||
      values.amount === undefined ||
      values.amount === ""
    ) {
      throw new Error(
        "Le montant programmé est obligatoire."
      );
    }

    return {
      activity: selectedActivity.id,

      // La sous-composante est déduite de l'activité choisie.
      program_node:
        selectedActivity.program_node || null,

      expense_category:
        values.expense_category || null,

      funding_source:
        values.funding_source || null,

      fiscal_year: fiscalYear,

      amount: values.amount,

      note: values.note || "",
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

      toForm={toForm}
      fromForm={fromForm}

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

            return activityLabel(row.activity);
          },
        },

        {
          field: "fiscal_year",
          header: "Exercice",
        },

        {
          field: "expense_category",
          header: t("finance.category"),

          body: (row) => {
            if (row.expense_category_name) {
              return row.expense_category_name;
            }

            return catLabel(
              row.expense_category
            );
          },
        },

        {
          field: "funding_source",
          header: "Source de financement",

          body: (row) => {
            if (row.funding_source_name) {
              return row.funding_source_name;
            }

            return fundLabel(
              row.funding_source
            );
          },
        },

        {
          field: "amount",
          header: "Montant programmé",
        },

        {
          field: "note",
          header: "Observation",
        },
      ]}

      fields={[
        {
          name: "component",
          label: "Composante",
          type: "dropdown",
          options: componentOpts,
          required: true,
          clearOnChange: [
            "program_node",
            "activity",
          ],
          full: true,
        },

        {
          name: "program_node",
          label: "Sous-composante",
          type: "dropdown",
          options: getSubcomponentOpts,
          required: true,
          clearOnChange: [
            "activity",
          ],
          full: true,
        },

        {
          name: "activity",
          label: "Activité",
          type: "dropdown",
          options: getActivityOpts,
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
          label: t("finance.category"),
          type: "dropdown",
          options: catOpts,
        },

        {
          name: "funding_source",
          label: "Source de financement",
          type: "dropdown",
          options: fundOpts,
        },

        {
          name: "amount",
          label: "Montant programmé",
          type: "number",
          required: true,
        },

        {
          name: "note",
          label: "Observation",
          type: "text",
          full: true,
        },
      ]}
    />
  );
}
