export interface ABTest {
  version_id: string;
  score: number;
  score_std: number;
  nb_tasks: number;
  first_task_timestamp: number;
}
