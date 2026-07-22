export function getLevelVariant(level: string): string {
  if (level === "critical") return "danger";
  if (level === "warning") return "warning";
  return "success";
}


export function getProcessingVariant(status: string): string {
  if (status === "failed") return "danger";
  if (status === "processing") return "warning";
  if (status === "processed") return "success";
  return "secondary";
}
