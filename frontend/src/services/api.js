import http from "./http.js";

// Generic CRUD + workflow resource bound to an /api/v1/<path>/ endpoint.
export function resource(path) {
  const base = `/${path}/`;

  return {
    list: (params) =>
      http
        .get(base, { params })
        .then((r) => r.data),

    get: (id, params) =>
      http
        .get(`${base}${id}/`, { params })
        .then((r) => r.data),

    create: (body) =>
      http
        .post(base, body)
        .then((r) => r.data),

    update: (id, body) =>
      http
        .patch(`${base}${id}/`, body)
        .then((r) => r.data),

    remove: (id) =>
      http
        .delete(`${base}${id}/`)
        .then((r) => r.data),

    transition: (
      id,
      action,
      comment = ""
    ) =>
      http
        .post(
          `${base}${id}/${action}/`,
          { comment }
        )
        .then((r) => r.data),

    history: (id) =>
      http
        .get(`${base}${id}/history/`)
        .then((r) => r.data),

    action: (
      id,
      name,
      body = {}
    ) =>
      http
        .post(
          `${base}${id}/${name}/`,
          body
        )
        .then((r) => r.data),

    exportXlsxUrl: (params) => {
      const qs =
        new URLSearchParams({
          ...params,
          format: "xlsx",
        }).toString();

      return `${
        import.meta.env.VITE_API_BASE_URL ||
        "/api/v1"
      }/${path}/?${qs}`;
    },
  };
}


export const api = {

  // ================================================================
  // PROJETS
  // ================================================================

  projects: resource("projects"),
  milestones: resource("milestones"),
  attachments: resource("attachments"),


  // ================================================================
  // UTILISATEURS / ROLES
  // ================================================================

  users: resource("users"),
  roles: resource("roles"),
  roleAssignments:
    resource("role-assignments"),


  // ================================================================
  // GEOGRAPHIE
  // ================================================================

  geoLevels:
    resource("geo-levels"),

  geoUnits:
    resource("geo-units"),


  // ================================================================
  // PROGRAMME
  // ================================================================

  programNodes:
    resource("program-nodes"),


  // ================================================================
  // INDICATEURS
  // ================================================================

  indicatorTypes:
    resource("indicator-types"),

  dimensions:
    resource("dimensions"),

  dimensionCategories:
    resource("dimension-categories"),

  indicators:
    resource("indicators"),

  indicatorTargets:
    resource("indicator-targets"),

  indicatorResponsibilities:
    resource(
      "indicator-responsibilities"
    ),

  measurements:
    resource("measurements"),


  // ================================================================
  // PROGRAMMATION / ACTIVITES / PTBA
  // ================================================================

  activities:
    resource("activities"),

  workplans:
    resource("workplans"),

  technicalPlans:
    resource("technical-plans"),

  technicalSchedules:
    resource("technical-schedules"),

  technicalExecutions:
    resource("technical-executions"),


  // ================================================================
  // INFRASTRUCTURES / KOBO
  // ================================================================

  infrastructures: {
    ...resource("infrastructures"),

    /**
     * Import d'un export Excel KoboToolbox.
     *
     * formData :
     * - file
     * - project
     */
    importKobo: (formData) =>
      http
        .post(
          "/infrastructures/import-kobo/",
          formData
        )
        .then((r) => r.data),

    /**
     * Dashboard Infrastructure.
     *
     * Exemple :
     *
     * api.infrastructures.dashboard({
     *   project: 1,
     *   wilaya: "Gorgol"
     * })
     */
    dashboard: (params = {}) =>
      http
        .get(
          "/infrastructures/dashboard/",
          {
            params,
          }
        )
        .then((r) => r.data),
  },


  // ================================================================
  // FINANCE
  // ================================================================

  expenseCategories:
    resource("expense-categories"),

  fundingSources:
    resource("funding-sources"),

  budgetLines:
    resource("budget-lines"),

  financialTransactions:
    resource(
      "financial-transactions"
    ),


  // ================================================================
  // PASSATION DES MARCHES
  // ================================================================

  procurementMethods:
    resource(
      "procurement-methods"
    ),

  procurementStages:
    resource(
      "procurement-stages"
    ),

  ppmItems:
    resource("ppm-items"),

  procurementProcesses:
    resource(
      "procurement-processes"
    ),

  stageEvents:
    resource("stage-events"),


  // ================================================================
  // RAPPORTS
  // ================================================================

  reportTemplates:
    resource("report-templates"),

  reports:
    resource("reports"),


  // ================================================================
  // PLAINTES
  // ================================================================

  grievanceTypes:
    resource("grievance-types"),


  // ================================================================
  // DONNEES DE REFERENCE
  // ================================================================

  unitsOfMeasure:
    resource("units-of-measure"),

  actors:
    resource("actors"),

  partners:
    resource("partners"),

  auditLogs:
    resource("audit-logs"),
};


// ======================================================================
// AUTHENTIFICATION
// ======================================================================

export const auth = {

  token: (
    username,
    password
  ) =>
    http
      .post(
        "/auth/token/",
        {
          username,
          password,
        }
      )
      .then((r) => r.data),

  me: () =>
    http
      .get("/auth/me/")
      .then((r) => r.data),
};


// ======================================================================
// DASHBOARDS GENERAUX
// ======================================================================

export const dashboards = {

  indicatorProgress: (params) =>
    http
      .get(
        "/dashboards/indicator-progress/",
        {
          params,
        }
      )
      .then((r) => r.data),

  financial: (params) =>
    http
      .get(
        "/dashboards/financial/",
        {
          params,
        }
      )
      .then((r) => r.data),

  procurement: (params) =>
    http
      .get(
        "/dashboards/procurement/",
        {
          params,
        }
      )
      .then((r) => r.data),
};


// ======================================================================
// METABASE
// ======================================================================

export const metabase = {

  embed: (
    dashboard,
    params = {}
  ) =>
    http
      .get(
        "/metabase/embed/",
        {
          params: {
            dashboard,
            ...params,
          },
        }
      )
      .then((r) => r.data),
};