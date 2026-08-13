import { NavLink } from "react-router-dom";
import { useTranslation } from "react-i18next";

import { useAuth } from "../auth/AuthProvider.jsx";

const SECTIONS = [
  {
    title: null,
    items: [
      { to: "/home", key: "home", icon: "pi-home" },
      { to: "/dashboard", key: "dashboard", icon: "pi-chart-bar" },
    ],
  },

  {
    title: "settings",
    cap: "config.manage",
    items: [
      { to: "/admin/program", key: "program_structure", icon: "pi-sitemap" },
      { to: "/admin/reference", key: "reference", icon: "pi-database" },
      { to: "/admin/geo", key: "intervention_zone", icon: "pi-map" },
    ],
  },

  {
    title: "programming",
    items: [
      { to: "/activities", key: "technical_programming", icon: "pi-calendar" },
      { to: "/finance/budget", key: "financial_programming", icon: "pi-wallet" },
      { to: "/procurement/ppm", key: "procurement_programming", icon: "pi-list" },
    ],
  },

  {
    title: "execution",
    items: [
      { to: "/execution/technical", key: "technical_monitoring", icon: "pi-cog" },
      { to: "/execution/financial", key: "financial_monitoring", icon: "pi-money-bill" },
      { to: "/finance/transactions", key: "disbursement_monitoring", icon: "pi-credit-card" },
      { to: "/procurement/processes", key: "procurement_monitoring", icon: "pi-briefcase" },
      { to: "/measurements", key: "execution_indicators", icon: "pi-chart-line" },
      { to: "/execution/infrastructure", key: "infrastructure_works", icon: "pi-building" },
    ],
  },

  {
    title: "results",
    items: [
      { to: "/indicators", key: "result_indicators", icon: "pi-chart-bar" },
    ],
  },

   {
    title: "reports",
    cap: "users.manage",
    items: [
      { to: "/reports", key: "reports", icon: "pi-file-pdf" },
    ],
  },

  {
    title: "local_structures",
    items: [
      { to: "/local-structures", key: "local_structures", icon: "pi-building" },
    ],
  },

  {
    title: "administration",
    cap: "users.manage",
    items: [
      { to: "/admin/users", key: "users", icon: "pi-users" },
    ],
  },

  {
    title: "archive",
    items: [
      { to: "/archive", key: "archive", icon: "pi-folder" },
    ],
  },
];

export default function Sidebar({ className = "", onNavigate }) {
  const { t } = useTranslation();
  const { hasCapability } = useAuth();

  return (
    <nav className={`app-sidebar ${className}`}>
      <div className="p-3 fw-bold" style={{ color: "#fff" }}>
        {t("app.title")}
      </div>

      {SECTIONS.filter((s) => !s.cap || hasCapability(s.cap)).map((s, i) => (
        <div key={i}>
          {s.title && (
            <div className="section-title">
              {t(`nav.${s.title}`)}
            </div>
          )}

          {s.items.map((it) => (
            <NavLink key={it.to} to={it.to} onClick={onNavigate}>
              <i className={`pi ${it.icon} me-2`} />
              {t(`nav.${it.key}`)}
            </NavLink>
          ))}
        </div>
      ))}
    </nav>
  );
}