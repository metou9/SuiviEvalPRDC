import { NavLink } from "react-router-dom";
import { useTranslation } from "react-i18next";

import { useAuth } from "../auth/AuthProvider.jsx";

const SECTIONS = [
  {
    title: null,
    items: [
      { to: "/dashboard", key: "dashboard", icon: "pi-chart-bar" },
      { to: "/indicators", key: "indicators", icon: "pi-sitemap" },
      { to: "/measurements", key: "measurements", icon: "pi-pencil" },
      { to: "/activities", key: "activities", icon: "pi-calendar" },
    ],
  },
  {
    title: "finance",
    items: [
      { to: "/finance/budget", key: "budget", icon: "pi-wallet" },
      { to: "/finance/transactions", key: "transactions", icon: "pi-money-bill" },
      { to: "/finance/dashboard", key: "finance_dashboard", icon: "pi-chart-line" },
    ],
  },
  {
    title: "procurement",
    items: [
      { to: "/procurement/ppm", key: "ppm", icon: "pi-list" },
      { to: "/procurement/processes", key: "processes", icon: "pi-th-large" },
      { to: "/procurement/dashboard", key: "procurement_dashboard", icon: "pi-chart-line" },
    ],
  },
  {
    title: "reports",
    items: [{ to: "/reports", key: "reports", icon: "pi-file-pdf" }],
  },
  {
    title: "config",
    cap: "config.manage",
    items: [
      { to: "/admin/geo", key: "geo", icon: "pi-map" },
      { to: "/admin/program", key: "program", icon: "pi-sitemap" },
      { to: "/admin/indicators", key: "indicators", icon: "pi-sliders-h" },
      { to: "/admin/reference", key: "reference", icon: "pi-database" },
    ],
  },
  {
    title: "admin",
    cap: "users.manage",
    items: [{ to: "/admin/users", key: "users", icon: "pi-users" }],
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
          {s.title && <div className="section-title">{t(`nav.${s.title}`)}</div>}
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
