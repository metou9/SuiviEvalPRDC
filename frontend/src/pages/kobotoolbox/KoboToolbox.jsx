import { useNavigate } from "react-router-dom";

export default function KoboToolbox() {
  const navigate = useNavigate();

  const questionnaires = [
    {
      title: "Gestion des plaintes (MGP)",
      description:
        "Suivi et traitement des plaintes et réclamations communautaires dans le cadre du Mécanisme de Gestion des Plaintes (MGP).",
      icon: "pi-comments",
      background: "#EFF8FF",
      iconColor: "#3B82F6",
      route: "/kobotoolbox/mgp",
    },
    {
      title: "Interconnexion transfrontalière",
      description:
        "Suivi des impacts et des bénéfices liés aux activités d’interconnexion transfrontalière.",
      icon: "pi-share-alt",
      background: "#EFFBF4",
      iconColor: "#22A06B",
      route: "/kobotoolbox/interconnection",
    },
    {
      title: "Activités de cohésion sociale",
      description:
        "Suivi des activités de cohésion sociale, de la participation communautaire et de leurs résultats.",
      icon: "pi-users",
      background: "#FFF8E8",
      iconColor: "#F59E0B",
      route: "/kobotoolbox/social-cohesion",
    },
  ];

  return (
    <div
      style={{
        padding: "1.5rem",
        maxWidth: "1500px",
        margin: "0 auto",
      }}
    >
      {/* En-tête */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "1rem",
          marginBottom: "1.75rem",
        }}
      >
        <div
          style={{
            width: "54px",
            height: "54px",
            borderRadius: "14px",
            background: "#E8F2FF",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <i
            className="pi pi-database"
            style={{
              fontSize: "1.6rem",
              color: "#5B9FE8",
            }}
          />
        </div>

        <div>
          <h2
            style={{
              margin: 0,
              color: "#14213D",
              fontSize: "1.8rem",
              fontWeight: 700,
            }}
          >
            KoboToolbox
          </h2>

          <div
            style={{
              marginTop: "0.25rem",
              color: "#64748B",
              fontSize: "1.05rem",
            }}
          >
            Collecte – Analyse – Résultats
          </div>
        </div>
      </div>

      {/* Conteneur principal */}
      <div
        style={{
          background: "#FFFFFF",
          border: "1px solid #E5E7EB",
          borderRadius: "16px",
          padding: "1.5rem",
          boxShadow: "0 2px 8px rgba(15, 23, 42, 0.04)",
        }}
      >
        <div style={{ marginBottom: "1.5rem" }}>
          <h3
            style={{
              margin: "0 0 0.45rem",
              color: "#1E293B",
              fontSize: "1.25rem",
            }}
          >
            Gestion des données KoboToolbox
          </h3>

          <p
            style={{
              margin: 0,
              color: "#64748B",
              lineHeight: 1.6,
            }}
          >
            Cette section permet de collecter, analyser et consulter les
            résultats des données issues des trois questionnaires KoboToolbox
            utilisés dans le projet.
          </p>
        </div>

        {/* Cartes */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
            gap: "1rem",
          }}
        >
          {questionnaires.map((questionnaire) => (
            <div
              key={questionnaire.route}
              style={{
                border: "1px solid #E2E8F0",
                borderRadius: "14px",
                overflow: "hidden",
                background: "#FFFFFF",
                display: "flex",
                flexDirection: "column",
                minHeight: "470px",
              }}
            >
              {/* Partie colorée */}
              <div
                style={{
                  background: questionnaire.background,
                  padding: "1.75rem 1.4rem",
                  textAlign: "center",
                  minHeight: "230px",
                }}
              >
                <div
                  style={{
                    width: "62px",
                    height: "62px",
                    margin: "0 auto 1rem",
                    borderRadius: "50%",
                    background: "#FFFFFF",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    boxShadow: "0 3px 10px rgba(15,23,42,0.08)",
                  }}
                >
                  <i
                    className={`pi ${questionnaire.icon}`}
                    style={{
                      fontSize: "1.8rem",
                      color: questionnaire.iconColor,
                    }}
                  />
                </div>

                <h3
                  style={{
                    margin: "0 0 0.85rem",
                    color: "#14213D",
                    fontSize: "1.15rem",
                    lineHeight: 1.35,
                  }}
                >
                  {questionnaire.title}
                </h3>

                <p
                  style={{
                    margin: 0,
                    color: "#64748B",
                    lineHeight: 1.55,
                    fontSize: "0.94rem",
                  }}
                >
                  {questionnaire.description}
                </p>
              </div>

              {/* Fonctionnalités */}
              <div
                style={{
                  padding: "1.25rem",
                  flex: 1,
                  display: "flex",
                  flexDirection: "column",
                }}
              >
                <div style={{ flex: 1 }}>
                  <Feature
                    icon="pi-file-import"
                    label="Collecte des données"
                  />

                  <Feature
                    icon="pi-chart-bar"
                    label="Analyse des données"
                  />

                  <Feature
                    icon="pi-chart-pie"
                    label="Résultats"
                  />
                </div>

                <button
                  type="button"
                  onClick={() => navigate(questionnaire.route)}
                  style={{
                    width: "100%",
                    border: "1px solid #5B9FE8",
                    borderRadius: "8px",
                    background: "#5B9FE8",
                    color: "#FFFFFF",
                    padding: "0.85rem 1rem",
                    fontWeight: 600,
                    fontSize: "0.95rem",
                    cursor: "pointer",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    gap: "0.7rem",
                    boxShadow: "0 2px 5px rgba(91, 159, 232, 0.15)",
                  }}
                >
                  Accéder
                  <i className="pi pi-arrow-right" />
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}


function Feature({ icon, label }) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: "0.8rem",
        padding: "0.65rem 0",
        color: "#475569",
      }}
    >
      <i
        className={`pi ${icon}`}
        style={{
          width: "22px",
          color: "#64748B",
        }}
      />

      <span>{label}</span>
    </div>
  );
}