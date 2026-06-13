import { useTranslation } from "react-i18next";

import ListPage from "../../components/ListPage.jsx";
import { useAuth } from "../../auth/AuthProvider.jsx";
import { useList } from "../../services/hooks.js";

const NODE_TYPES = ["COMPONENT", "SUBCOMPONENT", "ACTION", "OTHER"];

export default function Program() {
  const { t } = useTranslation();
  const { hasCapability } = useAuth();
  const nodes = useList("programNodes", { page_size: 300 });
  const nodeOpts = (nodes.data?.results || []).map((n) => ({ label: `${n.code} — ${n.name}`, value: n.id }));

  return (
    <ListPage
      title={t("nav.program")}
      resourceName="programNodes"
      canManage={hasCapability("config.manage")}
      columns={[
        { field: "code", header: t("common.code") },
        { field: "name", header: t("common.name") },
        { field: "node_type", header: "Type" },
      ]}
      fields={[
        { name: "code", label: t("common.code"), type: "text", required: true },
        { name: "name", label: t("common.name"), type: "text", required: true, full: true },
        { name: "node_type", label: "Type", type: "dropdown", options: NODE_TYPES.map((x) => ({ label: x, value: x })) },
        { name: "parent", label: "Parent", type: "dropdown", options: nodeOpts },
        { name: "order", label: "Ordre", type: "number" },
      ]}
    />
  );
}
