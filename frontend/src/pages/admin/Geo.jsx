import { TabPanel, TabView } from "primereact/tabview";
import { useTranslation } from "react-i18next";

import ListPage from "../../components/ListPage.jsx";
import { useAuth } from "../../auth/AuthProvider.jsx";
import { useList } from "../../services/hooks.js";

export default function Geo() {
  const { t } = useTranslation();
  const { hasCapability } = useAuth();
  const canManage = hasCapability("config.manage");
  const levels = useList("geoLevels", { page_size: 50 });
  const units = useList("geoUnits", { page_size: 1000 });

  const levelOpts = (levels.data?.results || []).map((l) => ({ label: `${l.rank} — ${l.name}`, value: l.id }));
  const unitOpts = (units.data?.results || []).map((u) => ({ label: u.name, value: u.id }));
  const levelLabel = (id) => levelOpts.find((o) => o.value === id)?.label || "—";

  return (
    <div>
      <h3 className="mb-3">{t("nav.geo")}</h3>
      <TabView>
        <TabPanel header="Niveaux">
          <ListPage
            title="Niveaux géographiques"
            resourceName="geoLevels"
            canManage={canManage}
            columns={[
              { field: "rank", header: "Rang" },
              { field: "name", header: t("common.name") },
              { field: "code", header: t("common.code") },
            ]}
            fields={[
              { name: "name", label: t("common.name"), type: "text", required: true },
              { name: "name_plural", label: "Pluriel", type: "text" },
              { name: "rank", label: "Rang", type: "number", required: true },
              { name: "code", label: t("common.code"), type: "text", required: true },
            ]}
          />
        </TabPanel>
        <TabPanel header="Unités">
          <ListPage
            title="Unités géographiques"
            resourceName="geoUnits"
            canManage={canManage}
            columns={[
              { field: "name", header: t("common.name") },
              { field: "code", header: t("common.code") },
              { field: "geo_level", header: "Niveau", body: (r) => levelLabel(r.geo_level) },
              { field: "population", header: "Population" },
            ]}
            fields={[
              { name: "name", label: t("common.name"), type: "text", required: true },
              { name: "code", label: t("common.code"), type: "text", required: true },
              { name: "geo_level", label: "Niveau", type: "dropdown", options: levelOpts, required: true },
              { name: "parent", label: "Parent", type: "dropdown", options: unitOpts },
              { name: "population", label: "Population", type: "number" },
            ]}
          />
        </TabPanel>
      </TabView>
    </div>
  );
}
