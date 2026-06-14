import { useTranslation } from "react-i18next";

import ListPage from "../../components/ListPage.jsx";
import { useAuth } from "../../auth/AuthProvider.jsx";
import { useList } from "../../services/hooks.js";

export default function Budget() {
  const { t } = useTranslation();
  const { hasCapability } = useAuth();
  const cats = useList("expenseCategories", { page_size: 200 });
  const nodes = useList("programNodes", { page_size: 200 });
  const funds = useList("fundingSources", { page_size: 200 });

  const catOpts = (cats.data?.results || []).map((c) => ({ label: `${c.code} — ${c.name}`, value: c.id }));
  const nodeOpts = (nodes.data?.results || []).map((n) => ({ label: `${n.code} — ${n.name}`, value: n.id }));
  const fundOpts = (funds.data?.results || []).map((f) => ({ label: f.name, value: f.id }));
  const catLabel = (id) => catOpts.find((o) => o.value === id)?.label || "—";

  return (
    <ListPage
      title={t("nav.budget")}
      resourceName="budgetLines"
      canManage={hasCapability("financialtransaction.create")}
      columns={[
        { field: "fiscal_year", header: t("finance.fiscal_year") },
        { field: "expense_category", header: t("finance.category"), body: (r) => catLabel(r.expense_category) },
        { field: "amount", header: t("finance.amount") },
        { field: "note", header: "Note" },
      ]}
      fields={[
        { name: "fiscal_year", label: t("finance.fiscal_year"), type: "number" },
        { name: "expense_category", label: t("finance.category"), type: "dropdown", options: catOpts },
        { name: "program_node", label: t("nav.program"), type: "dropdown", options: nodeOpts },
        { name: "funding_source", label: "Source", type: "dropdown", options: fundOpts },
        { name: "amount", label: t("finance.amount"), type: "number", required: true },
        { name: "note", label: "Note", type: "text", full: true },
      ]}
    />
  );
}
