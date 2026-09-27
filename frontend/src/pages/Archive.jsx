import {
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import { Button } from "primereact/button";
import { Dialog } from "primereact/dialog";
import { InputText } from "primereact/inputtext";
import { DataTable } from "primereact/datatable";
import { Column } from "primereact/column";
import {
  ConfirmDialog,
  confirmDialog,
} from "primereact/confirmdialog";
import { Toast } from "primereact/toast";
import { ProgressSpinner } from "primereact/progressspinner";

import { api } from "../services/api.js";
import { useAuth } from "../auth/AuthProvider.jsx";


export default function Archive() {
  // ================================================================
  // AUTHENTIFICATION / PROJET COURANT
  // ================================================================

  const { me } = useAuth();

  const toast = useRef(null);

  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  const [search, setSearch] = useState("");

  const [dialogVisible, setDialogVisible] =
    useState(false);

  const [title, setTitle] = useState("");
  const [file, setFile] = useState(null);


  // ================================================================
  // IDENTIFIANT DU PROJET COURANT
  // ================================================================

  const projectId =
    me?.current_project?.id ||
    me?.current_project ||
    null;


  // ================================================================
  // CHARGEMENT DES DOCUMENTS
  // ================================================================

  const loadDocuments = async () => {
    if (!projectId) {
      setDocuments([]);
      return;
    }

    setLoading(true);

    try {
      const data =
        await api.archiveDocuments.list({
          project: projectId,
        });

      const rows = Array.isArray(data)
        ? data
        : data?.results || [];

      setDocuments(rows);
    } catch (error) {
      console.error(
        "Erreur chargement archivage :",
        error
      );

      toast.current?.show({
        severity: "error",
        summary: "Erreur",
        detail:
          "Impossible de charger les documents archivés.",
        life: 4000,
      });
    } finally {
      setLoading(false);
    }
  };


  useEffect(() => {
    loadDocuments();
  }, [projectId]);


  // ================================================================
  // RECHERCHE
  // ================================================================

  const filteredDocuments = useMemo(() => {
    const value = search
      .trim()
      .toLowerCase();

    if (!value) {
      return documents;
    }

    return documents.filter((document) => {
      const titleValue =
        document?.title
          ?.toLowerCase() || "";

      const userValue =
        document?.imported_by
          ?.toLowerCase() || "";

      const fileValue =
        document?.file_name
          ?.toLowerCase() || "";

      return (
        titleValue.includes(value) ||
        userValue.includes(value) ||
        fileValue.includes(value)
      );
    });
  }, [documents, search]);


  // ================================================================
  // OUVERTURE DU FORMULAIRE
  // ================================================================

  const openCreateDialog = () => {
    setTitle("");
    setFile(null);
    setDialogVisible(true);
  };


  // ================================================================
  // FERMETURE DU FORMULAIRE
  // ================================================================

  const closeCreateDialog = () => {
    if (saving) {
      return;
    }

    setDialogVisible(false);
    setTitle("");
    setFile(null);
  };


  // ================================================================
  // SELECTION DU FICHIER
  // ================================================================

  const handleFileChange = (event) => {
    const selectedFile =
      event.target.files?.[0];

    setFile(selectedFile || null);
  };


  // ================================================================
  // AJOUT D'UN DOCUMENT
  // ================================================================

  const saveDocument = async () => {
    const cleanTitle = title.trim();

    if (!cleanTitle) {
      toast.current?.show({
        severity: "warn",
        summary: "Champ obligatoire",
        detail:
          "Veuillez saisir le titre du document.",
        life: 3000,
      });

      return;
    }

    if (!file) {
      toast.current?.show({
        severity: "warn",
        summary: "Document obligatoire",
        detail:
          "Veuillez sélectionner un document.",
        life: 3000,
      });

      return;
    }

    if (!projectId) {
      toast.current?.show({
        severity: "warn",
        summary: "Projet",
        detail:
          "Aucun projet actif n'est sélectionné.",
        life: 3000,
      });

      return;
    }

    const formData = new FormData();

    formData.append(
      "title",
      cleanTitle
    );

    formData.append(
      "file",
      file
    );

    formData.append(
      "project",
      String(projectId)
    );

    setSaving(true);

    try {
      await api.archiveDocuments.upload(
        formData
      );

      toast.current?.show({
        severity: "success",
        summary: "Document ajouté",
        detail:
          "Le document a été archivé avec succès.",
        life: 3000,
      });

      setDialogVisible(false);
      setTitle("");
      setFile(null);

      await loadDocuments();
    } catch (error) {
      console.error(
        "Erreur ajout document :",
        error
      );

      const response =
        error?.response?.data;

      let backendMessage = null;

      if (typeof response === "string") {
        backendMessage = response;
      } else {
        backendMessage =
          response?.detail ||
          response?.file?.[0] ||
          response?.title?.[0] ||
          response?.project?.[0];
      }

      toast.current?.show({
        severity: "error",
        summary: "Erreur",
        detail:
          backendMessage ||
          "Impossible d'ajouter le document.",
        life: 4500,
      });
    } finally {
      setSaving(false);
    }
  };


  // ================================================================
  // SUPPRESSION
  // ================================================================

  const deleteDocument = (document) => {
    confirmDialog({
      message:
        `Voulez-vous vraiment supprimer « ${document.title} » ?`,

      header:
        "Supprimer le document",

      icon:
        "pi pi-exclamation-triangle",

      acceptLabel:
        "Supprimer",

      rejectLabel:
        "Annuler",

      acceptClassName:
        "p-button-danger",

      accept: async () => {
        try {
          await api.archiveDocuments.remove(
            document.id
          );

          toast.current?.show({
            severity: "success",
            summary: "Document supprimé",
            detail:
              "Le document a été supprimé avec succès.",
            life: 3000,
          });

          await loadDocuments();
        } catch (error) {
          console.error(
            "Erreur suppression document :",
            error
          );

          toast.current?.show({
            severity: "error",
            summary: "Erreur",
            detail:
              "Impossible de supprimer le document.",
            life: 4000,
          });
        }
      },
    });
  };


  // ================================================================
  // URL DU DOCUMENT
  // ================================================================

  const getDocumentUrl = (document) => {
    const value =
      document?.file ||
      document?.file_url ||
      null;

    if (!value) {
      return null;
    }

    /*
     * Cas normal :
     * Django renvoie /media/archive/...
     */
    if (value.startsWith("/media/")) {
      return value;
    }

    /*
     * Si le backend renvoie une URL absolue, par exemple :
     *
     * http://backend:8000/media/archive/...
     * http://localhost:28000/media/archive/...
     *
     * on extrait uniquement /media/archive/...
     *
     * Le navigateur utilisera alors le même domaine que
     * le frontend :
     *
     * http://localhost:28080/media/...
     *
     * et Nginx servira directement le fichier.
     */
    try {
      const parsedUrl = new URL(
        value,
        window.location.origin
      );

      if (
        parsedUrl.pathname.startsWith(
          "/media/"
        )
      ) {
        return (
          parsedUrl.pathname +
          parsedUrl.search
        );
      }
    } catch (error) {
      console.error(
        "URL du document invalide :",
        value,
        error
      );
    }

    return value;
  };


  // ================================================================
  // OUVRIR / VOIR LE DOCUMENT
  // ================================================================

  const openDocument = (document) => {
    const url =
      getDocumentUrl(document);

    if (!url) {
      toast.current?.show({
        severity: "warn",
        summary: "Document",
        detail:
          "Le fichier n'est pas disponible.",
        life: 3000,
      });

      return;
    }

    window.open(
      url,
      "_blank",
      "noopener,noreferrer"
    );
  };


  // ================================================================
  // TELECHARGER LE DOCUMENT
  // ================================================================

  const downloadDocument = (document) => {
    const url =
      getDocumentUrl(document);

    if (!url) {
      toast.current?.show({
        severity: "warn",
        summary: "Document",
        detail:
          "Le fichier n'est pas disponible.",
        life: 3000,
      });

      return;
    }

    const link =
      window.document.createElement("a");

    link.href = url;

    link.download =
      document?.file_name ||
      document?.title ||
      "document";

    link.style.display = "none";

    window.document.body.appendChild(
      link
    );

    link.click();

    window.document.body.removeChild(
      link
    );
  };


  // ================================================================
  // FORMATAGE DATE
  // ================================================================

  const formatDate = (value) => {
    if (!value) {
      return "—";
    }

    const date = new Date(value);

    if (
      Number.isNaN(
        date.getTime()
      )
    ) {
      return value;
    }

    return new Intl.DateTimeFormat(
      "fr-FR",
      {
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      }
    ).format(date);
  };


  // ================================================================
  // AFFICHAGE DU TITRE
  // ================================================================

  const titleTemplate = (row) => (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: "0.75rem",
      }}
    >
      <div
        style={{
          width: "40px",
          height: "40px",
          borderRadius: "10px",
          background: "#EEF6FD",
          color: "#5B9FE8",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          flexShrink: 0,
        }}
      >
        <i className="pi pi-file" />
      </div>

      <div>
        <div
          style={{
            fontWeight: 600,
            color: "#1E293B",
          }}
        >
          {row.title}
        </div>

        {row.file_name && (
          <div
            style={{
              color: "#64748B",
              fontSize: "0.8rem",
              marginTop: "3px",
            }}
          >
            {row.file_name}
          </div>
        )}
      </div>
    </div>
  );


  // ================================================================
  // AFFICHAGE DE LA DATE
  // ================================================================

  const dateTemplate = (row) => (
    <span
      style={{
        color: "#475569",
      }}
    >
      {formatDate(
        row.created_at
      )}
    </span>
  );


  // ================================================================
  // AFFICHAGE UTILISATEUR
  // ================================================================

  const userTemplate = (row) => (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: "0.55rem",
      }}
    >
      <div
        style={{
          width: "30px",
          height: "30px",
          borderRadius: "50%",
          background: "#EEF6FD",
          color: "#5B9FE8",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <i
          className="pi pi-user"
          style={{
            fontSize: "0.8rem",
          }}
        />
      </div>

      <span
        style={{
          color: "#334155",
        }}
      >
        {row.imported_by || "—"}
      </span>
    </div>
  );


  // ================================================================
  // ACTIONS
  // ================================================================

  const actionsTemplate = (row) => (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: "0.25rem",
      }}
    >
      <Button
        type="button"
        icon="pi pi-eye"
        rounded
        text
        severity="info"
        tooltip="Ouvrir"
        tooltipOptions={{
          position: "top",
        }}
        onClick={() =>
          openDocument(row)
        }
      />

      <Button
        type="button"
        icon="pi pi-download"
        rounded
        text
        severity="info"
        tooltip="Télécharger"
        tooltipOptions={{
          position: "top",
        }}
        onClick={() =>
          downloadDocument(row)
        }
      />

      <Button
        type="button"
        icon="pi pi-trash"
        rounded
        text
        severity="danger"
        tooltip="Supprimer"
        tooltipOptions={{
          position: "top",
        }}
        onClick={() =>
          deleteDocument(row)
        }
      />
    </div>
  );


  // ================================================================
  // PIED DU FORMULAIRE
  // ================================================================

  const dialogFooter = (
    <div
      style={{
        display: "flex",
        justifyContent: "flex-end",
        gap: "0.65rem",
      }}
    >
      <Button
        type="button"
        label="Annuler"
        icon="pi pi-times"
        outlined
        severity="secondary"
        disabled={saving}
        onClick={
          closeCreateDialog
        }
      />

      <Button
        type="button"
        label={
          saving
            ? "Enregistrement..."
            : "Enregistrer"
        }
        icon="pi pi-check"
        loading={saving}
        onClick={
          saveDocument
        }
        style={{
          background: "#5B9FE8",
          borderColor: "#5B9FE8",
        }}
      />
    </div>
  );


  // ================================================================
  // PAGE
  // ================================================================

  return (
    <div
      style={{
        padding: "1.5rem",
      }}
    >
      <Toast ref={toast} />

      <ConfirmDialog />


      {/* ============================================================
          ENTETE
      ============================================================ */}

      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent:
            "space-between",
          gap: "1rem",
          marginBottom: "1.5rem",
          flexWrap: "wrap",
        }}
      >
        <div>
          <h2
            style={{
              margin: 0,
              color: "#1E293B",
              fontSize: "1.55rem",
              fontWeight: 700,
            }}
          >
            Archivage électronique
          </h2>

          <p
            style={{
              margin:
                "0.4rem 0 0 0",
              color: "#64748B",
            }}
          >
            Documents archivés du projet
          </p>
        </div>

        <Button
          type="button"
          label="Ajouter un document"
          icon="pi pi-plus"
          onClick={
            openCreateDialog
          }
          style={{
            background: "#5B9FE8",
            borderColor: "#5B9FE8",
          }}
        />
      </div>


      {/* ============================================================
          BLOC PRINCIPAL
      ============================================================ */}

      <div
        style={{
          background: "#FFFFFF",
          border:
            "1px solid #E2E8F0",
          borderRadius: "14px",
          overflow: "hidden",
          boxShadow:
            "0 1px 3px rgba(15, 23, 42, 0.04)",
        }}
      >

        {/* ==========================================================
            BARRE RECHERCHE
        ========================================================== */}

        <div
          style={{
            padding: "1rem",
            borderBottom:
              "1px solid #E2E8F0",
            display: "flex",
            alignItems: "center",
            justifyContent:
              "space-between",
            gap: "1rem",
            flexWrap: "wrap",
          }}
        >
          <span
            className="p-input-icon-left"
            style={{
              width: "100%",
              maxWidth: "420px",
            }}
          >
            <i className="pi pi-search" />

            <InputText
              value={search}
              onChange={(e) =>
                setSearch(
                  e.target.value
                )
              }
              placeholder="Rechercher un document..."
              style={{
                width: "100%",
              }}
            />
          </span>

          <div
            style={{
              color: "#64748B",
              fontSize: "0.9rem",
            }}
          >
            {filteredDocuments.length}{" "}
            document
            {
              filteredDocuments.length !== 1
                ? "s"
                : ""
            }
          </div>
        </div>


        {/* ==========================================================
            CHARGEMENT / TABLEAU
        ========================================================== */}

        {loading ? (
          <div
            style={{
              minHeight: "250px",
              display: "flex",
              justifyContent:
                "center",
              alignItems: "center",
            }}
          >
            <ProgressSpinner
              style={{
                width: "45px",
                height: "45px",
              }}
            />
          </div>
        ) : (
          <DataTable
            value={
              filteredDocuments
            }
            dataKey="id"
            paginator
            rows={10}
            rowsPerPageOptions={[
              10,
              20,
              50,
            ]}
            emptyMessage="Aucun document archivé."
            responsiveLayout="scroll"
          >
            <Column
              header="Titre du document"
              body={
                titleTemplate
              }
              style={{
                minWidth: "300px",
              }}
            />

            <Column
              header="Date d'import"
              body={
                dateTemplate
              }
              style={{
                minWidth: "180px",
              }}
            />

            <Column
              header="Importé par"
              body={
                userTemplate
              }
              style={{
                minWidth: "190px",
              }}
            />

            <Column
              header="Actions"
              body={
                actionsTemplate
              }
              style={{
                width: "170px",
              }}
            />
          </DataTable>
        )}
      </div>


      {/* ============================================================
          DIALOG AJOUT
      ============================================================ */}

      <Dialog
        header="Ajouter un document"
        visible={dialogVisible}
        style={{
          width: "520px",
          maxWidth: "95vw",
        }}
        modal
        closable={!saving}
        onHide={
          closeCreateDialog
        }
        footer={
          dialogFooter
        }
      >
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            gap: "1.3rem",
            paddingTop: "0.5rem",
          }}
        >

          {/* ========================================================
              TITRE
          ======================================================== */}

          <div>
            <label
              htmlFor="archive-title"
              style={{
                display: "block",
                marginBottom:
                  "0.5rem",
                color: "#1E293B",
                fontWeight: 600,
              }}
            >
              Titre du document
              <span
                style={{
                  color: "#DC2626",
                }}
              >
                {" "}
                *
              </span>
            </label>

            <InputText
              id="archive-title"
              value={title}
              onChange={(e) =>
                setTitle(
                  e.target.value
                )
              }
              placeholder="Ex. Rapport trimestriel"
              style={{
                width: "100%",
              }}
              autoFocus
            />
          </div>


          {/* ========================================================
              DOCUMENT
          ======================================================== */}

          <div>
            <label
              htmlFor="archive-file"
              style={{
                display: "block",
                marginBottom:
                  "0.5rem",
                color: "#1E293B",
                fontWeight: 600,
              }}
            >
              Document
              <span
                style={{
                  color: "#DC2626",
                }}
              >
                {" "}
                *
              </span>
            </label>

            <input
              id="archive-file"
              type="file"
              onChange={
                handleFileChange
              }
              style={{
                width: "100%",
                padding: "0.8rem",
                border:
                  "1px solid #CBD5E1",
                borderRadius: "8px",
                background:
                  "#F8FAFC",
                color:
                  "#1E293B",
              }}
            />

            {file && (
              <div
                style={{
                  marginTop:
                    "0.65rem",
                  padding:
                    "0.7rem 0.8rem",
                  borderRadius:
                    "8px",
                  background:
                    "#EEF6FD",
                  color:
                    "#4A8ED8",
                  fontSize:
                    "0.88rem",
                  display:
                    "flex",
                  alignItems:
                    "center",
                  gap: "0.5rem",
                }}
              >
                <i className="pi pi-file" />

                <span>
                  {file.name}
                </span>
              </div>
            )}
          </div>

        </div>
      </Dialog>
    </div>
  );
}