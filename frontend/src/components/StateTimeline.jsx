import { useEffect, useState } from "react";
import { Timeline } from "primereact/timeline";
import { useTranslation } from "react-i18next";

import { api } from "../services/api.js";

export default function StateTimeline({ resourceName, id }) {
  const { t } = useTranslation();
  const [events, setEvents] = useState([]);

  useEffect(() => {
    if (id) api[resourceName].history(id).then((d) => setEvents(d.timeline || []));
  }, [resourceName, id]);

  if (!events.length) return <div className="text-muted">{t("common.empty")}</div>;

  return (
    <Timeline
      value={events}
      content={(e) => (
        <div>
          <strong>{t(`workflow.${e.action}`)}</strong> — {t(`workflow.${e.to_state}`)}
          <div style={{ fontSize: "0.8rem", color: "#64748b" }}>
            {e.actor || "?"} · {new Date(e.at).toLocaleString()}
          </div>
          {e.comment && <div style={{ fontSize: "0.85rem" }}>{e.comment}</div>}
        </div>
      )}
    />
  );
}
