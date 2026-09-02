import { useMemo, useRef, useState } from "react";

import { Button } from "primereact/button";
import { Column } from "primereact/column";
import { DataTable } from "primereact/datatable";
import { Dropdown } from "primereact/dropdown";
import { FileUpload } from "primereact/fileupload";
import { Toast } from "primereact/toast";

import { useTranslation } from "react-i18next";

import EntityFormDialog from "../../components/EntityFormDialog.jsx";

import { useAuth } from "../../auth/AuthProvider.jsx";

import http from "../../services/http.js";

import {
  useList,
  useRemove,
  useSave,
} from "../../services/hooks.js";


// ======================================================================
// TYPES DE TRANSACTIONS FINANCIERES
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

export default function Transactions() {

  const { t } =
    useTranslation();


  const {
    hasCapability,
  } = useAuth();


  const canCreate =
    hasCapability(
      "financialtransaction.create"
    );


  const toast =
    useRef(null);


  // ====================================================================
  // ETATS
  // ====================================================================

  const [
    kind,
    setKind,
  ] = useState(null);


  const [
    dialog,
    setDialog,
  ] = useState({
    open: false,
    initial: null,
  });


  // ====================================================================
  // LIGNES BUDGETAIRES
  // ====================================================================

  const budgetLines =
    useList(
      "budgetLines",
      {
        page_size: 1000,
        ordering: "-fiscal_year",
      }
    );


  const budgetLineRecords =
    budgetLines.data?.results ||
    budgetLines.data ||
    [];


  // ====================================================================
  // OPTIONS LIGNES BUDGETAIRES
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
            line.activity_title
              ? (
                  line.activity_code
                    ? `${line.activity_code} — ${line.activity_title}`
                    : line.activity_title
                )
              : `Activité #${line.activity}`;


          const yearLabel =
            line.fiscal_year
              ? `Exercice ${line.fiscal_year}`
              : "Exercice non défini";


          const amountLabel =
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
              `${activityLabel} | ${yearLabel} | Budget ${amountLabel} MRU`,

            value:
              line.id,
          };
        }
      );


  // ====================================================================
  // PARAMETRES DE LA LISTE
  // ====================================================================

  const params =
    useMemo(
      () => ({

        page_size: 500,

        ...(kind
          ? {
              kind,
            }
          : {}),

        ordering: "-date",

      }),
      [
        kind,
      ]
    );


  // ====================================================================
  // TRANSACTIONS
  // ====================================================================

  const {
    data,
    isLoading,
    refetch,
  } =
    useList(
      "financialTransactions",
      params
    );


  const rows =
    data?.results ||
    data ||
    [];


  // ====================================================================
  // SAVE / DELETE
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
  // JUSTIFICATIF
  //
  // Facultatif pour :
  // - Engagement
  // - Décaissement
  // - Dépense justifiée
  //
  // Peut être ajouté après l'enregistrement.
  // Peut également être remplacé.
  // ====================================================================

  const uploadDoc =
    async (
      id,
      file
    ) => {

      if (!file) {
        return;
      }


      try {

        const fd =
          new FormData();


        fd.append(
          "supporting_doc",
          file
        );


        await http.patch(
          `/financial-transactions/${id}/`,
          fd,
          {
            headers: {
              "Content-Type":
                "multipart/form-data",
            },
          }
        );


        toast.current?.show({
          severity: "success",
          summary: "Justificatif enregistré",
          detail:
            "Le justificatif a été ajouté à la transaction.",
        });


        refetch();

      } catch (error) {

        toast.current?.show({
          severity: "error",
          summary: "Erreur",
          detail:
            error?.response?.data?.detail ||
            "Impossible d'ajouter le justificatif.",
        });
      }
    };


  // ====================================================================
  // FORMULAIRE
  // ====================================================================

  const fields = [

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
      label: "Type d'opération",
      type: "dropdown",
      required: true,
      options:
        KINDS.map(
          (item) => ({
            label:
              KIND_LABEL[item],

            value:
              item,
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
      label: "Observation / description",
      type: "textarea",
      full: true,
    },
  ];


  // ====================================================================
  // ACTIVITE
  // ====================================================================

  const activityBody =
    (row) => {

      if (!row.activity_title) {
        return "—";
      }


      if (row.activity_code) {

        return (
          `${row.activity_code} — ${row.activity_title}`
        );
      }


      return row.activity_title;
    };


  // ====================================================================
  // TYPE
  // ====================================================================

  const kindBody =
    (row) => (

      <span>
        {
          KIND_LABEL[row.kind] ||
          row.kind ||
          "—"
        }
      </span>

    );


  // ====================================================================
  // SOUS-COMPOSANTE
  // ====================================================================

  const programNodeBody =
    (row) =>
      row.program_node_name ||
      "—";


  // ====================================================================
  // CATEGORIE
  // ====================================================================

  const categoryBody =
    (row) =>
      row.expense_category_name ||
      "—";


  // ====================================================================
  // SOURCE DE FINANCEMENT
  // ====================================================================

  const fundingSourceBody =
    (row) =>
      row.funding_source_name ||
      "—";


  // ====================================================================
  // MODIFIER
  // ====================================================================

  const editTransaction =
    (row) => {

      setDialog({
        open: true,

        initial: {

          id:
            row.id,

          budget_line:
            row.budget_line,

          kind:
            row.kind,

          date:
            row.date,

          amount:
            row.amount,

          reference:
            row.reference ||
            "",

          narrative:
            row.narrative ||
            "",
        },
      });
    };


  // ====================================================================
  // SUPPRIMER
  // ====================================================================

  const deleteTransaction =
    async (row) => {

      const confirmed =
        window.confirm(
          "Voulez-vous supprimer cette transaction financière ?"
        );


      if (!confirmed) {
        return;
      }


      try {

        await remove.mutateAsync(
          row.id
        );


        toast.current?.show({
          severity: "success",
          summary: "Transaction supprimée",
          detail:
            "La transaction financière a été supprimée.",
        });


        refetch();

      } catch (error) {

        toast.current?.show({
          severity: "error",
          summary: "Erreur",
          detail:
            error?.response?.data?.detail ||
            "Impossible de supprimer la transaction financière.",
        });
      }
    };


  // ====================================================================
  // JUSTIFICATIF
  // ====================================================================

  const supportingDocBody =
    (row) => {

      return (

        <div
          className="
            d-flex
            align-items-center
            gap-2
            flex-wrap
          "
        >

          {row.supporting_doc
            ? (

                <a
                  href={
                    row.supporting_doc
                  }
                  target="_blank"
                  rel="noreferrer"
                  title="Voir le justificatif"
                  style={{
                    textDecoration:
                      "none",
                  }}
                >

                  <Button
                    type="button"
                    icon="pi pi-file"
                    label="Voir"
                    size="small"
                    text
                  />

                </a>

              )
            : (

                <span
                  className="text-muted"
                >
                  Aucun
                </span>

              )
          }


          {canCreate && (

            <FileUpload
              mode="basic"
              auto
              customUpload

              chooseLabel={
                row.supporting_doc
                  ? "Remplacer"
                  : "Ajouter"
              }

              chooseOptions={{
                icon:
                  row.supporting_doc
                    ? "pi pi-refresh"
                    : "pi pi-paperclip",

                className:
                  "p-button-sm p-button-outlined",
              }}

              uploadHandler={
                (event) => {

                  const file =
                    event.files?.[0];


                  if (file) {

                    uploadDoc(
                      row.id,
                      file
                    );
                  }
                }
              }
            />

          )}

        </div>

      );
    };


  // ====================================================================
  // ACTIONS
  // ====================================================================

  const actionsBody =
    (row) => (

      <div
        className="
          d-flex
          align-items-center
          gap-2
          flex-wrap
        "
      >

        <Button
          icon="pi pi-pencil"
          label="Modifier"
          size="small"
          outlined
          onClick={() =>
            editTransaction(
              row
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
              row
            )
          }
        />

      </div>

    );


  // ====================================================================
  // ENREGISTRER
  // ====================================================================

  const saveTransaction =
    async (values) => {

      // --------------------------------------------------------------
      // PROGRAMMATION FINANCIERE
      // --------------------------------------------------------------

      const selectedBudgetLine =
        budgetLineRecords.find(
          (line) =>
            Number(line.id) ===
            Number(
              values.budget_line
            )
        );


      if (!selectedBudgetLine) {

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

      const fiscalYear =
        Number(
          selectedBudgetLine.fiscal_year
        );


      if (!fiscalYear) {

        toast.current?.show({
          severity: "error",
          summary: "Exercice",
          detail:
            "La programmation financière sélectionnée ne possède pas d'exercice.",
        });

        return;
      }


      // --------------------------------------------------------------
      // CONTROLE DATE / EXERCICE
      // --------------------------------------------------------------

      if (
        values.date
      ) {

        const transactionDate =
          new Date(
            values.date
          );


        const transactionYear =
          transactionDate.getFullYear();


        if (
          transactionYear !==
          fiscalYear
        ) {

          toast.current?.show({
            severity: "error",
            summary:
              "Date incorrecte",
            detail:
              `La date doit appartenir à l'exercice ${fiscalYear}.`,
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
      // DONNEES
      //
      // Les autres informations sont récupérées automatiquement
      // depuis BudgetLine par le serializer :
      //
      // - program_node
      // - expense_category
      // - funding_source
      // - geo_unit
      // --------------------------------------------------------------

      const body = {

        budget_line:
          values.budget_line,

        kind:
          values.kind,

        date:
          values.date,

        fiscal_year:
          fiscalYear,

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
      // ENREGISTREMENT
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
              ? "Transaction modifiée"
              : "Transaction enregistrée",

          detail:
            values.id
              ? "La transaction financière a été modifiée."
              : "La transaction financière a été enregistrée.",
        });


        setDialog({
          open: false,
          initial: null,
        });


        refetch();

      } catch (error) {

        const response =
          error?.response?.data;


        let detail =
          "Impossible d'enregistrer la transaction financière.";


        if (
          response &&
          typeof response ===
          "object"
        ) {

          const firstError =
            Object.values(
              response
            )?.[0];


          if (
            Array.isArray(
              firstError
            )
          ) {

            detail =
              firstError[0];

          } else if (
            typeof firstError ===
            "string"
          ) {

            detail =
              firstError;
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
          gap-2
          mb-3
          flex-wrap
        "
      >

        <div
          className="me-auto"
        >

          <h4
            className="m-0"
          >
            Transactions financières
          </h4>


          <div
            className="
              text-muted
              small
              mt-1
            "
          >
            Saisie des engagements,
            décaissements et dépenses
            justifiées
          </div>

        </div>


        {/* =========================================================== */}
        {/* FILTRE TYPE */}
        {/* =========================================================== */}

        <Dropdown
          placeholder="Type d'opération"
          value={
            kind
          }
          options={
            KINDS.map(
              (item) => ({
                label:
                  KIND_LABEL[item],

                value:
                  item,
              })
            )
          }
          onChange={
            (e) =>
              setKind(
                e.value
              )
          }
          showClear
          style={{
            minWidth: "13rem",
          }}
        />


        {/* =========================================================== */}
        {/* NOUVELLE TRANSACTION */}
        {/* =========================================================== */}

        {canCreate && (

          <Button
            label={
              t(
                "common.new"
              )
            }
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
      {/* TABLEAU */}
      {/* ============================================================= */}

      <DataTable
        value={
          rows
        }
        loading={
          isLoading ||
          budgetLines.isLoading
        }
        responsiveLayout="scroll"
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
        emptyMessage={
          t(
            "common.empty"
          )
        }
      >

        {/* =========================================================== */}
        {/* TYPE */}
        {/* =========================================================== */}

        <Column
          header="Type"
          body={
            kindBody
          }
          style={{
            minWidth: "10rem",
          }}
        />


        {/* =========================================================== */}
        {/* ACTIVITE */}
        {/* =========================================================== */}

        <Column
          header="Activité"
          body={
            activityBody
          }
          style={{
            minWidth: "18rem",
          }}
        />


        {/* =========================================================== */}
        {/* EXERCICE */}
        {/* =========================================================== */}

        <Column
          field="fiscal_year"
          header="Exercice"
          style={{
            minWidth: "7rem",
          }}
        />


        {/* =========================================================== */}
        {/* SOUS-COMPOSANTE */}
        {/* =========================================================== */}

        <Column
          header="Sous-composante"
          body={
            programNodeBody
          }
          style={{
            minWidth: "14rem",
          }}
        />


        {/* =========================================================== */}
        {/* CATEGORIE */}
        {/* =========================================================== */}

        <Column
          header="Catégorie de dépense"
          body={
            categoryBody
          }
          style={{
            minWidth: "13rem",
          }}
        />


        {/* =========================================================== */}
        {/* SOURCE */}
        {/* =========================================================== */}

        <Column
          header="Source de financement"
          body={
            fundingSourceBody
          }
          style={{
            minWidth: "13rem",
          }}
        />


        {/* =========================================================== */}
        {/* DATE */}
        {/* =========================================================== */}

        <Column
          field="date"
          header="Date"
          style={{
            minWidth: "8rem",
          }}
        />


        {/* =========================================================== */}
        {/* MONTANT */}
        {/* =========================================================== */}

        <Column
          header="Montant"
          body={
            (row) =>
              `${formatAmount(
                row.amount
              )} MRU`
          }
          style={{
            minWidth: "11rem",
          }}
        />


        {/* =========================================================== */}
        {/* REFERENCE */}
        {/* =========================================================== */}

        <Column
          field="reference"
          header="Référence"
          body={
            (row) =>
              row.reference ||
              "—"
          }
          style={{
            minWidth: "10rem",
          }}
        />


        {/* =========================================================== */}
        {/* JUSTIFICATIF */}
        {/* =========================================================== */}

        <Column
          header="Justificatif"
          body={
            supportingDocBody
          }
          style={{
            minWidth: "17rem",
          }}
        />


        {/* =========================================================== */}
        {/* ACTIONS */}
        {/* =========================================================== */}

        <Column
          header={
            t(
              "common.actions"
            )
          }
          body={
            actionsBody
          }
          style={{
            minWidth: "16rem",
          }}
        />

      </DataTable>


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
          fields
        }

        initial={
          dialog.initial
        }

        title={
          dialog.initial?.id
            ? "Modifier la transaction financière"
            : "Nouvelle transaction financière"
        }

        onSubmit={
          saveTransaction
        }
      />

    </div>
  );
} 