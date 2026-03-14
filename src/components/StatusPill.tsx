export function statusTone(status: string, suspicion?: number) {
  const value = status.toLowerCase();
  if (suspicion !== undefined) {
    if (suspicion >= 80) return "danger";
    if (suspicion >= 55) return "warn";
  }
  if (value.includes("актив")) return "success";
  if (value.includes("наблю")) return "warn";
  if (value.includes("риск") || value.includes("крит")) return "danger";
  return "neutral";
}

export function StatusPill({ label, tone }: { label: string; tone?: string }) {
  return <span className={`status-pill status-pill--${tone ?? "neutral"}`}>{label}</span>;
}
