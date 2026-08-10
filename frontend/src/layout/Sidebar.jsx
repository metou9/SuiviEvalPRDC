import { NavLink } from "react-router-dom";
import { useTranslation } from "react-i18next";

import { useAuth } from "../auth/AuthProvider.jsx";

const SECTIONS = [
  {
    title: null,
    items: [
      { to: "/dashboard", key: "dashboard", icon: "pi-chart-bar" },
    ],
  },
  {
    title: "settings_custom",
    label: "Paramétrage",
    cap: "config.manage",
    items: [
      { to: "/admin/reference", key: "reference", icon: "pi-database" },
      { to: "/admin/program", key: "program", icon: "pi-sitemap" },
      { to: "/admin/indicators", key: "indicators_config", icon: "pi-sliders-h" },
    ],
  },
  {
    title: "programming_custom",
    label: "Programmation",
    items: [
      { to: "/activities", key: "activities", icon: "pi-calendar" },
      { to: "/finance/budget", key: "budget", icon: "pi-wallet" },
      { to: "/procurement/ppm", key: "ppm", icon: "pi-list" },
    ],
  },
  {
    title: "execution_custom",
    label: "Exécution",
    items: [
      { to: "/execution/technical", key: "technical_execution", icon: "pi-cog" },
      { to: "/execution/financial", key: "financial_execution", icon: "pi-money-bill" },
    ],
  },
  {
    title: "reports",
    items: [
      { to: "/reports", key: "reports", icon: "pi-file-pdf" },
    ],
  },
  {
    title: "results_custom",
    label: "Suivi des résultats",
    items: [
      { to: "/indicators", key: "indicators", icon: "pi-sitemap" },
      { to: "/measurements", key: "measurements", icon: "pi-pencil" },
    ],
  },
  {
    title: "archive_custom",
    label: "Archivage",
    items: [
      { to: "/archive", key: "archive", icon: "pi-folder" },
    ],
  },
  {
    title: "admin",
    cap: "users.manage",
    items: [
      { to: "/admin/users", key: "users", icon: "pi-users" },
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
              {s.label || t(`nav.${s.title}`)}
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