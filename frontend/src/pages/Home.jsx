import { useNavigate } from "react-router-dom";

import { useAuth } from "../auth/AuthProvider.jsx";

export default function Home() {
  const { me } = useAuth();
  const navigate = useNavigate();

  const userName =
    me?.display_name ||
    me?.username ||
    "Utilisateur";

  return (
    <div className="home-dashboard">
      <div className="home-hero">
        <div className="home-hero-content">
          <span className="home-eyebrow">
            ESPACE DE PILOTAGE
          </span>

          <h1>
            Bienvenue, {userName}
          </h1>

          <p>
            Suivez la programmation, l'exécution et les résultats
            du PRDC-VFS depuis un espace unique.
          </p>

          <div className="home-actions">
            <button
              type="button"
              className="home-primary-action"
              onClick={() => navigate("/dashboard")}
            >
              <i className="pi pi-chart-bar" />
              Voir le tableau de bord
            </button>

            <button
              type="button"
              className="home-secondary-action"
              onClick={() => navigate("/activities")}
            >
              <i className="pi pi-calendar" />
              Programmation technique
            </button>
          </div>
        </div>

        <div className="home-project-card">
          <div className="home-project-icon">
            <i className="pi pi-chart-line" />
          </div>

          <div>
            <span>Projet courant</span>
            <strong>PRDC-VFS</strong>
            <small>
              Plateforme de Suivi-Évaluation
            </small>
          </div>
        </div>
      </div>

      <div className="home-module-grid">
        <button
          type="button"
          onClick={() => navigate("/activities")}
        >
          <div className="home-module-icon">
            <i className="pi pi-calendar" />
          </div>

          <strong>Programmation</strong>

          <span>
            Activités, programmation financière et marchés
          </span>

          <i className="pi pi-arrow-right" />
        </button>

        <button
          type="button"
          onClick={() => navigate("/execution/technical")}
        >
          <div className="home-module-icon">
            <i className="pi pi-cog" />
          </div>

          <strong>Exécution</strong>

          <span>
            Suivi technique, financier et décaissements
          </span>

          <i className="pi pi-arrow-right" />
        </button>

        <button
          type="button"
          onClick={() => navigate("/indicators")}
        >
          <div className="home-module-icon">
            <i className="pi pi-chart-line" />
          </div>

          <strong>Résultats</strong>

          <span>
            Suivi des indicateurs et performances
          </span>

          <i className="pi pi-arrow-right" />
        </button>

        <button
          type="button"
          onClick={() => navigate("/reports")}
        >
          <div className="home-module-icon">
            <i className="pi pi-file-pdf" />
          </div>

          <strong>Rapports</strong>

          <span>
            Consultation et édition des rapports
          </span>

          <i className="pi pi-arrow-right" />
        </button>
      </div>

      <section className="home-about">
        <div className="home-about-header">
          <span>PRDC-VFS</span>
          <h2>Suivi intégré du projet</h2>
        </div>

        <p>
          La plateforme centralise les données nécessaires au pilotage
          du projet : programmation des activités, suivi de leur
          exécution, gestion financière, passation des marchés et suivi
          des indicateurs de résultats.
        </p>
      </section>
    </div>
  );
}