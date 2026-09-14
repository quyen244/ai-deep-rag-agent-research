import type { RunStatus, SignalDirection } from "@/lib/contracts";

export function titleCase(value: string): string {
  return value.replace(/_/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export function formatDate(value: string | null): string {
  if (!value) return "Not available";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Not available";
  return new Intl.DateTimeFormat("en-US", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

export function formatDuration(value: number): string {
  if (value < 1_000) return `${Math.round(value)} ms`;
  return `${(value / 1_000).toFixed(1)} s`;
}

export function formatMetric(value: string | number | boolean | null, unit?: string | null): string {
  if (value === null) return "Not available";
  if (typeof value === "boolean") return value ? "Yes" : "No";
  if (typeof value === "number") {
    const formatted = new Intl.NumberFormat("en-US", { maximumFractionDigits: 2 }).format(value);
    if (unit === "percent") return `${formatted}%`;
    return unit ? `${formatted} ${unit}` : formatted;
  }
  return unit ? `${value} ${unit}` : value;
}

export function statusLabel(status: RunStatus): string {
  return titleCase(status);
}

export function directionLabel(direction: SignalDirection): string {
  return direction === "positive" ? "Positive" : direction === "negative" ? "Negative" : "Neutral";
}
