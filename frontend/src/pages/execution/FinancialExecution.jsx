import { useMemo, useRef, useState } from "react";

import { Button } from "primereact/button";
import { Column } from "primereact/column";
import { DataTable } from "primereact/datatable";
import { Dialog } from "primereact/dialog";
import { Dropdown } from "primereact/dropdown";
import { InputText } from "primereact/inputtext";
import { ProgressBar } from "primereact/progressbar";
import { Tag } from "primereact/tag";
import { Toast } from "primereact/toast";

import EntityFormDialog from "../../components/EntityFormDialog.jsx";

import { useAuth } from "../../auth/AuthProvider.jsx";

import {
  useList,
  useRemove,
  useSave,
} from "../../services/hooks.js";


// ======================================================================
// TYPES DE SUIVI FINANCIER
// ======================================================================

const KINDS = [
  "ENGAGEMENT",
  "DISBURSEMENT",
  "REALIZATION",
];

const KIND_LABEL = {
  ENGAGEMENT: "Engagement",
  DISBURSEMENT: "Décaissement",
  REALIZATION: "Dépense justifiée",
};


// ======================================================================
// PAGE
// ======================================================================

export default function FinancialExecution() {

  const toast = useRef(null);

  const { hasCapability } = useAuth();

  const canCreate =
    hasCapability(
      "financialtransaction.create"
    );


  // ====================================================================
  // ETATS
  // ====================================================================

  const [
    activityFilter,
    setActivityFilter,
  ] = useState(null);

  const [
    exerciseFilter,
    setExerciseFilter,
  ] = useState(null);

  const [
    search,
    setSearch,
  ] = useState("");

  const [
    dialog,
    setDialog,
  ] = useState({
    open: false,
    initial: null,
  });

  const [
    detailDialog,
    setDetailDialog,
  ] = useState({
    open: false,
    row: null,
  });


  // ====================================================================
  // ACTIVITES
  // ====================================================================

  const activities =
    useList(
      "activities",
      {
        page_size: 1000,
        ordering: "code",
      }
    );

  const activityRecords =
    activities.data?.results ||
    activities.data ||
    [];


  const activityOptions =
    activityRecords.map(
      (activity) => ({
        label:
          activity.code
            ? `${activity.code} — ${activity.title}`
            : activity.title,

        value:
          activity.id,
      })
    );


  // ====================================================================
  // LIGNES BUDGETAIRES
  // ====================================================================

  const budgetLines =
    useList(
      "budgetLines",
      {
        page_size: 2000,
        ordering: "-fiscal_year",
      }
    );

  const budgetLineRecords =
    budgetLines.data?.results ||
    budgetLines.data ||
    [];


  // ====================================================================
  // OPTIONS ACTIVITES PROGRAMMEES FINANCIEREMENT
  //
  // La valeur envoyée reste l'identifiant de BudgetLine.
  // L'utilisateur voit l'activité.
  // ====================================================================

  const budgetLineOptions =
    budgetLineRecords
      .filter(
        (line) =>
          !!line.activity
      )
      .map(
        (line) => {

          const activityLabel =
            line.activity_code
              ? `${line.activity_code} — ${line.activity_title}`
              : (
                  line.activity_title ||
                  `Activité #${line.activity}`
                );


          const year =
            line.fiscal_year ||
            "—";


          const amount =
            new Intl.NumberFormat(
              "fr-FR",
              {
                maximumFractionDigits: 2,
              }
            ).format(
              Number(
                line.amount || 0
              )
            );


          return {
            label:
              `${activityLabel} | Exercice ${year} | Budget ${amount} MRU`,

            value:
              line.id,
          };
        }
      );


  // ====================================================================
  // EXERCICES
  // ====================================================================

  const exerciseOptions =
    Array.from(
      new Set(
        budgetLineRecords
          .map(
            (line) =>
              line.fiscal_year
          )
          .filter(Boolean)
      )
    )
      .sort(
        (a, b) =>
          Number(b) -
          Number(a)
      )
      .map(
        (year) => ({
          label:
            String(year),

          value:
            Number(year),
        })
      );


  // ====================================================================
  // TRANSACTIONS FINANCIERES
  // ====================================================================

  const transactions =
    useList(
      "financialTransactions",
      {
        page_size: 5000,
        ordering: "-date",
      }
    );

  const transactionRecords =
    transactions.data?.results ||
    transactions.data ||
    [];


  // ====================================================================
  // SAUVEGARDE / SUPPRESSION
  // ====================================================================

  const save =
    useSave(
      "financialTransactions"
    );

  const remove =
    useRemove(
      "financialTransactions"
    );


  // ====================================================================
  // FORMAT MONTANT
  // ====================================================================

  const formatAmount =
    (value) =>
      new Intl.NumberFormat(
        "fr-FR",
        {
          minimumFractionDigits: 0,
          maximumFractionDigits: 2,
        }
      ).format(
        Number(
          value || 0
        )
      );


  // ====================================================================
  // COULEUR DES TAUX
  // ====================================================================

  const rateSeverity =
    (rate) => {

      if (rate >= 80) {
        return "success";
      }

      if (rate >= 50) {
        return "warning";
      }

      return "danger";
    };


  // ====================================================================
  // CONSTRUCTION DU SUIVI PAR LIGNE BUDGETAIRE / ACTIVITE
  //
  // Les transactions sont prises en compte immédiatement.
  // Aucun workflow n'est utilisé dans cette page.
  // ====================================================================

  const rows =
    useMemo(
      () => {

        return budgetLineRecords
          .map(
            (line) => {

              // --------------------------------------------------------
              // ACTIVITE
              // --------------------------------------------------------

              const activity =
                activityRecords.find(
                  (item) =>
                    Number(item.id) ===
                    Number(line.activity)
                );


              // --------------------------------------------------------
              // TRANSACTIONS DE CETTE LIGNE BUDGETAIRE
              // --------------------------------------------------------

              const lineTransactions =
                transactionRecords
                  .filter(
                    (transaction) =>
                      Number(
                        transaction.budget_line
                      ) ===
                      Number(
                        line.id
                      )
                  )
                  .sort(
                    (a, b) => {

                      const dateA =
                        a.date
                          ? new Date(a.date)
                          : new Date(0);

                      const dateB =
                        b.date
                          ? new Date(b.date)
                          : new Date(0);

                      return dateB - dateA;
                    }
                  );


              // --------------------------------------------------------
              // ENGAGEMENTS
              // --------------------------------------------------------

              const engagements =
                lineTransactions
                  .filter(
                    (transaction) =>
                      transaction.kind ===
                      "ENGAGEMENT"
                  )
                  .reduce(
                    (
                      sum,
                      transaction
                    ) =>
                      sum +
                      Number(
                        transaction.amount ||
                        0
                      ),
                    0
                  );


              // --------------------------------------------------------
              // DECAISSEMENTS
              // --------------------------------------------------------

              const disbursements =
                lineTransactions
                  .filter(
                    (transaction) =>
                      transaction.kind ===
                      "DISBURSEMENT"
                  )
                  .reduce(
                    (
                      sum,
                      transaction
                    ) =>
                      sum +
                      Number(
                        transaction.amount ||
                        0
                      ),
                    0
                  );


              // --------------------------------------------------------
              // DEPENSES JUSTIFIEES
              // --------------------------------------------------------

              const realizations =
                lineTransactions
                  .filter(
                    (transaction) =>
                      transaction.kind ===
                      "REALIZATION"
                  )
                  .reduce(
                    (
                      sum,
                      transaction
                    ) =>
                      sum +
                      Number(
                        transaction.amount ||
                        0
                      ),
                    0
                  );


              // --------------------------------------------------------
              // BUDGET
              // --------------------------------------------------------

              const programmedAmount =
                Number(
                  line.amount ||
                  0
                );


              // --------------------------------------------------------
              // SOLDE
              //
              // Budget programmé - dépenses justifiées
              // --------------------------------------------------------

              const balance =
                programmedAmount -
                realizations;


              // --------------------------------------------------------
              // TAUX ENGAGEMENT
              // --------------------------------------------------------

              const commitmentRate =
                programmedAmount > 0
                  ? (
                      engagements /
                      programmedAmount
                    ) * 100
                  : 0;


              // --------------------------------------------------------
              // TAUX DECAISSEMENT
              // --------------------------------------------------------

              const disbursementRate =
                programmedAmount > 0
                  ? (
                      disbursements /
                      programmedAmount
                    ) * 100
                  : 0;


              // --------------------------------------------------------
              // TAUX REALISATION FINANCIERE
              // --------------------------------------------------------

              const realizationRate =
                programmedAmount > 0
                  ? (
                      realizations /
                      programmedAmount
                    ) * 100
                  : 0;


              // --------------------------------------------------------
              // RESULTAT
              // --------------------------------------------------------

              return {

                ...line,

                activity_label:
                  line.activity_title ||
                  (
                    activity
                      ? (
                          activity.code
                            ? `${activity.code} — ${activity.title}`
                            : activity.title
                        )
                      : "—"
                  ),

                exercise:
                  line.fiscal_year ||
                  "—",

                programmed_amount:
                  programmedAmount,

                engagements,

                disbursements,

                realizations,

                balance,

                commitment_rate:
                  commitmentRate,

                disbursement_rate:
                  disbursementRate,

                realization_rate:
                  realizationRate,

                transactions:
                  lineTransactions,
              };
            }
          )

          // ------------------------------------------------------------
          // FILTRES
          // ------------------------------------------------------------

          .filter(
            (row) => {

              if (
                activityFilter &&
                Number(row.activity) !==
                Number(activityFilter)
              ) {
                return false;
              }


              if (
                exerciseFilter &&
                Number(row.fiscal_year) !==
                Number(exerciseFilter)
              ) {
                return false;
              }


              if (
                search.trim()
              ) {

                const value =
                  search
                    .trim()
                    .toLowerCase();


                const text =
                  [
                    row.activity_label,
                    row.program_node_name,
                    row.component_name,
                    row.expense_category_name,
                    row.funding_source_name,
                    row.note,
                  ]
                    .filter(Boolean)
                    .join(" ")
                    .toLowerCase();


                if (
                  !text.includes(
                    value
                  )
                ) {
                  return false;
                }
              }


              return true;
            }
          );
      },
      [
        budgetLineRecords,
        transactionRecords,
        activityRecords,
        activityFilter,
        exerciseFilter,
        search,
      ]
    );


  // ====================================================================
  // SYNTHESE GENERALE
  // ====================================================================

  const totalProgrammed =
    rows.reduce(
      (sum, row) =>
        sum +
        Number(
          row.programmed_amount ||
          0
        ),
      0
    );


  const totalEngagements =
    rows.reduce(
      (sum, row) =>
        sum +
        Number(
          row.engagements ||
          0
        ),
      0
    );


  const totalDisbursements =
    rows.reduce(
      (sum, row) =>
        sum +
        Number(
          row.disbursements ||
          0
        ),
      0
    );


  const totalRealizations =
    rows.reduce(
      (sum, row) =>
        sum +
        Number(
          row.realizations ||
          0
        ),
      0
    );


  const totalBalance =
    totalProgrammed -
    totalRealizations;


  const globalRealizationRate =
    totalProgrammed > 0
      ? (
          totalRealizations /
          totalProgrammed
        ) * 100
      : 0;


  // ====================================================================
  // CHAMPS FORMULAIRE
  // ====================================================================

  const formFields = [

    {
      name: "budget_line",
      label: "Activité",
      type: "dropdown",
      required: true,
      options:
        budgetLineOptions,
    },

    {
      name: "kind",
      label: "Type de suivi",
      type: "dropdown",
      required: true,
      options:
        KINDS.map(
          (kind) => ({
            label:
              KIND_LABEL[kind],

            value:
              kind,
          })
        ),
    },

    {
      name: "date",
      label: "Date",
      type: "date",
      required: true,
    },

    {
      name: "amount",
      label: "Montant",
      type: "number",
      required: true,
    },

    {
      name: "reference",
      label: "Référence",
      type: "text",
    },

    {
      name: "narrative",
      label: "Observation",
      type: "textarea",
      full: true,
    },
  ];


  // ====================================================================
  // ENREGISTREMENT
  // ====================================================================

  const saveExecution =
    async (values) => {

      // --------------------------------------------------------------
      // LIGNE BUDGETAIRE SELECTIONNEE
      // --------------------------------------------------------------

      const budgetLine =
        budgetLineRecords.find(
          (line) =>
            Number(line.id) ===
            Number(
              values.budget_line
            )
        );


      if (!budgetLine) {

        toast.current?.show({
          severity: "error",
          summary: "Activité",
          detail:
            "Veuillez sélectionner une activité programmée financièrement.",
        });

        return;
      }


      // --------------------------------------------------------------
      // EXERCICE
      // --------------------------------------------------------------

      if (!budgetLine.fiscal_year) {

        toast.current?.show({
          severity: "error",
          summary: "Exercice",
          detail:
            "La programmation financière sélectionnée ne possède pas d'exercice.",
        });

        return;
      }


      // --------------------------------------------------------------
      // DATE / EXERCICE
      // --------------------------------------------------------------

      if (
        values.date
      ) {

        const year =
          new Date(
            values.date
          ).getFullYear();


        if (
          Number(year) !==
          Number(
            budgetLine.fiscal_year
          )
        ) {

          toast.current?.show({
            severity: "error",
            summary:
              "Date incorrecte",
            detail:
              `La date doit appartenir à l'exercice ${budgetLine.fiscal_year}.`,
          });

          return;
        }
      }


      // --------------------------------------------------------------
      // MONTANT
      // --------------------------------------------------------------

      if (
        values.amount === null ||
        values.amount === undefined ||
        values.amount === ""
      ) {

        toast.current?.show({
          severity: "error",
          summary: "Montant",
          detail:
            "Veuillez saisir un montant.",
        });

        return;
      }


      if (
        Number(
          values.amount
        ) < 0
      ) {

        toast.current?.show({
          severity: "error",
          summary: "Montant",
          detail:
            "Le montant ne peut pas être négatif.",
        });

        return;
      }


      // --------------------------------------------------------------
      // BODY
      // --------------------------------------------------------------

      const body = {

        budget_line:
          values.budget_line,

        kind:
          values.kind,

        date:
          values.date,

        fiscal_year:
          budgetLine.fiscal_year,

        amount:
          values.amount,

        reference:
          values.reference ||
          "",

        narrative:
          values.narrative ||
          "",
      };


      // --------------------------------------------------------------
      // SAVE
      // --------------------------------------------------------------

      try {

        await save.mutateAsync({
          id:
            values.id,

          body,
        });


        toast.current?.show({
          severity: "success",
          summary:
            values.id
              ? "Suivi modifié"
              : "Suivi ajouté",
          detail:
            "Le suivi financier a été enregistré.",
        });


        setDialog({
          open: false,
          initial: null,
        });


        transactions.refetch();
        budgetLines.refetch();

      } catch (error) {

        const response =
          error?.response?.data;

        let detail =
          "Impossible d'enregistrer le suivi financier.";


        if (
          response &&
          typeof response ===
          "object"
        ) {

          const first =
            Object.values(
              response
            )?.[0];


          if (
            Array.isArray(
              first
            )
          ) {

            detail =
              first[0];

          } else if (
            typeof first ===
            "string"
          ) {

            detail =
              first;
          }
        }


        toast.current?.show({
          severity: "error",
          summary: "Erreur",
          detail,
        });
      }
    };


  // ====================================================================
  // MODIFIER UN SUIVI
  // ====================================================================

  const editTransaction =
    (transaction) => {

      // Fermer la fenêtre de détail.
      setDetailDialog({
        open: false,
        row: null,
      });


      // Ouvrir le formulaire de modification.
      setDialog({
        open: true,

        initial: {

          id:
            transaction.id,

          budget_line:
            transaction.budget_line,

          kind:
            transaction.kind,

          date:
            transaction.date,

          amount:
            transaction.amount,

          reference:
            transaction.reference ||
            "",

          narrative:
            transaction.narrative ||
            "",
        },
      });
    };


  // ====================================================================
  // SUPPRIMER UN SUIVI
  // ====================================================================

  const deleteTransaction =
    async (transaction) => {

      const ok =
        window.confirm(
          "Voulez-vous supprimer ce suivi financier ?"
        );


      if (!ok) {
        return;
      }


      try {

        await remove.mutateAsync(
          transaction.id
        );


        toast.current?.show({
          severity: "success",
          summary: "Supprimé",
          detail:
            "Le suivi financier a été supprimé.",
        });


        // Fermer le détail pour éviter
        // d'afficher une ancienne version des données.
        setDetailDialog({
          open: false,
          row: null,
        });


        transactions.refetch();
        budgetLines.refetch();

      } catch (error) {

        toast.current?.show({
          severity: "error",
          summary: "Erreur",
          detail:
            error?.response?.data?.detail ||
            "Impossible de supprimer ce suivi financier.",
        });
      }
    };


  // ====================================================================
  // OUVRIR LE DETAIL
  // ====================================================================

  const openDetail =
    (row) => {

      setDetailDialog({
        open: true,
        row,
      });
    };


  // ====================================================================
  // BOUTON DETAIL DU TABLEAU PRINCIPAL
  // ====================================================================

  const detailButtonBody =
    (row) => {

      const count =
        row.transactions?.length ||
        0;


      return (

        <Button
          label={
            count > 0
              ? `Détail (${count})`
              : "Détail"
          }
          icon="pi pi-eye"
          outlined
          size="small"
          onClick={() =>
            openDetail(
              row
            )
          }
        />

      );
    };


  // ====================================================================
  // RENDER
  // ====================================================================

  return (

    <div>

      <Toast
        ref={toast}
      />


      {/* ============================================================= */}
      {/* ENTETE */}
      {/* ============================================================= */}

      <div
        className="
          d-flex
          align-items-center
          gap-3
          flex-wrap
          mb-4
        "
      >

        <div
          className="me-auto"
        >

          <h4
            className="mb-1"
          >
            Suivi financier
          </h4>

          <div
            className="text-muted"
          >
            Suivi de l’exécution du plan financier par activité
          </div>

        </div>


        {canCreate && (

          <Button
            label="Nouveau suivi"
            icon="pi pi-plus"
            onClick={() =>
              setDialog({
                open: true,
                initial: {},
              })
            }
          />

        )}

      </div>


      {/* ============================================================= */}
      {/* FILTRES */}
      {/* ============================================================= */}

      <div
        className="
          d-flex
          gap-2
          flex-wrap
          mb-4
        "
      >

        <span
          className="p-input-icon-left"
        >

          <i
            className="pi pi-search"
          />

          <InputText
            value={
              search
            }
            onChange={
              (e) =>
                setSearch(
                  e.target.value
                )
            }
            placeholder="Rechercher..."
            style={{
              minWidth: "16rem",
            }}
          />

        </span>


        <Dropdown
          value={
            activityFilter
          }
          options={
            activityOptions
          }
          onChange={
            (e) =>
              setActivityFilter(
                e.value
              )
          }
          placeholder="Activité"
          filter
          showClear
          style={{
            minWidth: "22rem",
          }}
        />


        <Dropdown
          value={
            exerciseFilter
          }
          options={
            exerciseOptions
          }
          onChange={
            (e) =>
              setExerciseFilter(
                e.value
              )
          }
          placeholder="Exercice"
          showClear
          style={{
            minWidth: "10rem",
          }}
        />


        <Button
          label="Réinitialiser"
          icon="pi pi-filter-slash"
          outlined
          onClick={() => {

            setActivityFilter(
              null
            );

            setExerciseFilter(
              null
            );

            setSearch(
              ""
            );
          }}
        />

      </div>


      {/* ============================================================= */}
      {/* CARTES DE SYNTHESE */}
      {/* ============================================================= */}

      <div
        className="row g-3 mb-4"
      >

        {/* =========================================================== */}
        {/* BUDGET */}
        {/* =========================================================== */}

        <div
          className="col-md-2"
        >

          <div
            className="card h-100"
          >

            <div
              className="card-body"
            >

              <div
                className="
                  text-muted
                  small
                  mb-1
                "
              >
                Budget programmé
              </div>

              <div
                className="
                  fs-4
                  fw-semibold
                "
              >
                {formatAmount(
                  totalProgrammed
                )}
              </div>

              <small
                className="text-muted"
              >
                MRU
              </small>

            </div>

          </div>

        </div>


        {/* =========================================================== */}
        {/* ENGAGEMENT */}
        {/* =========================================================== */}

        <div
          className="col-md-2"
        >

          <div
            className="card h-100"
          >

            <div
              className="card-body"
            >

              <div
                className="
                  text-muted
                  small
                  mb-1
                "
              >
                Engagements
              </div>

              <div
                className="
                  fs-4
                  fw-semibold
                "
              >
                {formatAmount(
                  totalEngagements
                )}
              </div>

              <small
                className="text-muted"
              >
                MRU
              </small>

            </div>

          </div>

        </div>


        {/* =========================================================== */}
        {/* DECAISSEMENT */}
        {/* =========================================================== */}

        <div
          className="col-md-2"
        >

          <div
            className="card h-100"
          >

            <div
              className="card-body"
            >

              <div
                className="
                  text-muted
                  small
                  mb-1
                "
              >
                Décaissements
              </div>

              <div
                className="
                  fs-4
                  fw-semibold
                "
              >
                {formatAmount(
                  totalDisbursements
                )}
              </div>

              <small
                className="text-muted"
              >
                MRU
              </small>

            </div>

          </div>

        </div>


        {/* =========================================================== */}
        {/* DEPENSES JUSTIFIEES */}
        {/* =========================================================== */}

        <div
          className="col-md-2"
        >

          <div
            className="card h-100"
          >

            <div
              className="card-body"
            >

              <div
                className="
                  text-muted
                  small
                  mb-1
                "
              >
                Dépenses justifiées
              </div>

              <div
                className="
                  fs-4
                  fw-semibold
                "
              >
                {formatAmount(
                  totalRealizations
                )}
              </div>

              <small
                className="text-muted"
              >
                MRU
              </small>

            </div>

          </div>

        </div>


        {/* =========================================================== */}
        {/* SOLDE */}
        {/* =========================================================== */}

        <div
          className="col-md-2"
        >

          <div
            className="card h-100"
          >

            <div
              className="card-body"
            >

              <div
                className="
                  text-muted
                  small
                  mb-1
                "
              >
                Solde
              </div>

              <div
                className="
                  fs-4
                  fw-semibold
                "
              >
                {formatAmount(
                  totalBalance
                )}
              </div>

              <small
                className="text-muted"
              >
                MRU
              </small>

            </div>

          </div>

        </div>


        {/* =========================================================== */}
        {/* TAUX GLOBAL */}
        {/* =========================================================== */}

        <div
          className="col-md-2"
        >

          <div
            className="card h-100"
          >

            <div
              className="card-body"
            >

              <div
                className="
                  text-muted
                  small
                  mb-2
                "
              >
                Taux réalisation financière
              </div>


              <div
                className="
                  d-flex
                  align-items-center
                  gap-2
                  mb-2
                "
              >

                <div
                  className="
                    fs-4
                    fw-semibold
                  "
                >
                  {globalRealizationRate.toFixed(
                    1
                  )} %
                </div>


                <Tag
                  value={
                    globalRealizationRate >= 80
                      ? "Bon"
                      : globalRealizationRate >= 50
                        ? "Moyen"
                        : "Faible"
                  }
                  severity={
                    rateSeverity(
                      globalRealizationRate
                    )
                  }
                />

              </div>


              <ProgressBar
                value={
                  Math.min(
                    globalRealizationRate,
                    100
                  )
                }
                showValue={
                  false
                }
                style={{
                  height: "0.5rem",
                }}
              />

            </div>

          </div>

        </div>

      </div>


      {/* ============================================================= */}
      {/* TABLEAU PRINCIPAL */}
      {/* ============================================================= */}

      <DataTable
        value={
          rows
        }
        loading={
          budgetLines.isLoading ||
          transactions.isLoading
        }
        paginator
        rows={
          25
        }
        rowsPerPageOptions={[
          25,
          50,
          100,
        ]}
        stripedRows
        responsiveLayout="scroll"
        emptyMessage="Aucune donnée financière"
      >

        {/* =========================================================== */}
        {/* ACTIVITE */}
        {/* =========================================================== */}

        <Column
          field="activity_label"
          header="Activité"
          style={{
            minWidth: "18rem",
          }}
        />


        {/* =========================================================== */}
        {/* EXERCICE */}
        {/* =========================================================== */}

        <Column
          field="exercise"
          header="Exercice"
          style={{
            minWidth: "7rem",
          }}
        />


        {/* =========================================================== */}
        {/* BUDGET */}
        {/* =========================================================== */}

        <Column
          header="Budget programmé"
          body={
            (row) =>
              `${formatAmount(
                row.programmed_amount
              )} MRU`
          }
          style={{
            minWidth: "11rem",
          }}
        />


        {/* =========================================================== */}
        {/* ENGAGEMENT */}
        {/* =========================================================== */}

        <Column
          header="Engagements"
          body={
            (row) =>
              `${formatAmount(
                row.engagements
              )} MRU`
          }
          style={{
            minWidth: "10rem",
          }}
        />


        {/* =========================================================== */}
        {/* DECAISSEMENT */}
        {/* =========================================================== */}

        <Column
          header="Décaissements"
          body={
            (row) =>
              `${formatAmount(
                row.disbursements
              )} MRU`
          }
          style={{
            minWidth: "10rem",
          }}
        />


        {/* =========================================================== */}
        {/* DEPENSES JUSTIFIEES */}
        {/* =========================================================== */}

        <Column
          header="Dépenses justifiées"
          body={
            (row) =>
              `${formatAmount(
                row.realizations
              )} MRU`
          }
          style={{
            minWidth: "12rem",
          }}
        />


        {/* =========================================================== */}
        {/* SOLDE */}
        {/* =========================================================== */}

        <Column
          header="Solde"
          body={
            (row) =>
              `${formatAmount(
                row.balance
              )} MRU`
          }
          style={{
            minWidth: "10rem",
          }}
        />


        {/* =========================================================== */}
        {/* TAUX ENGAGEMENT */}
        {/* =========================================================== */}

        <Column
          header="Taux engagement"
          body={
            (row) =>
              `${row.commitment_rate.toFixed(
                1
              )} %`
          }
          style={{
            minWidth: "10rem",
          }}
        />


        {/* =========================================================== */}
        {/* TAUX DECAISSEMENT */}
        {/* =========================================================== */}

        <Column
          header="Taux décaissement"
          body={
            (row) =>
              `${row.disbursement_rate.toFixed(
                1
              )} %`
          }
          style={{
            minWidth: "11rem",
          }}
        />


        {/* =========================================================== */}
        {/* TAUX REALISATION */}
        {/* =========================================================== */}

        <Column
          header="Taux réalisation financière"
          body={
            (row) => (

              <div
                style={{
                  minWidth: "10rem",
                }}
              >

                <div
                  className="
                    d-flex
                    justify-content-between
                    align-items-center
                    gap-2
                    mb-1
                  "
                >

                  <span>
                    {row.realization_rate.toFixed(
                      1
                    )} %
                  </span>


                  <Tag
                    value={
                      row.realization_rate >= 80
                        ? "Bon"
                        : row.realization_rate >= 50
                          ? "Moyen"
                          : "Faible"
                    }
                    severity={
                      rateSeverity(
                        row.realization_rate
                      )
                    }
                  />

                </div>


                <ProgressBar
                  value={
                    Math.min(
                      row.realization_rate,
                      100
                    )
                  }
                  showValue={
                    false
                  }
                  style={{
                    height: "0.45rem",
                  }}
                />

              </div>
            )
          }
          style={{
            minWidth: "14rem",
          }}
        />


        {/* =========================================================== */}
        {/* DETAIL */}
        {/* =========================================================== */}

        <Column
          header="Détail"
          body={
            detailButtonBody
          }
          style={{
            minWidth: "10rem",
          }}
        />

      </DataTable>


      {/* ============================================================= */}
      {/* FENETRE DETAIL D'UNE ACTIVITE */}
      {/* ============================================================= */}

      <Dialog
        visible={
          detailDialog.open
        }
        onHide={() =>
          setDetailDialog({
            open: false,
            row: null,
          })
        }
        header={
          detailDialog.row
            ? `Détail du suivi financier — ${detailDialog.row.activity_label}`
            : "Détail du suivi financier"
        }
        modal
        style={{
          width: "85vw",
          maxWidth: "1200px",
        }}
        breakpoints={{
          "960px": "96vw",
        }}
      >

        {detailDialog.row && (

          <div>

            {/* ======================================================= */}
            {/* INFORMATIONS GENERALES */}
            {/* ======================================================= */}

            <div
              className="row g-3 mb-4"
            >

              {/* ACTIVITE */}

              <div
                className="col-md-4"
              >

                <div
                  className="
                    text-muted
                    small
                    mb-1
                  "
                >
                  Activité
                </div>

                <div
                  className="fw-semibold"
                >
                  {detailDialog.row.activity_label ||
                    "—"}
                </div>

              </div>


              {/* EXERCICE */}

              <div
                className="col-md-2"
              >

                <div
                  className="
                    text-muted
                    small
                    mb-1
                  "
                >
                  Exercice
                </div>

                <div
                  className="fw-semibold"
                >
                  {detailDialog.row.exercise ||
                    "—"}
                </div>

              </div>


              {/* BUDGET */}

              <div
                className="col-md-3"
              >

                <div
                  className="
                    text-muted
                    small
                    mb-1
                  "
                >
                  Budget programmé
                </div>

                <div
                  className="fw-semibold"
                >
                  {formatAmount(
                    detailDialog.row
                      .programmed_amount
                  )} MRU
                </div>

              </div>


              {/* SOLDE */}

              <div
                className="col-md-3"
              >

                <div
                  className="
                    text-muted
                    small
                    mb-1
                  "
                >
                  Solde
                </div>

                <div
                  className="fw-semibold"
                >
                  {formatAmount(
                    detailDialog.row.balance
                  )} MRU
                </div>

              </div>

            </div>


            {/* ======================================================= */}
            {/* SYNTHESE DE L'ACTIVITE */}
            {/* ======================================================= */}

            <div
              className="row g-3 mb-4"
            >

              {/* ENGAGEMENT */}

              <div
                className="col-md-4"
              >

                <div
                  className="card h-100"
                >

                  <div
                    className="card-body"
                  >

                    <div
                      className="
                        text-muted
                        small
                        mb-1
                      "
                    >
                      Engagements
                    </div>

                    <div
                      className="
                        fs-5
                        fw-semibold
                      "
                    >
                      {formatAmount(
                        detailDialog.row
                          .engagements
                      )} MRU
                    </div>

                    <div
                      className="
                        text-muted
                        small
                        mt-1
                      "
                    >
                      Taux :{" "}
                      {detailDialog.row
                        .commitment_rate
                        .toFixed(1)} %
                    </div>

                  </div>

                </div>

              </div>


              {/* DECAISSEMENT */}

              <div
                className="col-md-4"
              >

                <div
                  className="card h-100"
                >

                  <div
                    className="card-body"
                  >

                    <div
                      className="
                        text-muted
                        small
                        mb-1
                      "
                    >
                      Décaissements
                    </div>

                    <div
                      className="
                        fs-5
                        fw-semibold
                      "
                    >
                      {formatAmount(
                        detailDialog.row
                          .disbursements
                      )} MRU
                    </div>

                    <div
                      className="
                        text-muted
                        small
                        mt-1
                      "
                    >
                      Taux :{" "}
                      {detailDialog.row
                        .disbursement_rate
                        .toFixed(1)} %
                    </div>

                  </div>

                </div>

              </div>


              {/* DEPENSE JUSTIFIEE */}

              <div
                className="col-md-4"
              >

                <div
                  className="card h-100"
                >

                  <div
                    className="card-body"
                  >

                    <div
                      className="
                        text-muted
                        small
                        mb-1
                      "
                    >
                      Dépenses justifiées
                    </div>

                    <div
                      className="
                        fs-5
                        fw-semibold
                      "
                    >
                      {formatAmount(
                        detailDialog.row
                          .realizations
                      )} MRU
                    </div>

                    <div
                      className="
                        text-muted
                        small
                        mt-1
                      "
                    >
                      Taux :{" "}
                      {detailDialog.row
                        .realization_rate
                        .toFixed(1)} %
                    </div>

                  </div>

                </div>

              </div>

            </div>


            {/* ======================================================= */}
            {/* TITRE LISTE */}
            {/* ======================================================= */}

            <div
              className="
                d-flex
                align-items-center
                justify-content-between
                gap-2
                mb-2
              "
            >

              <h6
                className="m-0"
              >
                Historique des suivis financiers
              </h6>


              <Tag
                value={
                  `${detailDialog.row.transactions?.length || 0} suivi(s)`
                }
                severity="info"
              />

            </div>


            {/* ======================================================= */}
            {/* TABLEAU DES SUIVIS */}
            {/* ======================================================= */}

            <DataTable
              value={
                detailDialog.row.transactions ||
                []
              }
              stripedRows
              responsiveLayout="scroll"
              emptyMessage="Aucun suivi financier enregistré pour cette activité"
            >

              {/* TYPE */}

              <Column
                header="Type de suivi"
                body={
                  (transaction) => (

                    <Tag
                      value={
                        KIND_LABEL[
                          transaction.kind
                        ] ||
                        transaction.kind
                      }
                    />

                  )
                }
                style={{
                  minWidth: "11rem",
                }}
              />


              {/* DATE */}

              <Column
                field="date"
                header="Date"
                style={{
                  minWidth: "8rem",
                }}
              />


              {/* MONTANT */}

              <Column
                header="Montant"
                body={
                  (transaction) =>
                    `${formatAmount(
                      transaction.amount
                    )} MRU`
                }
                style={{
                  minWidth: "10rem",
                }}
              />


              {/* REFERENCE */}

              <Column
                field="reference"
                header="Référence"
                body={
                  (transaction) =>
                    transaction.reference ||
                    "—"
                }
                style={{
                  minWidth: "10rem",
                }}
              />


              {/* OBSERVATION */}

              <Column
                field="narrative"
                header="Observation"
                body={
                  (transaction) =>
                    transaction.narrative ||
                    "—"
                }
                style={{
                  minWidth: "16rem",
                }}
              />


              {/* ACTIONS */}

              <Column
                header="Actions"
                body={
                  (transaction) => (

                    <div
                      className="
                        d-flex
                        gap-2
                        align-items-center
                      "
                    >

                      <Button
                        icon="pi pi-pencil"
                        label="Modifier"
                        size="small"
                        outlined
                        onClick={() =>
                          editTransaction(
                            transaction
                          )
                        }
                      />


                      <Button
                        icon="pi pi-trash"
                        label="Supprimer"
                        size="small"
                        outlined
                        severity="danger"
                        onClick={() =>
                          deleteTransaction(
                            transaction
                          )
                        }
                      />

                    </div>

                  )
                }
                style={{
                  minWidth: "15rem",
                }}
              />

            </DataTable>

          </div>

        )}

      </Dialog>


      {/* ============================================================= */}
      {/* FORMULAIRE NOUVEAU / MODIFIER */}
      {/* ============================================================= */}

      <EntityFormDialog
        visible={
          dialog.open
        }
        onHide={() =>
          setDialog({
            open: false,
            initial: null,
          })
        }
        fields={
          formFields
        }
        initial={
          dialog.initial
        }
        title={
          dialog.initial?.id
            ? "Modifier le suivi financier"
            : "Nouveau suivi financier"
        }
        onSubmit={
          saveExecution
        }
      />

    </div>
  );
}