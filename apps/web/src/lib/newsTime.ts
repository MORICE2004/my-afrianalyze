// News time labels, usable on the server and in the browser.
const TZ = "Africa/Dar_es_Salaam";

// Labels come from actual timestamps in East Africa Time. Nothing is ever called "breaking".
export function timeBucket(iso: string, now = new Date()): "Today" | "This week" | "Earlier" {
  const day = (d: Date) => d.toLocaleDateString("en-CA", { timeZone: TZ });
  if (day(new Date(iso)) === day(now)) return "Today";
  return now.getTime() - new Date(iso).getTime() < 7 * 864e5 ? "This week" : "Earlier";
}

export function newsTime(iso: string, now = new Date()): string {
  const d = new Date(iso);
  if (timeBucket(iso, now) === "Today") return `${d.toLocaleTimeString("en-GB", { timeZone: TZ, hour: "2-digit", minute: "2-digit" })} EAT`;
  return d.toLocaleDateString("en-GB", { timeZone: TZ, day: "numeric", month: "short", year: "numeric" });
}
