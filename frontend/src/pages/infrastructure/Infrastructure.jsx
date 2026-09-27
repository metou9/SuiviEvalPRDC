import { useEffect, useRef, useState } from "react";

import { Button } from "primereact/button";
import { Dialog } from "primereact/dialog";
import { FileUpload } from "primereact/fileupload";
import { Message } from "primereact/message";
import { Tag } from "primereact/tag";
import { Dropdown } from "primereact/dropdown";
import { ProgressSpinner } from "primereact/progressspinner";

import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  ArcElement,
  Tooltip,
  Legend,
} from "chart.js";
import { Bar, Doughnut } from "react-chartjs-2";

import { useQueryClient } from "@tanstack/react-query";

import ListPage from "../../components/ListPage.jsx";
import { api } from "../../services/api.js";

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  ArcElement,
  Tooltip,
  Legend
);

export default function Infrastructure() {
  const queryClient = useQueryClient();

  const fileUploadRef = useRef(null);

  const [selected, setSelected] =
    useState(null);

  const [detailVisible, setDetailVisible] =
    useState(false);

  const [importing, setImporting] =
    useState(false);

  const [importResult, setImportResult] =
    useState(null);

  const [importError, setImportError] =
    useState("");

  const [dashboard, setDashboard] = useState(null);
  const [dashboardLoading, setDashboardLoading] = useState(true);
  const [dashboardError, setDashboardError] = useState("");
  const [dashboardFilters, setDashboardFilters] = useState({
    wilaya: null,
    moughataa: null,
    commune: null,
    infrastructure_type: null,
  });


  // ================================================================
  // PROJET
  // ================================================================

  const projectId = 1;

  // ================================================================
  // DASHBOARD
  // ================================================================

  const loadDashboard = async () => {
    setDashboardLoading(true);
    setDashboardError("");

    try {
      const params = { project: projectId };

      Object.entries(dashboardFilters).forEach(([key, value]) => {
        if (value) params[key] = value;
      });

      const result = await api.infrastructures.dashboard(params);
      setDashboard(result);
    } catch (error) {
      console.error("Erreur dashboard Infrastructure :", error);
      setDashboardError(
        error?.response?.data?.detail ||
        error?.message ||
        "Impossible de charger le dashboard."
      );
    } finally {
      setDashboardLoading(false);
    }
  };

  useEffect(() => {
    loadDashboard();
  }, [
    dashboardFilters.wilaya,
    dashboardFilters.moughataa,
    dashboardFilters.commune,
    dashboardFilters.infrastructure_type,
  ]);


  // ================================================================
  // IMPORT KOBO
  // ================================================================

  const importKobo = async (event) => {
    const file =
      event.files?.[0];

    if (!file) {
      return;
    }

    setImporting(true);
    setImportResult(null);
    setImportError("");

    const formData =
      new FormData();

    formData.append(
      "file",
      file
    );

    formData.append(
      "project",
      projectId
    );

    try {
      const result =
        await api.infrastructures.importKobo(
          formData
        );

      setImportResult(
        result
      );

      /*
       * Recharge les données après l'import.
       */
      await queryClient.invalidateQueries();
      await loadDashboard();

    } catch (error) {
      console.error(
        "Erreur import Kobo :",
        error
      );

      setImportError(
        error?.response?.data?.detail ||
        error?.response?.data?.error ||
        error?.message ||
        "Erreur pendant l'import Kobo."
      );

    } finally {
      setImporting(false);

      fileUploadRef.current?.clear();
    }
  };


  // ================================================================
  // DETAIL
  // ================================================================

  const openDetail = (row) => {
    setSelected(row);
    setDetailVisible(true);
  };


  // ================================================================
  // HELPERS
  // ================================================================

  const display = (value) => {
    if (
      value === null ||
      value === undefined ||
      value === ""
    ) {
      return "—";
    }

    return value;
  };


  const yesNo = (value) => {
    if (value === true) {
      return "Oui";
    }

    if (value === false) {
      return "Non";
    }

    return "—";
  };


  // ================================================================
  // VOLETS
  // ================================================================

  const modulesBody = (row) => {
    const modules = [];

    if (row.has_rehabilitation) {
      modules.push(
        <Tag
          key="rehabilitation"
          value="Réhabilitation"
          severity="info"
        />
      );
    }

    if (row.has_maintenance) {
      modules.push(
        <Tag
          key="maintenance"
          value="Maintenance"
          severity="warning"
        />
      );
    }

    if (row.has_governance) {
      modules.push(
        <Tag
          key="governance"
          value="Gouvernance"
          severity="success"
        />
      );
    }

    if (!modules.length) {
      return "—";
    }

    return (
      <div className="d-flex gap-1 flex-wrap">
        {modules}
      </div>
    );
  };


  // ================================================================
  // BOUTON DETAIL
  // ================================================================

  const detailButton = (row) => (
    <Button
      icon="pi pi-eye"
      rounded
      text
      size="small"
      tooltip="Détail"
      tooltipOptions={{
        position: "top",
      }}
      onClick={() =>
        openDetail(row)
      }
    />
  );


  // ================================================================
  // IMPORT KOBO
  // ================================================================

  const importButton = (
    <FileUpload
      ref={fileUploadRef}

      mode="basic"

      name="file"

      accept=".xlsx"

      maxFileSize={
        50 * 1024 * 1024
      }

      customUpload

      auto

      uploadHandler={
        importKobo
      }

      chooseLabel={
        importing
          ? "Import en cours..."
          : "Importer depuis Kobo"
      }

      chooseOptions={{
        icon:
          importing
            ? "pi pi-spin pi-spinner"
            : "pi pi-upload",
      }}

      disabled={
        importing
      }
    />
  );


  // ================================================================
  // PAGE
  // ================================================================

  return (
    <div>

      {/* ========================================================== */}
      {/* RESULTAT IMPORT                                           */}
      {/* ========================================================== */}

      {importResult && (
        <div className="mb-3">

          <Message
            severity="success"
            text={
              `Import Kobo terminé : ` +
              `${importResult.created ?? 0} créé(s), ` +
              `${importResult.updated ?? 0} mis à jour, ` +
              `${importResult.ignored ?? 0} ignoré(s).`
            }
          />

          {importResult.geo_not_found_count > 0 && (
            <div className="mt-2">

              <Message
                severity="warn"
                text={
                  `${importResult.geo_not_found_count} ` +
                  `localité(s) non associée(s) au référentiel géographique.`
                }
              />

            </div>
          )}

        </div>
      )}


      {importError && (
        <div className="mb-3">

          <Message
            severity="error"
            text={
              importError
            }
          />

        </div>
      )}


      {/* ========================================================== */}
      {/* LISTE                                                     */}
      {/* ========================================================== */}

      {/* ========================================================== */}
      {/* DASHBOARD INFRASTRUCTURE                                   */}
      {/* ========================================================== */}

      <div className="mb-4">
        <div className="card mb-3">
          <div className="card-body">
            <div className="d-flex align-items-center justify-content-between flex-wrap gap-3 mb-3">
              <div>
                <h4 className="mb-1">Tableau de bord des infrastructures</h4>
                <div className="text-muted">Synthèse des données collectées depuis Kobo</div>
              </div>
              <Button
                label="Réinitialiser les filtres"
                icon="pi pi-filter-slash"
                outlined
                size="small"
                onClick={() =>
                  setDashboardFilters({
                    wilaya: null,
                    moughataa: null,
                    commune: null,
                    infrastructure_type: null,
                  })
                }
              />
            </div>

            <div className="row g-3">
              <DashboardFilter label="Wilaya" value={dashboardFilters.wilaya}
                options={dashboard?.filters?.wilayas || []} placeholder="Toutes les Wilayas"
                onChange={(value) => setDashboardFilters((p) => ({ ...p, wilaya: value, moughataa: null, commune: null }))} />
              <DashboardFilter label="Moughataa" value={dashboardFilters.moughataa}
                options={dashboard?.filters?.moughataas || []} placeholder="Toutes les Moughataas"
                onChange={(value) => setDashboardFilters((p) => ({ ...p, moughataa: value, commune: null }))} />
              <DashboardFilter label="Commune" value={dashboardFilters.commune}
                options={dashboard?.filters?.communes || []} placeholder="Toutes les communes"
                onChange={(value) => setDashboardFilters((p) => ({ ...p, commune: value }))} />
              <DashboardFilter label="Type d'infrastructure" value={dashboardFilters.infrastructure_type}
                options={dashboard?.filters?.infrastructure_types || []} placeholder="Tous les types"
                onChange={(value) => setDashboardFilters((p) => ({ ...p, infrastructure_type: value }))} />
            </div>
          </div>
        </div>

        {dashboardLoading && (
          <div className="d-flex justify-content-center align-items-center py-5">
            <ProgressSpinner style={{ width: "45px", height: "45px" }} />
          </div>
        )}

        {dashboardError && <Message severity="error" text={dashboardError} />}

        {!dashboardLoading && !dashboardError && dashboard && (
          <>
            <div className="row g-3 mb-4">
              <DashboardCard icon="pi pi-building" label="Infrastructures recensées" value={dashboard.kpis?.total ?? 0} accent="#60A5FA" soft="#EFF6FF" />
              <DashboardCard icon="pi pi-check-circle" label="Travaux achevés" value={dashboard.kpis?.works_completed ?? 0} secondary={`${dashboard.kpis?.completion_rate ?? 0}%`} accent="#65C77A" soft="#F0FDF4" />
              <DashboardCard icon="pi pi-verified" label="Infrastructures fonctionnelles" value={dashboard.kpis?.functional ?? 0} secondary={`${dashboard.kpis?.non_functional ?? 0} non fonctionnelle(s)`} accent="#67C7D7" soft="#ECFEFF" />
              <DashboardCard icon="pi pi-cog" label="Maintenance sur 12 mois" value={dashboard.kpis?.maintenance_recent ?? 0} secondary={`${dashboard.kpis?.maintenance_rate ?? 0}%`} accent="#F6A54C" soft="#FFF7ED" />
              <DashboardCard icon="pi pi-users" label="Comités fonctionnels" value={dashboard.kpis?.committees_functional ?? 0} secondary={`${dashboard.kpis?.committee_functional_rate ?? 0}%`} accent="#A78BFA" soft="#F5F3FF" />
            </div>

            <div className="row g-3 mb-4">
              <div className="col-12 col-xl-6">
                <DashboardChartCard title="Infrastructures par type">
                  <Bar data={{ labels: dashboard.charts?.by_type?.map((x) => x.infrastructure_type) || [], datasets: [{
                      label: "Nombre d'infrastructures",
                      data: dashboard.charts?.by_type?.map((x) => x.count) || [],
                      backgroundColor: ["#93C5FD", "#86D993", "#FDBA74", "#C4B5FD", "#F9A8C4", "#7DD3D8", "#FBCB77", "#A5B4FC"],
                      borderRadius: 7,
                      borderSkipped: false,
                    }] }} options={barChartOptions} />
                </DashboardChartCard>
              </div>
              <div className="col-12 col-xl-6">
                <DashboardChartCard title="Infrastructures par Wilaya">
                  <Bar data={{ labels: dashboard.charts?.by_wilaya?.map((x) => x.kobo_wilaya) || [], datasets: [{
                      label: "Nombre d'infrastructures",
                      data: dashboard.charts?.by_wilaya?.map((x) => x.count) || [],
                      backgroundColor: ["#93C5FD", "#86D993", "#FDBA74", "#C4B5FD", "#F9A8C4", "#7DD3D8"],
                      borderRadius: 7,
                      borderSkipped: false,
                    }] }} options={barChartOptions} />
                </DashboardChartCard>
              </div>
            </div>

            <div className="row g-3 mb-4">
              <div className="col-12 col-xl-6">
                <DashboardChartCard title="Volets renseignés">
                  <Bar data={{ labels: dashboard.charts?.modules?.map((x) => x.name) || [], datasets: [{
                      label: "Nombre d'infrastructures",
                      data: dashboard.charts?.modules?.map((x) => x.count) || [],
                      backgroundColor: ["#93C5FD", "#86D993", "#FDBA74"],
                      borderRadius: 7,
                      borderSkipped: false,
                    }] }} options={barChartOptions} />
                </DashboardChartCard>
              </div>
              <div className="col-12 col-xl-6">
                <DashboardChartCard title="État de fonctionnement">
                  <Doughnut data={{ labels: dashboard.charts?.functionality?.map((x) => x.name) || [], datasets: [{
                      data: dashboard.charts?.functionality?.map((x) => x.count) || [],
                      backgroundColor: ["#86D993", "#F9A8C4", "#FBCB77"],
                      borderColor: "#ffffff",
                      borderWidth: 3,
                      hoverOffset: 6,
                    }] }} options={doughnutOptions} />
                </DashboardChartCard>
              </div>
            </div>

            <div className="card mb-4" style={{ background: "linear-gradient(135deg, #FFF1F5 0%, #FFF8FA 100%)", border: "1px solid #F9A8C455", borderRadius: "12px", boxShadow: "0 3px 12px rgba(244, 114, 166, 0.08)" }}>
              <div className="card-body">
                <div className="d-flex align-items-center gap-2 mb-3" style={{ color: "#DB3E72" }}>
                  <i className="pi pi-users" />
                  <h5 className="m-0">Gouvernance et participation des femmes</h5>
                </div>
                <div className="row g-3">
                  <GovernanceValue label="Comités recensés" value={dashboard.kpis?.governance_total ?? 0} accent="#60A5FA" soft="#EFF6FF" />
                  <GovernanceValue label="Comités fonctionnels" value={dashboard.kpis?.committees_functional ?? 0} accent="#65C77A" soft="#F0FDF4" />
                  <GovernanceValue label="Comités comprenant des femmes" value={dashboard.kpis?.committees_with_women ?? 0} accent="#F472A6" soft="#FDF2F8" />
                  <GovernanceValue label="Total membres" value={dashboard.kpis?.committee_members_total ?? 0} accent="#67C7D7" soft="#ECFEFF" />
                  <GovernanceValue label="Femmes membres" value={dashboard.kpis?.committee_women_total ?? 0} accent="#A78BFA" soft="#F5F3FF" />
                  <GovernanceValue label="Participation féminine" value={`${dashboard.kpis?.women_rate ?? 0}%`} accent="#F6A54C" soft="#FFF7ED" />
                </div>
              </div>
            </div>
          </>
        )}
      </div>

      <ListPage
        title="Infrastructure"

        resourceName="infrastructures"

        canManage={false}

        extraParams={{
          project: projectId,
        }}

        headerActions={
          importButton
        }

        columns={[
          {
            field: "name",
            header: "Infrastructure",
            sortable: true,

            body: (row) =>
              display(
                row.name
              ),
          },

          {
            field:
              "infrastructure_type",

            header:
              "Type",

            sortable:
              true,

            body: (row) =>
              display(
                row.infrastructure_type
              ),
          },

          {
            field:
              "kobo_wilaya",

            header:
              "Wilaya",

            sortable:
              true,

            body: (row) =>
              display(
                row.kobo_wilaya
              ),
          },

          {
            field:
              "kobo_moughataa",

            header:
              "Moughataa",

            sortable:
              true,

            body: (row) =>
              display(
                row.kobo_moughataa
              ),
          },

          {
            field:
              "kobo_commune",

            header:
              "Commune",

            sortable:
              true,

            body: (row) =>
              display(
                row.kobo_commune
              ),
          },

          {
            field:
              "village_locality",

            header:
              "Village / Localité",

            body: (row) =>
              display(
                row.village_locality
              ),
          },

          {
            field:
              "modules",

            header:
              "Volet(s)",

            body:
              modulesBody,
          },
        ]}

        actionsBody={
          detailButton
        }
      />


      {/* ========================================================== */}
      {/* DETAIL COMPLET                                            */}
      {/* ========================================================== */}

      <Dialog
        header={
          selected?.name
            ? `Détail - ${selected.name}`
            : "Détail de l'infrastructure"
        }

        visible={
          detailVisible
        }

        modal

        maximizable

        style={{
          width: "85vw",
          maxWidth: "1200px",
        }}

        breakpoints={{
          "1200px": "90vw",
          "960px": "95vw",
          "640px": "98vw",
        }}

        onHide={() => {
          setDetailVisible(false);
          setSelected(null);
        }}
      >

        {selected && (
          <div>

            {/* ==================================================== */}
            {/* INFORMATIONS GENERALES                              */}
            {/* ==================================================== */}

            <DetailSection
              title="Informations générales"
              icon="pi pi-info-circle"
            >

              <Detail
                label="Nom / désignation de l'infrastructure"
                value={
                  selected.name
                }
              />

              <Detail
                label="Type d'infrastructure"
                value={
                  selected.infrastructure_type
                }
              />

              <Detail
                label="Autre type d'infrastructure"
                value={
                  selected.infrastructure_type_other
                }
              />

              <Detail
                label="Nom de l'enquêteur"
                value={
                  selected.enumerator_name
                }
              />

            </DetailSection>


            {/* ==================================================== */}
            {/* LOCALISATION                                       */}
            {/* ==================================================== */}

            <DetailSection
              title="Localisation"
              icon="pi pi-map-marker"
            >

              <Detail
                label="Wilaya"
                value={
                  selected.kobo_wilaya
                }
              />

              <Detail
                label="Moughataa"
                value={
                  selected.kobo_moughataa
                }
              />

              <Detail
                label="Commune"
                value={
                  selected.kobo_commune
                }
              />

              <Detail
                label="Village / Localité"
                value={
                  selected.village_locality
                }
              />

            </DetailSection>


            {/* ==================================================== */}
            {/* GPS                                                */}
            {/* ==================================================== */}

            <DetailSection
              title="Coordonnées GPS"
              icon="pi pi-map"
            >

              <Detail
                label="Latitude"
                value={
                  selected.gps_latitude
                }
              />

              <Detail
                label="Longitude"
                value={
                  selected.gps_longitude
                }
              />

              <Detail
                label="Altitude"
                value={
                  formatNumber(
                    selected.gps_altitude,
                    " m"
                  )
                }
              />

              <Detail
                label="Précision GPS"
                value={
                  formatNumber(
                    selected.gps_accuracy,
                    " m"
                  )
                }
              />

            </DetailSection>


            {/* ==================================================== */}
            {/* VOLETS                                             */}
            {/* ==================================================== */}

            <DetailSection
              title="Volets renseignés"
              icon="pi pi-list"
            >

              <Detail
                label="Réhabilitation / mise à niveau"
                value={
                  yesNo(
                    selected.has_rehabilitation
                  )
                }
              />

              <Detail
                label="Fonctionnement / maintenance"
                value={
                  yesNo(
                    selected.has_maintenance
                  )
                }
              />

              <Detail
                label="Gouvernance / participation des femmes"
                value={
                  yesNo(
                    selected.has_governance
                  )
                }
              />

            </DetailSection>


            {/* ==================================================== */}
            {/* REHABILITATION                                     */}
            {/* ==================================================== */}

            {selected.has_rehabilitation && (
              <DetailSection
                title="Réhabilitation / mise à niveau"
                icon="pi pi-building"
              >

                <Detail
                  label="Nature de l'intervention réalisée"
                  value={
                    selected.intervention_type
                  }
                />

                <Detail
                  label="Autre nature de l'intervention"
                  value={
                    selected.intervention_type_other
                  }
                />

                <Detail
                  label="Travaux achevés"
                  value={
                    yesNo(
                      selected.works_completed
                    )
                  }
                />

                <Detail
                  label="Date d'achèvement des travaux"
                  value={
                    formatDate(
                      selected.completion_date
                    )
                  }
                />

                <Detail
                  label="Infrastructure actuellement fonctionnelle"
                  value={
                    yesNo(
                      selected.rehab_functional
                    )
                  }
                />

              </DetailSection>
            )}


            {/* ==================================================== */}
            {/* MAINTENANCE                                        */}
            {/* ==================================================== */}

            {selected.has_maintenance && (
              <DetailSection
                title="Fonctionnement et maintenance"
                icon="pi pi-cog"
              >

                <Detail
                  label="Structure de gestion mise en place"
                  value={
                    yesNo(
                      selected.management_structure_exists
                    )
                  }
                />

                <Detail
                  label="Nom de la structure de gestion"
                  value={
                    selected.management_structure_name
                  }
                />

                <Detail
                  label="Infrastructure actuellement fonctionnelle"
                  value={
                    yesNo(
                      selected.maintenance_functional
                    )
                  }
                />

                <Detail
                  label="Maintenance réalisée au cours des 12 derniers mois"
                  value={
                    yesNo(
                      selected.maintenance_last_12_months
                    )
                  }
                />

              </DetailSection>
            )}


            {/* ==================================================== */}
            {/* GOUVERNANCE                                        */}
            {/* ==================================================== */}

            {selected.has_governance && (
              <DetailSection
                title="Gouvernance et participation des femmes"
                icon="pi pi-users"
              >

                <Detail
                  label="Nom de l'organe ou comité concerné"
                  value={
                    selected.committee_name
                  }
                />

                <Detail
                  label="Comité actuellement fonctionnel"
                  value={
                    yesNo(
                      selected.committee_functional
                    )
                  }
                />

                <Detail
                  label="Le comité comprend des femmes"
                  value={
                    yesNo(
                      selected.committee_has_women
                    )
                  }
                />

                <Detail
                  label="Nombre total de membres du comité"
                  value={
                    selected.committee_members_total
                  }
                />

                <Detail
                  label="Nombre de femmes membres"
                  value={
                    selected.committee_women_total
                  }
                />

                <Detail
                  label="Fonctions occupées par les femmes"
                  value={
                    formatFunctions(
                      selected.women_functions
                    )
                  }
                  fullWidth
                />

                <Detail
                  label="Autres fonctions occupées"
                  value={
                    selected.women_functions_other
                  }
                  fullWidth
                />

              </DetailSection>
            )}


            {/* ==================================================== */}
            {/* TRACABILITE KOBO                                   */}
            {/* ==================================================== */}

            <DetailSection
              title="Traçabilité Kobo"
              icon="pi pi-database"
            >

              <Detail
                label="ID Kobo"
                value={
                  selected.kobo_id
                }
              />

              <Detail
                label="UUID Kobo"
                value={
                  selected.kobo_uuid
                }
              />

              <Detail
                label="Date de soumission"
                value={
                  formatDateTime(
                    selected.kobo_submission_time
                  )
                }
              />

              <Detail
                label="Soumis par"
                value={
                  selected.kobo_submitted_by
                }
              />

            </DetailSection>

          </div>
        )}

      </Dialog>

    </div>
  );
}


