import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"
 
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

interface Session {
  id: string;
  created_at: string;
  version_id: string;
  project_id: string;
  metadata: {
    flag: string;
    score: string;
    rating: string;
  };
  data: {};
}

export const countObjectsPerDay = (data: Session[]): Record<string, number>  => {
  return data.reduce((counts, item) => {
    // Convert the Unix timestamp to a date string in 'YYYY-MM-DD' format
    const date = new Date(Number(item.created_at) * 1000).toISOString().split("T")[0];

    // Initialize or increment the count for each day
    counts[date] = (counts[date] || 0) + 1;

    return counts;
  }, {} as Record<string, number>);
};