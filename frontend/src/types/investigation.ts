export type InvestigationStatus =
  | "OPEN"
  | "IN_PROGRESS"
  | "COMPLETED"
  | "FAILED";

export interface InvestigationCreate {
  title: string;
  description?: string | null;
}

export interface Investigation {
  id: number;
  title: string;
  description: string | null;
  status: InvestigationStatus;
  user_id: number;
  created_at: string;
  updated_at: string;
  summary?: string | null;
  root_cause?: string | null;
  failed_component?: string | null;
  severity?: string | null;
  confidence?: number | null;
  additional_notes?: string | null;
}