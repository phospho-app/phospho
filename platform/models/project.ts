export interface Project {
  id: string;
  created_at: number;
  project_name: string;
  org_id: string;
  settings: Record<string, any>;
}

export interface HasEnoughLabelledTasks {
  project_id: string;
  enough_labelled_tasks: number;
  has_enough_labelled_tasks: boolean;
  currently_labelled_tasks: number;
}
