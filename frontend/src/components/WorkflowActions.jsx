import { useState } from "react";
import { Button } from "primereact/button";
import { Dialog } from "primereact/dialog";
import { InputTextarea } from "primereact/inputtextarea";
import { useTranslation } from "react-i18next";

import { useAuth } from "../auth/AuthProvider.jsx";
import { useTransition } from "../services/hooks.js";

// Actions allowed from each state, with the capability step they require.
const NEXT = {
  DRAFT: [["submit", "submit"]],
  SUBMITTED: [["validate", "validate"], ["reject", "validate"]],
  VALIDATED: [["audit", "audit"], ["reject", "audit"]],
  AUDITED: [["consolidate", "consolidate"], ["reject", "consolidate"]],
  REJECTED: [["reopen", "submit"]],
  CONSOLIDATED: [["reopen", "consolidate"]],
};

export default function WorkflowActions({ resourceName, area, record, onDone }) {
  const { t } = useTranslation();
  const { hasCapability } = useAuth();
  const transition = useTransition(resourceName);
  const [pending, setPending] = useState(null);
  const [comment, setComment] = useState("");

  const options = (NEXT[record.status] || []).filter(([, step]) =>
    hasCapability(`${area}.${step}`),
  );
  if (!options.length) return null;

  const run = async () => {
    await transition.mutateAsync({ id: record.id, action: pending, comment });
    setPending(null);
    setComment("");
    onDone?.();
  };

  return (
    <span className="d-inline-flex gap-2">
      {options.map(([action]) => (
        <Button
          key={action}
          size="small"
          severity={action === "reject" ? "danger" : "primary"}
          outlined
          label={t(`workflow.${action}`)}
          onClick={() => setPending(action)}
        />
      ))}
      <Dialog
        header={pending && t(`workflow.${pending}`)}
        visible={!!pending}
        style={{ width: "26rem" }}
        onHide={() => setPending(null)}
      >
        <div className="field">
          <label>{t("common.comment")}</label>
          <InputTextarea
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            rows={3}
            className="w-100"
          />
        </div>
        <div className="d-flex justify-content-end gap-2 mt-2">
          <Button label={t("common.cancel")} text onClick={() => setPending(null)} />
          <Button label={t("common.save")} loading={transition.isPending} onClick={run} />
        </div>
      </Dialog>
    </span>
  );
}
