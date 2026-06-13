import { Tag } from "primereact/tag";
import { useTranslation } from "react-i18next";

const SEVERITY = {
  DRAFT: "secondary",
  SUBMITTED: "info",
  VALIDATED: "warning",
  AUDITED: "warning",
  CONSOLIDATED: "success",
  REJECTED: "danger",
};

export default function WorkflowBadge({ status }) {
  const { t } = useTranslation();
  if (!status) return null;
  return <Tag severity={SEVERITY[status] || "secondary"} value={t(`workflow.${status}`)} />;
}
