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
  human_eval?: HumanEval;
  last_eval?: Eval;
  sentiment?: SentimentObject;
  language?: string;
  notes?: string;
  task_position: number;
  is_last_task: boolean;
}

export interface HumanEval {
  flag: string;
}

export interface SentimentObject {
  score: number;
  magnitude: number;
  label: string;
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
  balance_transaction: number;
  next_invoice_total: number;
  next_invoice_amount_due: number;
}

export interface OrgMetadata {
  org_id: string;
  plan?: string | null; // "hobby" or "pro"
  customer_id?: string | null; // Stripe customer id
  initialized?: boolean | null; // Whether the org has been initialized
  argilla_workspace_id?: string | null; // Argilla workspace id
  power_bi?: string | null; // Power BI workspace id
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
  stats: Stats;
  last_message_ts?: number;
}

export interface Stats {
  avg_sentiment_score: number;
  avg_magnitude_score: number;
  most_common_sentiment_label: string;
  most_common_language: string;
  most_common_flag: string;
  human_eval: string;
}

export interface SessionWithEvents extends Session {
  events: Event[];
  tasks: Task[];
  users: UserMetadata[];
}

export interface UserMetadata {
  user_id: string;
  nb_tasks: number;
  avg_success_rate: number;
  avg_session_length: number;
  total_tokens: number;
  events: Event[];
  tasks_id: string[];
  first_message_ts: number;
  last_message_ts: number;
}

export interface ScoreRange {
  min: number;
  max: number;
  value: number;
  score_type: ScoreRangeType;
  label: string;
  options_confidence: Record<string | number, number>;
  corrected_label?: string;
  corrected_value?: number;
}

export interface Event {
  id: string;
  created_at: number;
  event_name: string;
  task_id?: string;
  session_id?: string;
  project_id: string;
  webhook?: string;
  source: string;
  score_range?: ScoreRange;
  confirmed: boolean;
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
  SystemPrompt = "system_prompt",
}

export enum ScoreRangeType {
  confidence = "confidence",
  range = "range",
  category = "category",
}

export interface ScoreRangeSettings {
  min: number;
  max: number;
  score_type: ScoreRangeType;
  categories?: string[];
}

export interface EventDefinition {
  id?: string;
  event_version_id?: number;
  created_at?: number;
  project_id: string;
  org_id: string;
  event_name: string;
  description: string;
  webhook?: string;
  webhook_headers?: Record<string, string> | null;
  detection_engine?: DetectionEngine;
  detection_scope: DetectionScope;
  keywords?: string;
  regex_pattern?: string;
  job_id?: string;
  score_range_settings?: ScoreRangeSettings;
  is_last_task?: boolean;
}

export interface ABTest {
  version_id: string;
  score: number;
  score_std?: number;
  nb_tasks: number;
  first_task_ts: number;
  last_task_ts: number;
  confidence_interval?: number[];
}

export interface SentimentThreshold {
  score: number;
  magnitude: number;
}

export interface DashboardTile {
  id: string;
  tile_name: string;
  metric: string;
  breakdown_by: string;
  metadata_metric?: string;
  scorer_id?: string;
  x?: number;
  y?: number;
  w: number;
  h: number;
}

export interface ProjectSettings {
  events: Record<string, EventDefinition>;
  sentiment_threshold: SentimentThreshold;
  run_evals?: boolean;
  run_sentiment?: boolean;
  run_language?: boolean;
  run_event_detection?: boolean;
  dashboard_tiles: DashboardTile[];
  analytics_threshold_enabled?: boolean;
  analytics_threshold?: number;
}

export interface Project {
  id: string;
  created_at: number;
  project_name: string;
  org_id: string;
  settings?: ProjectSettings;
}

export interface ProjectsData {
  projects: Project[];
}

export interface PostgresCredentials {
  org_id: string;
  server: string;
  database: string;
  username: string;
  password: string;
  projects_started: string[];
  projects_finished: string[];
}

export interface HasEnoughLabelledTasks {
  project_id: string;
  enough_labelled_tasks: number;
  has_enough_labelled_tasks: boolean;
  currently_labelled_tasks: number;
}

export interface Cluster {
  id: string;
  clustering_id: string;
  project_id: string;
  org_id: string;
  created_at: number;
  name: string;
  description: string;
  size: number;
  scope: "messages" | "sessions" | "users";
  tasks_ids: string[] | null;
  sessions_ids: string[] | null;
  users_ids: string[] | null;
}

export interface Clustering {
  id: string;
  clustering_id: string;
  project_id: string;
  org_id: string;
  created_at: number;
  type?: string;
  nb_clusters?: number;
  clusters_ids: string[];
  status?:
    | "started"
    | "summaries"
    | "completed"
    | "loading_existing_embeddings"
    | "generate_clusters"
    | "generating_new_embeddings"
    | "generate_clusters_description_and_title"
    | "merging_similar_clusters"
    | "saving_clusters";
  percent_of_completion?: number;
  clusters?: Cluster[] | null;
  scope: "messages" | "sessions";
  name?: string;
  instruction?: string;
  model?: string;
  clustering_mode?: "agglomerative" | "dbscan";
}

export interface CustomDateRange {
  from: Date | undefined;
  to: Date | undefined;
  created_at_start: number | undefined;
  created_at_end: number | undefined;
}

export interface MetadataFieldsToUniqueValues {
  [key: string]: string[];
}
export interface MetadataTypeToFieldsToUniqueValues {
  number: MetadataFieldsToUniqueValues;
  string: MetadataFieldsToUniqueValues;
}

export interface EvaluationModelDefinition {
  project_id: string;
  system_prompt: string;
}

export interface EvaluationModel {
  project_id: string;
  system_prompt: string;
  created_at: number;
  id: number;
  removed: boolean;
}

export interface ProjectDataFilters {
  created_at_start?: number | null;
  created_at_end?: number | null;
  event_name?: string[] | null;
  flag?: string | null;
  metadata?: Record<string, any> | null;
  user_id?: string | null;
  last_eval_source?: string | null;
  sentiment?: string | null;
  language?: string | null;
  has_notes?: boolean | null;
  tasks_ids?: string[] | null;
  clustering_id?: string | null;
  clusters_ids?: string[] | null;
  is_last_task?: boolean | null;
  session_ids?: string[] | null;
  version_id?: string | null;
}

export interface DatavizSorting {
  id: "breakdown_by" | "metric";
  desc: boolean;
}
