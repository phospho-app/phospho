export interface Eval {
  id: string;
  created_at: number;
  project_id: string;
  session_id: string;
  task_id: string;
  value: string;
  source: string;
  notes?: string | null;
}
