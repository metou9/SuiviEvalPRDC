import { useState } from "react";
import { Button } from "primereact/button";
import { Menu } from "primereact/menu";
import { Sidebar as PrSidebar } from "primereact/sidebar";
import { useRef } from "react";
import { Outlet, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";

import { useAuth } from "../auth/AuthProvider.jsx";
import LanguageSwitcher from "./LanguageSwitcher.jsx";
import ProjectSwitcher from "./ProjectSwitcher.jsx";
import Sidebar from "./Sidebar.jsx";

export default function AppShell() {
  const { t } = useTranslation();
  const { me, logout } = useAuth();
  const navigate = useNavigate();
  const [drawer, setDrawer] = useState(false);
  const userMenu = useRef(null);

  return (
    <div className="app-shell">
      <Sidebar className="desktop" />
      <PrSidebar visible={drawer} onHide={() => setDrawer(false)}>
        <Sidebar onNavigate={() => setDrawer(false)} />
      </PrSidebar>

      <div className="app-main">
        <div className="app-topbar">
          <Button
            icon="pi pi-bars"
            text
            className="d-md-none"
            onClick={() => setDrawer(true)}
          />
          <ProjectSwitcher />
          <div className="spacer" />
          <LanguageSwitcher />
          <Button
            icon="pi pi-user"
            rounded
            text
            onClick={(e) => userMenu.current.toggle(e)}
            aria-label="user"
          />
          <Menu
            popup
            ref={userMenu}
            model={[
              { label: me?.display_name, disabled: true },
              { label: t("nav.profile"), icon: "pi pi-id-card", command: () => navigate("/profile") },
              { separator: true },
              { label: t("auth.logout"), icon: "pi pi-sign-out", command: logout },
            ]}
          />
        </div>
        <div className="app-content">
          <Outlet />
        </div>
      </div>
    </div>
  );
}
