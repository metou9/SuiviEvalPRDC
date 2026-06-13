import { TabPanel, TabView } from "primereact/tabview";
import { useTranslation } from "react-i18next";

import ListPage from "../../components/ListPage.jsx";
import { useAuth } from "../../auth/AuthProvider.jsx";
import { useList } from "../../services/hooks.js";

export default function Users() {
  const { t } = useTranslation();
  const { hasCapability } = useAuth();
  const canManage = hasCapability("users.manage");
  const users = useList("users", { page_size: 500 });
  const roles = useList("roles", { page_size: 100 });
  const geoUnits = useList("geoUnits", { page_size: 1000 });

  const userOpts = (users.data?.results || []).map((u) => ({ label: u.username, value: u.id }));
  const roleOpts = (roles.data?.results || []).map((r) => ({ label: `${r.code} — ${r.name}`, value: r.id }));
  const geoOpts = (geoUnits.data?.results || []).map((g) => ({ label: g.name, value: g.id }));
  const userLabel = (id) => userOpts.find((o) => o.value === id)?.label || id;
  const roleLabel = (id) => roleOpts.find((o) => o.value === id)?.label || id;

  return (
    <div>
      <h3 className="mb-3">{t("nav.users")}</h3>
      <TabView>
        <TabPanel header={t("nav.users")}>
          <ListPage
            title={t("nav.users")}
            resourceName="users"
            canManage={canManage}
            columns={[
              { field: "username", header: t("auth.username") },
              { field: "display_name", header: t("common.name") },
              { field: "email", header: "Email" },
            ]}
            fields={[
              { name: "username", label: t("auth.username"), type: "text", required: true },
              { name: "display_name", label: t("common.name"), type: "text" },
              { name: "email", label: "Email", type: "text" },
              { name: "password", label: t("auth.password"), type: "text" },
              { name: "default_locale", label: t("common.language"), type: "text" },
            ]}
          />
        </TabPanel>
        <TabPanel header="Affectations de rôles">
          <ListPage
            title="Affectations de rôles"
            resourceName="roleAssignments"
            canManage={canManage}
            columns={[
              { field: "user", header: "Utilisateur", body: (r) => userLabel(r.user) },
              { field: "role", header: "Rôle", body: (r) => roleLabel(r.role) },
              { field: "scope_geo", header: "Portée géo." },
            ]}
            fields={[
              { name: "user", label: "Utilisateur", type: "dropdown", options: userOpts, required: true },
              { name: "role", label: "Rôle", type: "dropdown", options: roleOpts, required: true },
              { name: "scope_geo", label: "Portée géographique", type: "dropdown", options: geoOpts },
            ]}
          />
        </TabPanel>
      </TabView>
    </div>
  );
}
