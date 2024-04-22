export interface Task {
  id: string;
  created_at: number;
  project_id: string;
  session_id: string;
  input: string;
  additional_input?: Record<string, any>;
  output?: string;
  additional_output?: Record<string, any>;
  metadata?: Record<string, any>;
  data?: Record<string, any>;
  flag?: string;
  last_eval?: Eval;
  environment?: string;
  notes?: string;
  topics?: string[];
}

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

export interface TaskWithEvents extends Task {
  events: Event[];
}

export interface UsageQuota {
  org_id: string;
  plan: string;
  current_usage: number;
  max_usage: number;
  max_usage_label: string;
}

export interface OrgMetadata {
  org_id: string;
  plan?: string | null; // "hobby" or "pro"
  customer_id?: string | null; // Stripe customer id
  initialized?: boolean | null; // Whether the org has been initialized
}

export interface Session {
  id: string;
  created_at: number;
  project_id: string;
  metadata?: Record<string, any>;
  data?: Record<string, any>;
  preview?: string;
  environment?: string;
  notes?: string;
  session_length?: number;
}

export interface SessionWithEvents extends Session {
  events: Event[];
}
export interface SessionWithTasks extends Session {
  tasks: Task[];
}

export interface UserMetadata {
  user_id: string;
  nb_tasks: number;
  avg_success_rate: number;
  avg_session_length: number;
  total_tokens: number;
  events: Event[];
  tasks_id: string[];
  sessions: Session[];
}

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

export enum DetectionEngine {
  LLM = "llm_detection",
  KEYWORD = "keyword_detection",
  REGEX = "regex_detection",
}

export enum DetectionScope {
  Task = "task",
  Session = "session",
  TaskInputOnly = "task_input_only",
  TaskOutputOnly = "task_output_only",
}

export interface EventDefinition {
  event_name: string;
  description: string;
  webhook?: string;
  webhook_headers?: Record<string, string> | null;
  detection_engine?: DetectionEngine;
  detection_scope: DetectionScope;
  keywords?: string;
  regex_pattern?: string;
  job_id?: string;
}

export interface ABTest {
  version_id: string;
  score: number;
  score_std: number;
  nb_tasks: number;
  first_task_timestamp: number;
}

export interface ProjectSettings {
  events: Record<string, EventDefinition>;
}

export interface Project {
  id: string;
  created_at: number;
  project_name: string;
  org_id: string;
  settings?: ProjectSettings;
}

export interface HasEnoughLabelledTasks {
  project_id: string;
  enough_labelled_tasks: number;
  has_enough_labelled_tasks: boolean;
  currently_labelled_tasks: number;
}

export interface Test {
  id: string;
  project_id: string;
  created_by: string;
  created_at: number;
  last_updated_at: number;
  terminated_at?: number;
  status: string;
  summary?: Record<string, any>;
}

export interface Topic {
  topic_name: string;
  count: number;
}
