import { Card } from "primereact/card";

import RagIndicator from "./RagIndicator.jsx";

export default function KpiCard({ title, value, target, rate, rag, unit }) {
  return (
    <Card className="h-100">
      <div style={{ fontSize: "0.8rem", color: "#64748b" }}>{title}</div>
      <div style={{ fontSize: "1.6rem", fontWeight: 700 }}>
        {value ?? "—"}
        {unit === "PERCENTAGE" ? "%" : ""}
      </div>
      {target != null && (
        <div style={{ fontSize: "0.8rem", color: "#64748b" }}>Cible : {target}</div>
      )}
      {(rate != null || rag) && (
        <div className="mt-2">
          <RagIndicator status={rag} rate={rate} />
        </div>
      )}
    </Card>
  );
}
