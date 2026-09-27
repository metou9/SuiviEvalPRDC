import { TabPanel, TabView } from "primereact/tabview";
import { useTranslation } from "react-i18next";

import ListPage from "../../components/ListPage.jsx";
import { useAuth } from "../../auth/AuthProvider.jsx";
import { useList } from "../../services/hooks.js";


export default function Reference() {
  const { t } = useTranslation();
  const { hasCapability } = useAuth();

  // Seuls ADMIN / Super Admin possèdent cette capacité.
  const canManage = hasCapability("reference.manage");


  // ------------------------------------------------------------------
  // Données utilisées dans les listes déroulantes
  // ------------------------------------------------------------------

  const programNodes = useList("programNodes", {
    page_size: 1000,
    node_type: "COMPONENT",
    ordering: "order,code",
  });

  const geoLevels = useList("geoLevels", {
    page_size: 1000,
    ordering: "rank",
  });

  const geoUnits = useList("geoUnits", {
    page_size: 1000,
    ordering: "geo_level__rank,name",
  });


  // ------------------------------------------------------------------
  // Options Programme
  // ------------------------------------------------------------------

  const programNodeOptions = (
    programNodes.data?.results || []
  ).map((item) => ({
    label: `${item.code} — ${item.name}`,
    value: item.id,
  }));


  const nodeTypeOptions = [
    {
      label: "Composante",
      value: "COMPONENT",
    },
    {
      label: "Sous Composante",
      value: "SUBCOMPONENT",
    },
  ];


  // ------------------------------------------------------------------
  // Affichage Type Programme
  // ------------------------------------------------------------------

  const nodeTypeLabel = (value) => {
    if (value === "COMPONENT") {
      return "Composante";
    }

    if (value === "SUBCOMPONENT") {
      return "Sous Composante";
    }

    return value || "";
  };


  // ------------------------------------------------------------------
  // Données Géographie
  // ------------------------------------------------------------------

  const geoLevelRecords =
    geoLevels.data?.results ||
    geoLevels.data ||
    [];

  const geoUnitRecords =
    geoUnits.data?.results ||
    geoUnits.data ||
    [];


  // ------------------------------------------------------------------
  // Options niveaux géographiques
  // ------------------------------------------------------------------

  const geoLevelOptions = geoLevelRecords.map((item) => ({
    label: item.name,
    value: item.id,
  }));


  // ------------------------------------------------------------------
  // Retrouver un niveau géographique par son ID
  // ------------------------------------------------------------------

  const getGeoLevel = (geoLevelId) => {
    return geoLevelRecords.find(
      (item) => Number(item.id) === Number(geoLevelId)
    );
  };


  // ------------------------------------------------------------------
  // Options dynamiques pour le rattachement géographique
  // ------------------------------------------------------------------

  const getGeoParentOptions = (values) => {
    const selectedLevel = getGeoLevel(
      values.geo_level
    );

    // Aucun niveau sélectionné.
    if (!selectedLevel) {
      return [];
    }

    // Wilaya = rang 0.
    // Une Wilaya n'a pas de parent.
    if (selectedLevel.rank === 0) {
      return [];
    }

    // Le parent doit être exactement au rang précédent.
    const parentRank =
      selectedLevel.rank - 1;

    return geoUnitRecords
      .filter(
        (unit) =>
          Number(unit.geo_level_rank) ===
          Number(parentRank)
      )
      .map((unit) => ({
        label: `${unit.name}`,
        value: unit.id,
      }));
  };


  // ------------------------------------------------------------------
  // Libellé du niveau géographique
  // ------------------------------------------------------------------

  const geoLevelLabel = (row) => {
    return row.geo_level_name || "";
  };


  // ------------------------------------------------------------------
  // Affichage du rattachement
  // ------------------------------------------------------------------

  const geoParentLabel = (row) => {
    if (!row.parent_name) {
      return "—";
    }

    return row.parent_name;
  };


  // ------------------------------------------------------------------
  // Colonnes communes
  // ------------------------------------------------------------------

  const codeName = [
    {
      field: "code",
      header: t("common.code"),
    },
    {
      field: "name",
      header: t("common.name"),
    },
  ];


  const codeNameFields = [
    {
      name: "code",
      label: t("common.code"),
      type: "text",
      required: true,
    },
    {
      name: "name",
      label: t("common.name"),
      type: "text",
      required: true,
    },
  ];


  return (
    <div>

      <h3 className="mb-3">
        {t("nav.reference")}
      </h3>

      <TabView>

        {/* ========================================================== */}
        {/* Composantes / Sous Composantes */}
        {/* ========================================================== */}

        <TabPanel
          header={t("nav.program_structure")}
        >
          <ListPage
            title={t("nav.program_structure")}
            resourceName="programNodes"
            canManage={canManage}

            columns={[
              ...codeName,

              {
                field: "node_type",
                header: "Type",
                body: (row) =>
                  nodeTypeLabel(
                    row.node_type
                  ),
              },

              {
                field: "parent_name",
                header: "Composante parente",
              },

              {
                field: "order",
                header: "Ordre",
              },
            ]}

            fields={[
              ...codeNameFields,

              {
                name: "node_type",
                label: "Type",
                type: "dropdown",
                required: true,
                options: nodeTypeOptions,
              },

              {
                name: "parent",
                label: "Composante parente",
                type: "dropdown",
                options: programNodeOptions,
              },

              {
                name: "order",
                label: "Ordre",
                type: "number",
              },
            ]}
          />
        </TabPanel>


        {/* ========================================================== */}
        {/* Zone d'intervention */}
        {/* ========================================================== */}

        <TabPanel
          header={t("nav.intervention_zone")}
        >
          <ListPage
            title={t("nav.intervention_zone")}
            resourceName="geoUnits"
            canManage={canManage}

            columns={[
              ...codeName,

              {
                field: "geo_level_name",
                header: "Type de zone",
                body: (row) =>
                  geoLevelLabel(row),
              },

              {
                field: "parent_name",
                header: "Rattachement",
                body: (row) =>
                  geoParentLabel(row),
              },
            ]}

            fields={[
              ...codeNameFields,

              {
                name: "geo_level",
                label: "Type de zone",
                type: "dropdown",
                required: true,
                options: geoLevelOptions,
              },

              {
                name: "parent",
                label: "Rattachement",
                type: "dropdown",

                /*
                 * Le champ est masqué pour le niveau 0
                 * (Wilaya dans le PRDC-VFS).
                 */
                visible: (values) => {
                  const level =
                    getGeoLevel(
                      values.geo_level
                    );

                  return (
                    level &&
                    level.rank > 0
                  );
                },

                /*
                 * Le rattachement est obligatoire pour :
                 *
                 * Moughataa
                 * Commune
                 * Village
                 */
                required: true,

                /*
                 * Options filtrées automatiquement
                 * selon le niveau sélectionné.
                 */
                options: (values) =>
                  getGeoParentOptions(values),
              },

            ]}

            /*
             * Nettoyage avant envoi au backend.
             *
             * Une Wilaya ne doit jamais avoir de parent.
             */
            fromForm={(values) => {
              const body = {
                ...values,
              };

              const level =
                getGeoLevel(
                  body.geo_level
                );

              if (
                level &&
                level.rank === 0
              ) {
                body.parent = null;
              }

              return body;
            }}
          />
        </TabPanel>


        {/* ========================================================== */}
        {/* Catégories de dépense */}
        {/* ========================================================== */}

        <TabPanel
          header="Catégories de dépense"
        >
          <ListPage
            title="Catégories de dépense"
            resourceName="expenseCategories"
            canManage={canManage}
            columns={codeName}
            fields={codeNameFields}
          />
        </TabPanel>


        {/* ========================================================== */}
        {/* Sources de financement */}
        {/* ========================================================== */}

        <TabPanel
          header="Sources de financement"
        >
          <ListPage
            title="Sources de financement"
            resourceName="fundingSources"
            canManage={canManage}
            columns={codeName}
            fields={codeNameFields}
          />
        </TabPanel>


        {/* ========================================================== */}
        {/* Méthodes de passation */}
        {/* ========================================================== */}

        <TabPanel
          header="Méthodes de passation"
        >
          <ListPage
            title="Méthodes de passation"
            resourceName="procurementMethods"
            canManage={canManage}
            columns={codeName}
            fields={codeNameFields}
          />
        </TabPanel>


        {/* ========================================================== */}
        {/* Étapes de passation */}
        {/* ========================================================== */}

        <TabPanel
          header="Étapes de passation"
        >
          <ListPage
            title="Étapes de passation"
            resourceName="procurementStages"
            canManage={canManage}

            columns={[
              ...codeName,

              {
                field: "order",
                header: "Ordre",
              },
            ]}

            fields={[
              ...codeNameFields,

              {
                name: "order",
                label: "Ordre",
                type: "number",
              },
            ]}
          />
        </TabPanel>


        {/* ========================================================== */}
        {/* Unités de mesure */}
        {/* ========================================================== */}

        <TabPanel
          header={t("nav.units")}
        >
          <ListPage
            title={t("nav.units")}
            resourceName="unitsOfMeasure"
            canManage={canManage}

            columns={[
              ...codeName,

              {
                field: "symbol",
                header: "Symbole",
              },
            ]}

            fields={[
              ...codeNameFields,

              {
                name: "symbol",
                label: "Symbole",
                type: "text",
              },
            ]}
          />
        </TabPanel>


        {/* ========================================================== */}
        {/* Responsable / Partenaire */}
        {/* ========================================================== */}

        <TabPanel
          header={t("nav.partners")}
        >
          <ListPage
            title={t("nav.partners")}
            resourceName="partners"
            canManage={canManage}

            columns={[
              ...codeName,

              {
                field: "phone",
                header: "Téléphone",
              },

              {
                field: "email",
                header: "Email",
              },
            ]}

            fields={[
              ...codeNameFields,

              {
                name: "phone",
                label: "Téléphone",
                type: "text",
              },

              {
                name: "email",
                label: "Email",
                type: "text",
              },
            ]}
          />
        </TabPanel>

      </TabView>

    </div>
  );
}