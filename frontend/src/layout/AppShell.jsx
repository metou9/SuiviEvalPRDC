import { useRef, useState } from "react";
import { Button } from "primereact/button";
import { Menu } from "primereact/menu";
import { Sidebar as PrSidebar } from "primereact/sidebar";
import { Outlet, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";

import { useAuth } from "../auth/AuthProvider.jsx";
import AppFooter from "../components/AppFooter.jsx";
import LanguageSwitcher from "./LanguageSwitcher.jsx";
import ProjectSwitcher from "./ProjectSwitcher.jsx";
import Sidebar from "./Sidebar.jsx";

export default function AppShell() {
  const { t } = useTranslation();
  const { me, logout } = useAuth();
  const navigate = useNavigate();

  const [drawer, setDrawer] = useState(false);
  const userMenu = useRef(null);

  const userMenuItems = [
    {
      label: me?.display_name || me?.username || "",
      disabled: true,
    },
    {
      label: t("nav.profile"),
      icon: "pi pi-id-card",
      command: () => navigate("/profile"),
    },
    {
      separator: true,
    },
    {
      label: t("auth.logout"),
      icon: "pi pi-sign-out",
      command: logout,
    },
  ];

  return (
    <div className="app-shell">
      <Sidebar className="desktop" />

      <PrSidebar
        visible={drawer}
        onHide={() => setDrawer(false)}
      >
        <Sidebar onNavigate={() => setDrawer(false)} />
      </PrSidebar>

      <div className="app-main">
        <header className="app-topbar">
          <Button
            icon="pi pi-bars"
            text
            className="d-md-none"
            onClick={() => setDrawer(true)}
            aria-label="Ouvrir le menu"
          />

          <ProjectSwitcher />

          <div className="spacer" />

          <LanguageSwitcher />

          <Button
            icon="pi pi-user"
            rounded
            text
            onClick={(event) => userMenu.current?.toggle(event)}
            aria-label="Menu utilisateur"
            aria-haspopup="true"
          />

          <Menu
            popup
            ref={userMenu}
            model={userMenuItems}
          />
        </header>

        <main className="app-content">
          <Outlet />
        </main>

        <AppFooter />
      </div>
    </div>
  );
}