const COLORS = { GREEN: "#16a34a", AMBER: "#f59e0b", RED: "#dc2626", GREY: "#9ca3af" };

export default function RagIndicator({ status, rate }) {
  return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: "0.4rem" }}>
      <span
        style={{
          width: 12,
          height: 12,
          borderRadius: "50%",
          background: COLORS[status] || COLORS.GREY,
          display: "inline-block",
        }}
      />
      {rate != null && <span>{rate}%</span>}
    </span>
  );
}
