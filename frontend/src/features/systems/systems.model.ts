import type { Account, Ticket } from "@/features/candidates/candidates.model";

export type SystemContents = {
  key: string;
  name: string;
  name_ar: string;
  kind: string;
  accounts: Account[];
  tickets: Ticket[];
};