// ======================================================================
// FORMAT DATE
// ======================================================================

function formatDate(value) {
  if (!value) {
    return "—";
  }

  const date =
    new Date(value);

  if (
    Number.isNaN(
      date.getTime()
    )
  ) {
    return value;
  }

  return date.toLocaleDateString(
    "fr-FR"
  );
}


// ======================================================================
// FORMAT DATE + HEURE
// ======================================================================

function formatDateTime(value) {
  if (!value) {
    return "—";
  }

  const date =
    new Date(value);

  if (
    Number.isNaN(
      date.getTime()
    )
  ) {
    return value;
  }

  return date.toLocaleString(
    "fr-FR"
  );
}


// ======================================================================
// FORMAT NOMBRE
// ======================================================================

function formatNumber(
  value,
  suffix = ""
) {
  if (
    value === null ||
    value === undefined ||
    value === ""
  ) {
    return "—";
  }

  return `${value}${suffix}`;
}


// ======================================================================
// FORMAT FONCTIONS FEMMES
// ======================================================================

function formatFunctions(value) {
  if (!value) {
    return "—";
  }

  if (Array.isArray(value)) {
    if (
      value.length === 0
    ) {
      return "—";
    }

    return value.join(
      ", "
    );
  }

  if (
    typeof value === "object"
  ) {
    return Object.values(
      value
    )
      .filter(Boolean)
      .join(", ");
  }

  return String(value);
}


