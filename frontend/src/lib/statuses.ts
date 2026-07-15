import type { ApplicationStatus } from "./types";

export const STATUS_OPTIONS: ApplicationStatus[] = [
  "not_applied",
  "recommended",
  "ready_to_apply",
  "applied",
  "interview",
  "offer",
  "rejected",
  "withdrawn",
];

export const STATUS_LABELS: Record<ApplicationStatus, string> = {
  not_applied: "Not applied",
  recommended: "Recommended",
  ready_to_apply: "Ready to apply",
  applied: "Applied",
  interview: "Interview",
  offer: "Offer",
  rejected: "Rejected",
  withdrawn: "Withdrawn",
};

export const STATUS_COLORS: Record<ApplicationStatus, string> = {
  not_applied: "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300",
  recommended: "bg-blue-100 text-blue-700 dark:bg-blue-950 dark:text-blue-300",
  ready_to_apply: "bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-300",
  applied: "bg-indigo-100 text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300",
  interview: "bg-purple-100 text-purple-700 dark:bg-purple-950 dark:text-purple-300",
  offer: "bg-green-100 text-green-700 dark:bg-green-950 dark:text-green-300",
  rejected: "bg-red-100 text-red-700 dark:bg-red-950 dark:text-red-300",
  withdrawn: "bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-400",
};
