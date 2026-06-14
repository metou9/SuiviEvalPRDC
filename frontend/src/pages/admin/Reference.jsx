import { TabPanel, TabView } from "primereact/tabview";
import { useTranslation } from "react-i18next";

import ListPage from "../../components/ListPage.jsx";
import { useAuth } from "../../auth/AuthProvider.jsx";

export default function Reference() {
  const { t } = useTranslation();
  const { hasCapability } = useAuth();
  const canManage = hasCapability("config.manage");
  const codeName = [
    { field: "code", header: t("common.code") },
    { field: "name", header: t("common.name") },
  ];
  const codeNameFields = [
    { name: "code", label: t("common.code"), type: "text", required: true },
    { name: "name", label: t("common.name"), type: "text", required: true },
  ];

  return (
    <div>
      <h3 className="mb-3">{t("nav.reference")}</h3>
      <TabView>
        <TabPanel header="Catégories de dépense">
          <ListPage title="Catégories de dépense" resourceName="expenseCategories" canManage={canManage} columns={codeName} fields={codeNameFields} />
        </TabPanel>
        <TabPanel header="Sources de financement">
          <ListPage title="Sources de financement" resourceName="fundingSources" canManage={canManage} columns={codeName} fields={codeNameFields} />
        </TabPanel>
        <TabPanel header="Méthodes de passation">
          <ListPage title="Méthodes de passation" resourceName="procurementMethods" canManage={canManage} columns={codeName} fields={codeNameFields} />
        </TabPanel>
        <TabPanel header="Étapes de passation">
          <ListPage
            title="Étapes de passation"
            resourceName="procurementStages"
            canManage={canManage}
            columns={[...codeName, { field: "order", header: "Ordre" }]}
            fields={[...codeNameFields, { name: "order", label: "Ordre", type: "number" }]}
          />
        </TabPanel>
        <TabPanel header="Types de plaintes">
          <ListPage title="Types de plaintes" resourceName="grievanceTypes" canManage={canManage} columns={codeName} fields={codeNameFields} />
        </TabPanel>
        <TabPanel header="Jalons">
          <ListPage
            title="Jalons"
            resourceName="milestones"
            canManage={canManage}
            columns={[...codeName, { field: "target_date", header: "Date" }]}
            fields={[...codeNameFields, { name: "target_date", label: "Date", type: "date" }, { name: "order", label: "Ordre", type: "number" }]}
          />
        </TabPanel>
      </TabView>
    </div>
  );
}
