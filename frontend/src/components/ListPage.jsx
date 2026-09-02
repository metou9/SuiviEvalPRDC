import { useState } from "react";
import { Button } from "primereact/button";
import { Column } from "primereact/column";
import {
  ConfirmDialog,
  confirmDialog,
} from "primereact/confirmdialog";
import { DataTable } from "primereact/datatable";
import { InputText } from "primereact/inputtext";
import { useTranslation } from "react-i18next";

import {
  useList,
  useRemove,
  useSave,
} from "../services/hooks.js";

import EntityFormDialog from "./EntityFormDialog.jsx";


/**
 * Generic list scaffold:
 * paginated DataTable + New/Edit dialog + delete + export.
 *
 * props:
 *  - title, resourceName
 *  - columns: [{ field, header, body? }]
 *  - fields: form field spec for the dialog (omit to disable create/edit)
 *  - canManage: bool (show New/Edit/Delete)
 *  - extraParams: object merged into list params
 *  - toForm: optional transform row -> form values
 *  - fromForm: optional transform form values -> API body
 *  - prepareBody: optional transform form values -> API body
 *                 if provided, it has priority over fromForm
 *  - actionsBody: optional (row) => node appended to the actions column
 */
export default function ListPage({
  title,
  resourceName,
  columns,
  fields,
  canManage = false,
  extraParams = {},

  toForm = (r) => r,

  fromForm = (v) => v,

  prepareBody,

  actionsBody,
}) {
  const { t } = useTranslation();

  // ==================================================================
  // ETAT LOCAL
  // ==================================================================

  const [page, setPage] =
    useState(0);

  const [rows] =
    useState(25);

  const [search, setSearch] =
    useState("");

  const [dialog, setDialog] =
    useState({
      open: false,
      initial: null,
    });

  // ==================================================================
  // PARAMETRES DE LISTE
  // ==================================================================

  const params = {
    page:
      page + 1,

    page_size:
      rows,

    ...(
      search
        ? { search }
        : {}
    ),

    ...extraParams,
  };

  // ==================================================================
  // API
  // ==================================================================

  const {
    data,
    isLoading,
  } = useList(
    resourceName,
    params
  );

  const save =
    useSave(
      resourceName
    );

  const remove =
    useRemove(
      resourceName
    );

  // ==================================================================
  // DONNEES
  // ==================================================================

  const records =
    data?.results ??
    data ??
    [];

  const total =
    data?.count ??
    records.length;

  // ==================================================================
  // CREATION / MODIFICATION
  // ==================================================================

  const onSubmit = async (values) => {
    let body;

    // --------------------------------------------------------------
    // Si prepareBody existe, on l'utilise en priorité.
    // Sinon on conserve le fonctionnement historique avec fromForm.
    // --------------------------------------------------------------

    if (prepareBody) {
      body =
        await prepareBody(
          values
        );
    } else {
      body =
        await fromForm(
          values
        );
    }

    await save.mutateAsync({
      id:
        values.id,

      body,
    });

    setDialog({
      open: false,
      initial: null,
    });
  };

  // ==================================================================
  // SUPPRESSION
  // ==================================================================

  const onDelete = (row) =>
    confirmDialog({
      message:
        t(
          "common.confirm_delete"
        ),

      header:
        title,

      icon:
        "pi pi-exclamation-triangle",

      accept: () =>
        remove.mutate(
          row.id
        ),
    });

  // ==================================================================
  // PAGE
  // ==================================================================

  return (
    <div>
      <ConfirmDialog />

      {/* ============================================================ */}
      {/* ENTETE                                                      */}
      {/* ============================================================ */}

      <div className="d-flex align-items-center mb-3 gap-2 flex-wrap">
        <h4 className="m-0 me-auto">
          {title}
        </h4>

        <span className="p-input-icon-left">
          <i className="pi pi-search" />

          <InputText
            placeholder={
              t(
                "common.search"
              )
            }

            value={
              search
            }

            onChange={(e) => {
              setSearch(
                e.target.value
              );

              setPage(
                0
              );
            }}
          />
        </span>

        {canManage && fields && (
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

      {/* ============================================================ */}
      {/* TABLEAU                                                     */}
      {/* ============================================================ */}

      <DataTable
        value={
          records
        }

        loading={
          isLoading
        }

        lazy

        paginator

        rows={
          rows
        }

        totalRecords={
          total
        }

        first={
          page * rows
        }

        onPage={(e) =>
          setPage(
            e.page
          )
        }

        responsiveLayout="stack"

        breakpoint="960px"

        emptyMessage={
          t(
            "common.empty"
          )
        }

        stripedRows
      >
        {columns.map((column) => (
          <Column
            key={
              column.field
            }

            field={
              column.field
            }

            header={
              column.header
            }

            body={
              column.body
            }

            sortable={
              column.sortable
            }
          />
        ))}

        {(canManage || actionsBody) && (
          <Column
            header={
              t(
                "common.actions"
              )
            }

            body={(row) => (
              <div className="d-flex gap-2 align-items-center">
                {actionsBody?.(
                  row
                )}

                {canManage && fields && (
                  <Button
                    icon="pi pi-pencil"

                    rounded

                    text

                    size="small"

                    onClick={() =>
                      setDialog({
                        open: true,

                        initial:
                          toForm(
                            row
                          ),
                      })
                    }
                  />
                )}

                {canManage && (
                  <Button
                    icon="pi pi-trash"

                    rounded

                    text

                    size="small"

                    severity="danger"

                    onClick={() =>
                      onDelete(
                        row
                      )
                    }
                  />
                )}
              </div>
            )}
          />
        )}
      </DataTable>

      {/* ============================================================ */}
      {/* FORMULAIRE                                                  */}
      {/* ============================================================ */}

      {fields && (
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

          onSubmit={
            onSubmit
          }

          title={
            title
          }
        />
      )}
    </div>
  );
}