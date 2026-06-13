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

// fields: [{ name, label, type, options?, required?, optionLabel?, optionValue? }]
export default function EntityFormDialog({ visible, onHide, fields, initial, onSubmit, title }) {
  const { t } = useTranslation();
  const [values, setValues] = useState({});
  const [errors, setErrors] = useState({});
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    setValues(initial || {});
    setErrors({});
  }, [initial, visible]);

  const set = (name, v) => setValues((s) => ({ ...s, [name]: v }));

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
        for (const [k, v] of Object.entries(data)) {
          mapped[k] = Array.isArray(v) ? v.join(" ") : String(v);
        }
        setErrors(mapped);
      }
    } finally {
      setSaving(false);
    }
  };

  const renderField = (f) => {
    const v = values[f.name];
    const common = { id: f.name, className: "w-100" };
    switch (f.type) {
      case "number":
        return (
          <InputNumber
            {...common}
            value={v ?? null}
            onValueChange={(e) => set(f.name, e.value)}
            mode="decimal"
            minFractionDigits={0}
            maxFractionDigits={2}
          />
        );
      case "textarea":
        return (
          <InputTextarea {...common} value={v ?? ""} onChange={(e) => set(f.name, e.target.value)} rows={3} />
        );
      case "dropdown":
        return (
          <Dropdown
            {...common}
            value={v ?? null}
            options={f.options || []}
            optionLabel={f.optionLabel || "label"}
            optionValue={f.optionValue || "value"}
            onChange={(e) => set(f.name, e.value)}
            filter
            showClear={!f.required}
          />
        );
      case "date":
        return (
          <Calendar
            {...common}
            value={v ? new Date(v) : null}
            onChange={(e) =>
              set(f.name, e.value ? e.value.toISOString().slice(0, 10) : null)
            }
            dateFormat="yy-mm-dd"
            showIcon
          />
        );
      case "checkbox":
        return <Checkbox checked={!!v} onChange={(e) => set(f.name, e.checked)} />;
      default:
        return <InputText {...common} value={v ?? ""} onChange={(e) => set(f.name, e.target.value)} />;
    }
  };

  return (
    <Dialog header={title} visible={visible} onHide={onHide} style={{ width: "40rem" }} maximizable>
      <div className="row g-3">
        {(fields || []).map((f) => (
          <div className={f.full ? "col-12" : "col-12 col-md-6"} key={f.name}>
            <label htmlFor={f.name} className="form-label">
              {f.label}
              {f.required && <span className="text-danger"> *</span>}
            </label>
            {renderField(f)}
            {errors[f.name] && <div className="text-danger small">{errors[f.name]}</div>}
          </div>
        ))}
      </div>
      {errors.detail && <div className="text-danger mt-2">{errors.detail}</div>}
      <div className="d-flex justify-content-end gap-2 mt-3">
        <Button label={t("common.cancel")} text onClick={onHide} />
        <Button label={t("common.save")} loading={saving} onClick={submit} />
      </div>
    </Dialog>
  );
}
