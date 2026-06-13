import { useTranslation } from "react-i18next";

import ListPage from "../../components/ListPage.jsx";
import { useAuth } from "../../auth/AuthProvider.jsx";
import { useList } from "../../services/hooks.js";

export default function Ppm() {
  const { t } = useTranslation();
  const { hasCapability } = useAuth();
  const methods = useList("procurementMethods", { page_size: 200 });
  const cats = useList("expenseCategories", { page_size: 200 });
  const methodOpts = (methods.data?.results || []).map((m) => ({ label: `${m.code} — ${m.name}`, value: m.id }));
  const catOpts = (cats.data?.results || []).map((c) => ({ label: `${c.code} — ${c.name}`, value: c.id }));
  const methodLabel = (id) => methodOpts.find((o) => o.value === id)?.label || "—";

  return (
    <ListPage
      title={t("nav.ppm")}
      resourceName="ppmItems"
      canManage={hasCapability("procurementprocess.create")}
      columns={[
        { field: "ppm_ref", header: "Réf" },
        { field: "designation", header: t("procurement.designation") },
        { field: "procurement_method", header: t("procurement.method"), body: (r) => methodLabel(r.procurement_method) },
        { field: "planned_amount", header: t("procurement.planned") },
        { field: "planned_year", header: t("common.year") },
      ]}
      fields={[
        { name: "ppm_ref", label: "Réf PPM", type: "text" },
        { name: "designation", label: t("procurement.designation"), type: "text", required: true, full: true },
        { name: "procurement_method", label: t("procurement.method"), type: "dropdown", options: methodOpts },
        { name: "expense_category", label: t("finance.category"), type: "dropdown", options: catOpts },
        { name: "planned_amount", label: t("procurement.planned"), type: "number" },
        { name: "planned_year", label: t("common.year"), type: "number" },
      ]}
    />
  );
}
