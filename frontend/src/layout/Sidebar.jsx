import { useState } from "react";
import { NavLink } from "react-router-dom";
import { useTranslation } from "react-i18next";

import { useAuth } from "../auth/AuthProvider.jsx";


const SECTIONS = [
  {
    title: null,
    items: [
      {
        to: "/home",
        key: "home",
        icon: "pi-home",
      },
      {
        to: "/dashboard",
        key: "dashboard",
        icon: "pi-chart-bar",
      },
    ],
  },

  {
    title: "settings",
    cap: "config.manage",
    items: [
      {
        to: "/admin/reference",
        key: "reference",
        icon: "pi-database",
      },
    ],
  },

  {
    title: "programming",
    items: [
      {
        to: "/activities",
        key: "technical_programming",
        icon: "pi-calendar",
      },
      {
        to: "/finance/budget",
        key: "financial_programming",
        icon: "pi-wallet",
      },
      {
        to: "/procurement/ppm",
        key: "procurement_programming",
        icon: "pi-list",
      },
    ],
  },

  {
    title: "execution",
    items: [
      {
        to: "/execution/technical",
        key: "technical_monitoring",
        icon: "pi-cog",
      },
      {
        to: "/execution/financial",
        key: "financial_monitoring",
        icon: "pi-money-bill",
      },
      {
        to: "/finance/transactions",
        key: "disbursement_monitoring",
        icon: "pi-credit-card",
      },
      {
        to: "/procurement/processes",
        key: "procurement_monitoring",
        icon: "pi-briefcase",
      },
      {
        to: "/measurements",
        key: "execution_indicators",
        icon: "pi-chart-line",
      },
      {
        to: "/execution/infrastructure",
        key: "infrastructure_works",
        icon: "pi-building",
      },
    ],
  },

  {
  title: "performance",
  items: [
    {
      to: "/indicators",
      key: "results_framework",
      icon: "pi-chart-bar",
    },
    {
      to: "/impact",
      key: "impact",
      icon: "pi-chart-line",
    },
  ],
},

  {
    title: "reports",
    cap: "users.manage",
    items: [
      {
        to: "/reports",
        key: "reports",
        icon: "pi-file-pdf",
      },
    ],
  },

  {
  title: "kobotoolbox",
  items: [
    {
      to: "/kobotoolbox",
      key: "kobotoolbox_collection_analysis_results",
      icon: "pi-database",
    },
  ],
},

  {
    title: "administration",
    cap: "users.manage",
    items: [
      {
        to: "/admin/users",
        key: "users",
        icon: "pi-users",
      },
    ],
  },

  {
    title: "archive",
    items: [
      {
        to: "/archive",
        key: "archive",
        icon: "pi-folder",
      },
    ],
  },
];


export default function Sidebar({
  className = "",
  onNavigate,
}) {
  const { t } = useTranslation();
  const { hasCapability } = useAuth();

  const [collapsed, setCollapsed] = useState(false);


  const visibleSections = SECTIONS.filter(
    (section) =>
      !section.cap ||
      hasCapability(section.cap)
  );


  return (
    <nav
      className={
        `app-sidebar ${collapsed ? "collapsed" : ""} ${className}`
      }
    >

      {/* ======================================================= */}
      {/* IDENTITÉ PLATEFORME */}
      {/* ======================================================= */}

      <div className="sidebar-brand">

        <div className="sidebar-brand-mark">
          <span>PR</span>
        </div>

        {!collapsed && (
          <div className="sidebar-brand-text">

            <span className="sidebar-brand-title">
              PRDC-VFS
            </span>

            <span className="sidebar-brand-subtitle">
              Suivi &amp; Évaluation
            </span>

          </div>
        )}

      </div>


      {/* ======================================================= */}
      {/* NAVIGATION */}
      {/* ======================================================= */}

      <div className="sidebar-navigation">

        {visibleSections.map((section, index) => (
          <div
            className="sidebar-section"
            key={index}
          >

            {section.title && !collapsed && (
              <div className="section-title">
                {t(`nav.${section.title}`)}
              </div>
            )}


            {section.items.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                onClick={onNavigate}
                title={
                  collapsed
                    ? t(`nav.${item.key}`)
                    : undefined
                }
                className={({ isActive }) =>
                  `sidebar-link${isActive ? " active" : ""}`
                }
              >

                <span className="sidebar-link-icon">
                  <i className={`pi ${item.icon}`} />
                </span>


                {!collapsed && (
                  <span className="sidebar-link-label">
                    {t(`nav.${item.key}`)}
                  </span>
                )}

              </NavLink>
            ))}

          </div>
        ))}

      </div>


      {/* ======================================================= */}
      {/* RÉDUIRE / AGRANDIR */}
      {/* ======================================================= */}

      <div className="sidebar-collapse-container">

        <button
          type="button"
          className="sidebar-collapse-button"
          onClick={() => setCollapsed((value) => !value)}
          title={
            collapsed
              ? "Agrandir le menu"
              : "Réduire le menu"
          }
        >

          <i
            className={
              collapsed
                ? "pi pi-angle-right"
                : "pi pi-angle-left"
            }
          />

          {!collapsed && (
            <span>
              Réduire
            </span>
          )}

        </button>

      </div>

    </nav>
  );
}