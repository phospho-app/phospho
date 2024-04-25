import { format } from "date-fns";

// Utility function to format Unix timestamp to a short date format
export function formatUnixTimestampToShortDate(timestamp: number): string {
  const date = new Date(timestamp * 1000); // Convert Unix timestamp to milliseconds
  return format(date, "MM/dd/yyyy");
}

// Utility function to format Unix timestamp to "Mon dd yyyy" format
export function formatUnixTimestampToLiteralShortDate(
  timestamp: number,
): string {
  const date = new Date(timestamp * 1000); // Convert Unix timestamp to milliseconds
  return format(date, "MMM dd yyyy");
}

// Convert
export function formatUnixTimestampToLiteralDatetime(
  timestamp: number,
): string {
  const date = new Date(timestamp * 1000); // Convert Unix timestamp to milliseconds
  // Don't format if the date is invalid
  if (isNaN(date.getTime())) {
    return "Invalid date";
  }
  return format(date, "yyyy MMMM dd, HH:mm:ss");
}

// Convert to the ISO standard
export function formatUnixTimestampToISO(timestamp: number): string {
  const date = new Date(timestamp * 1000); // Convert Unix timestamp to milliseconds
  return format(date, "yyyy-MM-dd'T'HH:mm:ssXX");
}
