import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";

import KpiCard from "../components/KpiCard.jsx";
import { useAuth } from "../auth/AuthProvider.jsx";
import { api, dashboards } from "../services/api.js";


export default function Dashboard() {
  const { t } = useTranslation();
  const { me } = useAuth();
  const navigate = useNavigate();

  const [pdo, setPdo] = useState([]);

  const [stats, setStats] = useState({
    activities: 0,
    indicators: 0,
    budgetLines: 0,
    ppmItems: 0,
    subcomponents: 0,
    partners: 0,
    programmedBudget: 0,
  });

  const [loading, setLoading] = useState(true);

  const userName =
    me?.display_name ||
    me?.username ||
    "Utilisateur";


  useEffect(() => {
    const loadDashboard = async () => {
      setLoading(true);

      const [
        activitiesResult,
        indicatorsResult,
        budgetResult,
        ppmResult,
        programResult,
        partnersResult,
        pdoResult,
      ] = await Promise.allSettled([
        api.activities.list({
          page_size: 1000,
        }),

        api.indicators.list({
          page_size: 1000,
        }),

        api.budgetLines.list({
          page_size: 1000,
        }),

        api.ppmItems.list({
          page_size: 1000,
        }),

        api.programNodes.list({
          page_size: 1000,
          node_type: "SUBCOMPONENT",
          ordering: "order,code",
        }),

        api.partners.list({
          page_size: 1000,
        }),

        dashboards.indicatorProgress({
          type: "PDO",
        }),
      ]);


      const activities =
        activitiesResult.status === "fulfilled"
          ? activitiesResult.value?.results || []
          : [];

      const indicators =
        indicatorsResult.status === "fulfilled"
          ? indicatorsResult.value?.results || []
          : [];

      const budgetLines =
        budgetResult.status === "fulfilled"
          ? budgetResult.value?.results || []
          : [];

      const ppmItems =
        ppmResult.status === "fulfilled"
          ? ppmResult.value?.results || []
          : [];

      const subcomponents =
        programResult.status === "fulfilled"
          ? programResult.value?.results || []
          : [];

      const partners =
        partnersResult.status === "fulfilled"
          ? partnersResult.value?.results || []
          : [];


      const programmedBudget = activities.reduce(
        (total, activity) =>
          total + Number(activity.programmed_budget || 0),
        0
      );


      setStats({
        activities:
          activitiesResult.status === "fulfilled"
            ? activitiesResult.value?.count ?? activities.length
            : 0,

        indicators:
          indicatorsResult.status === "fulfilled"
            ? indicatorsResult.value?.count ?? indicators.length
            : 0,

        budgetLines:
          budgetResult.status === "fulfilled"
            ? budgetResult.value?.count ?? budgetLines.length
            : 0,

        ppmItems:
          ppmResult.status === "fulfilled"
            ? ppmResult.value?.count ?? ppmItems.length
            : 0,

        subcomponents:
          programResult.status === "fulfilled"
            ? programResult.value?.count ?? subcomponents.length
            : 0,

        partners:
          partnersResult.status === "fulfilled"
            ? partnersResult.value?.count ?? partners.length
            : 0,

        programmedBudget,
      });


      if (pdoResult.status === "fulfilled") {
        const rows = pdoResult.value || [];

        const byCode = {};

        for (const row of rows) {
          byCode[row.indicator_code] = row;
        }

        setPdo(Object.values(byCode));
      } else {
        setPdo([]);
      }

      setLoading(false);
    };

    loadDashboard();
  }, []);


  const formattedBudget = useMemo(() => {
    return new Intl.NumberFormat("fr-FR", {
      maximumFractionDigits: 0,
    }).format(stats.programmedBudget);
  }, [stats.programmedBudget]);


  const overviewCards = [
    {
      label: "Activités programmées",
      value: stats.activities,
      icon: "pi-calendar",
      className: "dashboard-stat-green",
      onClick: () => navigate("/activities"),
    },

    {
      label: "Sous-composantes",
      value: stats.subcomponents,
      icon: "pi-sitemap",
      className: "dashboard-stat-blue",
      onClick: () => navigate("/admin/reference"),
    },

    {
      label: "Indicateurs",
      value: stats.indicators,
      icon: "pi-chart-line",
      className: "dashboard-stat-orange",
      onClick: () => navigate("/indicators"),
    },

    {
      label: "Responsables / Partenaires",
      value: stats.partners,
      icon: "pi-users",
      className: "dashboard-stat-purple",
      onClick: () => navigate("/admin/reference"),
    },
  ];


  const programmingCards = [
    {
      label: "Budget programmé",
      value: `${formattedBudget} MRU`,
      icon: "pi-wallet",
      description: "Montant programmé dans les activités",
      onClick: () => navigate("/activities"),
    },

    {
      label: "Lignes budgétaires",
      value: stats.budgetLines,
      icon: "pi-money-bill",
      description: "Programmation financière",
      onClick: () => navigate("/finance/budget"),
    },

    {
      label: "Marchés programmés",
      value: stats.ppmItems,
      icon: "pi-briefcase",
      description: "Plan de passation des marchés",
      onClick: () => navigate("/procurement/ppm"),
    },
  ];


  return (
    <div className="dashboard-page">

      {/* ========================================================= */}
      {/* BIENVENUE */}
      {/* ========================================================= */}

      <div className="dashboard-welcome">
        <div>
          <span className="dashboard-page-eyebrow">
            PILOTAGE DU PROJET
          </span>

          <h1>
            Bienvenue, {userName}
          </h1>

          <p>
            Vue synthétique de la programmation, de l'exécution
            et des résultats du PRDC-VFS.
          </p>
        </div>

        <div className="dashboard-welcome-project">
          <div className="dashboard-welcome-icon">
            <i className="pi pi-chart-bar" />
          </div>

          <div>
            <span>Projet courant</span>
            <strong>PRDC-VFS</strong>
            <small>Suivi &amp; Évaluation</small>
          </div>
        </div>
      </div>


      {/* ========================================================= */}
      {/* VUE D'ENSEMBLE */}
      {/* ========================================================= */}

      <section className="dashboard-section">

        <div className="dashboard-section-header">
          <div>
            <span className="dashboard-section-eyebrow">
              VUE D'ENSEMBLE
            </span>

            <h4>
              Situation générale
            </h4>
          </div>

          <div className="dashboard-section-icon">
            <i className="pi pi-th-large" />
          </div>
        </div>


        <div className="dashboard-stat-grid">

          {overviewCards.map((card) => (
            <button
              type="button"
              className={`dashboard-stat-card ${card.className}`}
              key={card.label}
              onClick={card.onClick}
            >
              <div className="dashboard-stat-icon">
                <i className={`pi ${card.icon}`} />
              </div>

              <div className="dashboard-stat-content">
                <span className="dashboard-stat-value">
                  {loading ? "…" : card.value}
                </span>

                <span className="dashboard-stat-label">
                  {card.label}
                </span>
              </div>

              <i className="pi pi-arrow-right dashboard-stat-arrow" />
            </button>
          ))}

        </div>

      </section>


      {/* ========================================================= */}
      {/* PROGRAMMATION */}
      {/* ========================================================= */}

      <section className="dashboard-section">

        <div className="dashboard-section-header">
          <div>
            <span className="dashboard-section-eyebrow">
              PROGRAMMATION
            </span>

            <h4>
              Situation de la programmation
            </h4>
          </div>

          <div className="dashboard-section-icon">
            <i className="pi pi-calendar" />
          </div>
        </div>


        <div className="dashboard-programming-grid">

          {programmingCards.map((card) => (
            <button
              type="button"
              className="dashboard-programming-card"
              key={card.label}
              onClick={card.onClick}
            >
              <div className="dashboard-programming-icon">
                <i className={`pi ${card.icon}`} />
              </div>

              <div className="dashboard-programming-content">
                <span className="dashboard-programming-label">
                  {card.label}
                </span>

                <strong>
                  {loading ? "…" : card.value}
                </strong>

                <small>
                  {card.description}
                </small>
              </div>
            </button>
          ))}

        </div>

      </section>


      {/* ========================================================= */}
      {/* INDICATEURS DE RÉSULTATS */}
      {/* ========================================================= */}

      <section className="dashboard-section">

        <div className="dashboard-section-header">
          <div>
            <span className="dashboard-section-eyebrow">
              RÉSULTATS
            </span>

            <h4>
              Indicateurs de résultats
            </h4>
          </div>

          <button
            type="button"
            className="dashboard-section-link"
            onClick={() => navigate("/indicators")}
          >
            Voir les indicateurs

            <i className="pi pi-arrow-right" />
          </button>
        </div>


        <div className="row g-3">

          {pdo.length === 0 && (
            <div className="col-12">
              <div className="dashboard-empty">
                <i className="pi pi-info-circle" />

                <span>
                  {t("common.empty")} — les indicateurs
                  seront affichés ici lorsque les mesures
                  auront été renseignées.
                </span>
              </div>
            </div>
          )}


          {pdo.map((row) => (
            <div
              className="col-12 col-md-6 col-xl-4"
              key={row.indicator_code}
            >
              <KpiCard
                title={`${row.indicator_code} — ${row.indicator_name}`}
                value={row.cumulative_value}
                target={row.target_value}
                rate={row.achievement_rate}
                rag={row.rag_status}
                unit={row.unit}
              />
            </div>
          ))}

        </div>

      </section>


      {/* ========================================================= */}
      {/* ACCÈS RAPIDES */}
      {/* ========================================================= */}

      <section className="dashboard-section">

        <div className="dashboard-section-header">
          <div>
            <span className="dashboard-section-eyebrow">
              ACCÈS RAPIDES
            </span>

            <h4>
              Modules de suivi
            </h4>
          </div>

          <div className="dashboard-section-icon">
            <i className="pi pi-bolt" />
          </div>
        </div>


        <div className="dashboard-shortcuts">

          <button
            type="button"
            onClick={() => navigate("/execution/technical")}
          >
            <i className="pi pi-cog" />
            <span>Suivi technique</span>
          </button>

          <button
            type="button"
            onClick={() => navigate("/execution/financial")}
          >
            <i className="pi pi-money-bill" />
            <span>Suivi financier</span>
          </button>

          <button
            type="button"
            onClick={() => navigate("/finance/transactions")}
          >
            <i className="pi pi-credit-card" />
            <span>Décaissements</span>
          </button>

          <button
            type="button"
            onClick={() => navigate("/procurement/processes")}
          >
            <i className="pi pi-briefcase" />
            <span>Suivi des marchés</span>
          </button>

          <button
            type="button"
            onClick={() => navigate("/measurements")}
          >
            <i className="pi pi-chart-line" />
            <span>Indicateurs d'exécution</span>
          </button>

          <button
            type="button"
            onClick={() => navigate("/reports")}
          >
            <i className="pi pi-file-pdf" />
            <span>Rapports</span>
          </button>

        </div>

      </section>

    </div>
  );
}