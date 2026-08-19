import { useMemo, useRef, useState } from "react";
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


  const userName =
    me?.display_name ||
    me?.username ||
    "Utilisateur";


  const userRole =
    me?.role_name ||
    me?.role?.name ||
    me?.role ||
    "Utilisateur";


  const initials = useMemo(() => {
    const text = String(userName || "").trim();

    if (!text) {
      return "U";
    }

    const parts = text
      .split(/\s+/)
      .filter(Boolean);

    if (parts.length === 1) {
      return parts[0]
        .substring(0, 2)
        .toUpperCase();
    }

    return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
  }, [userName]);


  const userMenuItems = [
    {
      template: () => (
        <div className="topbar-user-menu-header">
          <div className="topbar-user-menu-avatar">
            {initials}
          </div>

          <div className="topbar-user-menu-identity">
            <strong>
              {userName}
            </strong>

            <span>
              {userRole}
            </span>
          </div>
        </div>
      ),
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
      className: "topbar-logout-item",
    },
  ];


  return (
    <div className="app-shell">

      {/* ======================================================= */}
      {/* SIDEBAR DESKTOP */}
      {/* ======================================================= */}

      <Sidebar className="desktop" />


      {/* ======================================================= */}
      {/* SIDEBAR MOBILE */}
      {/* ======================================================= */}

      <PrSidebar
        visible={drawer}
        onHide={() => setDrawer(false)}
        className="mobile-navigation-drawer"
      >
        <Sidebar
          onNavigate={() => setDrawer(false)}
        />
      </PrSidebar>


      {/* ======================================================= */}
      {/* CONTENU PRINCIPAL */}
      {/* ======================================================= */}

      <div className="app-main">

        {/* ===================================================== */}
        {/* TOPBAR */}
        {/* ===================================================== */}

        <header className="app-topbar">

          <div className="topbar-left">

            <Button
              icon="pi pi-bars"
              text
              className="d-md-none topbar-mobile-menu"
              onClick={() => setDrawer(true)}
              aria-label="Ouvrir le menu"
            />

            <ProjectSwitcher />

          </div>


          <div className="topbar-spacer" />


          <div className="topbar-actions">

            <LanguageSwitcher />


            <div className="topbar-divider" />


            <button
              type="button"
              className="topbar-user-trigger"
              onClick={(event) =>
                userMenu.current?.toggle(event)
              }
              aria-label="Menu utilisateur"
              aria-haspopup="true"
            >
              <span className="topbar-user-avatar">
                {initials}
              </span>

              <span className="topbar-user-info">
                <strong>
                  {userName}
                </strong>

                <small>
                  {userRole}
                </small>
              </span>

              <i className="pi pi-angle-down topbar-user-chevron" />
            </button>


            <Menu
              popup
              ref={userMenu}
              model={userMenuItems}
              className="topbar-user-menu"
            />

          </div>

        </header>


        {/* ===================================================== */}
        {/* PAGE */}
        {/* ===================================================== */}

        <main className="app-content">
          <Outlet />
        </main>


        {/* ===================================================== */}
        {/* FOOTER */}
        {/* ===================================================== */}

        <AppFooter />

      </div>

    </div>
  );
}