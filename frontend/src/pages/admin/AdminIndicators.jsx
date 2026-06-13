import { TabPanel, TabView } from "primereact/tabview";
import { useTranslation } from "react-i18next";

import ListPage from "../../components/ListPage.jsx";
import { useAuth } from "../../auth/AuthProvider.jsx";
import { useList } from "../../services/hooks.js";

const UNITS = ["NUMBER", "PERCENTAGE", "CURRENCY", "RATIO", "TEXT"];
const AGG = ["SUM", "AVERAGE", "LAST", "MAX", "MIN", "MANUAL"];
const DIR = ["INCREASE", "DECREASE"];

export default function AdminIndicators() {
  const { t } = useTranslation();
  const { hasCapability } = useAuth();
  const canManage = hasCapability("config.manage");
  const types = useList("indicatorTypes", { page_size: 50 });
  const nodes = useList("programNodes", { page_size: 300 });
  const indicators = useList("indicators", { page_size: 500 });
  const milestones = useList("milestones", { page_size: 50 });

  const typeOpts = (types.data?.results || []).map((x) => ({ label: x.code, value: x.id }));
  const nodeOpts = (nodes.data?.results || []).map((n) => ({ label: `${n.code} — ${n.name}`, value: n.id }));
  const indOpts = (indicators.data?.results || []).map((i) => ({ label: `${i.code} — ${i.name}`, value: i.id }));
  const msOpts = (milestones.data?.results || []).map((m) => ({ label: m.name, value: m.id }));
  const indLabel = (id) => indOpts.find((o) => o.value === id)?.label || id;

  return (
    <div>
      <h3 className="mb-3">{t("nav.indicators")} — {t("nav.config")}</h3>
      <TabView>
        <TabPanel header="Indicateurs">
          <ListPage
            title="Indicateurs"
            resourceName="indicators"
            canManage={canManage}
            columns={[
              { field: "code", header: t("common.code") },
              { field: "name", header: t("common.name") },
              { field: "indicator_type_code", header: t("indicators.type") },
              { field: "unit", header: t("indicators.unit") },
            ]}
            fields={[
              { name: "code", label: t("common.code"), type: "text", required: true },
              { name: "name", label: t("common.name"), type: "text", required: true, full: true },
              { name: "indicator_type", label: t("indicators.type"), type: "dropdown", options: typeOpts, required: true },
              { name: "program_node", label: t("nav.program"), type: "dropdown", options: nodeOpts },
              { name: "unit", label: t("indicators.unit"), type: "dropdown", options: UNITS.map((x) => ({ label: x, value: x })) },
              { name: "direction", label: "Direction", type: "dropdown", options: DIR.map((x) => ({ label: x, value: x })) },
              { name: "aggregation_method", label: "Agrégation", type: "dropdown", options: AGG.map((x) => ({ label: x, value: x })) },
              { name: "definition", label: t("indicators.definition"), type: "textarea", full: true },
            ]}
          />
        </TabPanel>
        <TabPanel header={t("indicators.targets")}>
          <ListPage
            title={t("indicators.targets")}
            resourceName="indicatorTargets"
            canManage={canManage}
            columns={[
              { field: "indicator", header: t("measurements.indicator"), body: (r) => indLabel(r.indicator) },
              { field: "milestone_code", header: "Jalon" },
              { field: "value", header: t("common.value") },
            ]}
            fields={[
              { name: "indicator", label: t("measurements.indicator"), type: "dropdown", options: indOpts, required: true },
              { name: "milestone", label: "Jalon", type: "dropdown", options: msOpts, required: true },
              { name: "value", label: t("common.value"), type: "number", required: true },
            ]}
          />
        </TabPanel>
      </TabView>
    </div>
  );
}
