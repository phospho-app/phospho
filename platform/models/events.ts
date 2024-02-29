export interface Event {
  id: string;
  created_at: number;
  event_name: string;
  task_id: string;
  session_id: string;
  project_id: string;
  webhook?: string;
  source: string;
}

export interface EventDefinition {
  event_name: string;
  description: string;
}