// ======================================================================
// SECTION DETAIL
// ======================================================================

function DetailSection({
  title,
  icon,
  children,
}) {
  return (
    <div className="mb-4">

      <div
        className="
          d-flex
          align-items-center
          gap-2
          mb-3
          pb-2
          border-bottom
        "
      >

        {icon && (
          <i
            className={icon}
            style={{
              fontSize: "1rem",
            }}
          />
        )}

        <h5 className="m-0">
          {title}
        </h5>

      </div>

      <div className="row g-3">
        {children}
      </div>

    </div>
  );
}


// ======================================================================
// CHAMP DETAIL
// ======================================================================

function Detail({
  label,
  value,
  fullWidth = false,
}) {
  const shown =
    value === null ||
    value === undefined ||
    value === ""
      ? "—"
      : value;

  return (
    <div
      className={
        fullWidth
          ? "col-12"
          : "col-12 col-md-6"
      }
    >

      <div
        className="
          border
          rounded
          p-3
          h-100
        "
      >

        <small
          className="
            text-muted
            d-block
            mb-1
          "
        >
          {label}
        </small>

        <div className="fw-medium">
          {shown}
        </div>

      </div>

    </div>
  );
}

// ======================================================================
// DASHBOARD HELPERS
// ======================================================================

const barChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { display: false } },
  scales: { y: { beginAtZero: true, ticks: { precision: 0 } } },
};

const doughnutOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { position: "bottom" } },
};

function DashboardFilter({ label, value, options, placeholder, onChange }) {
  return (
    <div className="col-12 col-md-6 col-xl-3">
      <label className="form-label">{label}</label>
      <Dropdown
        value={value}
        options={options}
        placeholder={placeholder}
        showClear
        filter
        className="w-100"
        onChange={(e) => onChange(e.value)}
      />
    </div>
  );
}

function DashboardCard({
  icon,
  label,
  value,
  secondary,
  accent = "#2563eb",
  soft = "#eff6ff",
}) {
  return (
    <div className="col-12 col-md-6 col-xl">
      <div
        className="card h-100"
        style={{
          border: `1px solid ${accent}45`,
          background: `linear-gradient(135deg, ${soft} 0%, #ffffff 100%)`,
          boxShadow: "0 3px 12px rgba(15, 23, 42, 0.05)",
          borderRadius: "12px",
        }}
      >
        <div className="card-body">
          <div className="d-flex justify-content-between align-items-start gap-3">
            <div>
              <div className="text-muted small mb-2">{label}</div>
              <div className="fs-3 fw-bold" style={{ color: accent }}>
                {value}
              </div>
              {secondary && (
                <div className="text-muted small mt-1">{secondary}</div>
              )}
            </div>

            <div
              className="rounded-circle d-flex align-items-center justify-content-center"
              style={{
                width: "46px",
                height: "46px",
                flexShrink: 0,
                color: accent,
                backgroundColor: soft,
                border: `1px solid ${accent}30`,
              }}
            >
              <i className={icon} style={{ fontSize: "1.2rem" }} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function DashboardChartCard({ title, children }) {
  return (
    <div
      className="card h-100"
      style={{
        border: "1px solid #E2E8F0",
        borderRadius: "12px",
        boxShadow: "0 3px 12px rgba(15, 23, 42, 0.045)",
      }}
    >
      <div className="card-body">
        <div className="d-flex align-items-center gap-2 mb-4">
          <span
            style={{
              width: "5px",
              height: "24px",
              borderRadius: "999px",
              backgroundColor: "#60A5FA",
              display: "inline-block",
            }}
          />
          <h5 className="m-0">{title}</h5>
        </div>
        <div style={{ position: "relative", height: "320px" }}>{children}</div>
      </div>
    </div>
  );
}

function GovernanceValue({
  label,
  value,
  accent = "#2563eb",
  soft = "#eff6ff",
}) {
  return (
    <div className="col-6 col-md-4 col-xl-2">
      <div
        className="rounded p-3 h-100 text-center"
        style={{
          background: `linear-gradient(135deg, ${soft} 0%, #ffffff 100%)`,
          border: `1px solid ${accent}35`,
          borderRadius: "10px",
          boxShadow: "0 2px 8px rgba(15, 23, 42, 0.035)",
        }}
      >
        <div className="fs-4 fw-bold mb-1" style={{ color: accent }}>
          {value}
        </div>
        <div className="small text-muted">{label}</div>
      </div>
    </div>
  );
}
