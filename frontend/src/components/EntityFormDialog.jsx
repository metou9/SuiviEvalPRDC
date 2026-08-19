import { useEffect, useState } from "react";
import { Button } from "primereact/button";
import { Calendar } from "primereact/calendar";
import { Checkbox } from "primereact/checkbox";
import { Dialog } from "primereact/dialog";
import { Dropdown } from "primereact/dropdown";
import { InputNumber } from "primereact/inputnumber";
import { InputText } from "primereact/inputtext";
import { InputTextarea } from "primereact/inputtextarea";
import { useTranslation } from "react-i18next";

/*
 * fields:
 *
 * [
 *   {
 *     name,
 *     label,
 *     type,
 *     options?,
 *     required?,
 *     optionLabel?,
 *     optionValue?,
 *     visible?,
 *   }
 * ]
 *
 * options peut être :
 *
 *   - un tableau
 *   - une fonction (values) => tableau
 *
 * visible peut être :
 *
 *   - true / false
 *   - une fonction (values) => true / false
 */

export default function EntityFormDialog({
  visible,
  onHide,
  fields,
  initial,
  onSubmit,
  title,
  onValuesChange,
}) {
  const { t } = useTranslation();

  const [values, setValues] = useState({});
  const [errors, setErrors] = useState({});
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    setValues(initial || {});
    setErrors({});
  }, [initial, visible]);


  // ------------------------------------------------------------------
  // Modification d'une valeur du formulaire
  // ------------------------------------------------------------------

  const set = (name, value) => {
    setValues((current) => {
      const next = {
        ...current,
        [name]: value,
      };

      onValuesChange?.(next);

      return next;
    });
  };


  // ------------------------------------------------------------------
  // Visibilité dynamique d'un champ
  // ------------------------------------------------------------------

  const isFieldVisible = (field) => {
    if (typeof field.visible === "function") {
      return field.visible(values);
    }

    if (field.visible === false) {
      return false;
    }

    return true;
  };


  // ------------------------------------------------------------------
  // Options dynamiques
  // ------------------------------------------------------------------

  const getFieldOptions = (field) => {
    if (typeof field.options === "function") {
      return field.options(values) || [];
    }

    return field.options || [];
  };


  // ------------------------------------------------------------------
  // Soumission
  // ------------------------------------------------------------------

  const submit = async () => {
    setSaving(true);
    setErrors({});

    try {
      await onSubmit(values);
      onHide();
    } catch (e) {
      const data = e?.response?.data;

      if (data && typeof data === "object") {
        const mapped = {};

        for (const [key, value] of Object.entries(data)) {
          mapped[key] = Array.isArray(value)
            ? value.join(" ")
            : String(value);
        }

        setErrors(mapped);
      }
    } finally {
      setSaving(false);
    }
  };


  // ------------------------------------------------------------------
  // Rendu d'un champ
  // ------------------------------------------------------------------

  const renderField = (field) => {
    const value = values[field.name];

    const common = {
      id: field.name,
      className: "w-100",
    };

    switch (field.type) {

      case "number":
        return (
          <InputNumber
            {...common}
            value={value ?? null}
            onValueChange={(e) =>
              set(field.name, e.value)
            }
            mode="decimal"
            minFractionDigits={0}
            maxFractionDigits={2}
          />
        );


      case "textarea":
        return (
          <InputTextarea
            {...common}
            value={value ?? ""}
            onChange={(e) =>
              set(field.name, e.target.value)
            }
            rows={3}
          />
        );


      case "dropdown":
        return (
          <Dropdown
            {...common}
            value={value ?? null}
            options={getFieldOptions(field)}
            optionLabel={field.optionLabel || "label"}
            optionValue={field.optionValue || "value"}
            onChange={(e) =>
              set(field.name, e.value)
            }
            filter
            showClear={!field.required}
          />
        );


      case "date":
        return (
          <Calendar
            {...common}
            value={
              value
                ? new Date(value)
                : null
            }
            onChange={(e) =>
              set(
                field.name,
                e.value
                  ? e.value.toISOString().slice(0, 10)
                  : null
              )
            }
            dateFormat="yy-mm-dd"
            showIcon
          />
        );


      case "checkbox":
        return (
          <Checkbox
            checked={!!value}
            onChange={(e) =>
              set(field.name, e.checked)
            }
          />
        );


      default:
        return (
          <InputText
            {...common}
            value={value ?? ""}
            onChange={(e) =>
              set(field.name, e.target.value)
            }
          />
        );
    }
  };


  // ------------------------------------------------------------------
  // Interface
  // ------------------------------------------------------------------

  return (
    <Dialog
      header={title}
      visible={visible}
      onHide={onHide}
      style={{ width: "40rem" }}
      maximizable
    >
      <div className="row g-3">

        {(fields || [])
          .filter(isFieldVisible)
          .map((field) => (

            <div
              className={
                field.full
                  ? "col-12"
                  : "col-12 col-md-6"
              }
              key={field.name}
            >

              <label
                htmlFor={field.name}
                className="form-label"
              >
                {field.label}

                {field.required && (
                  <span className="text-danger">
                    {" "}*
                  </span>
                )}
              </label>

              {renderField(field)}

              {errors[field.name] && (
                <div className="text-danger small">
                  {errors[field.name]}
                </div>
              )}

            </div>
          ))}

      </div>


      {errors.detail && (
        <div className="text-danger mt-2">
          {errors.detail}
        </div>
      )}


      <div className="d-flex justify-content-end gap-2 mt-3">

        <Button
          label={t("common.cancel")}
          text
          onClick={onHide}
        />

        <Button
          label={t("common.save")}
          loading={saving}
          onClick={submit}
        />

      </div>

    </Dialog>
  );
}