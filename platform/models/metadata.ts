import { Event } from "./events";
import { Task } from "./tasks";
import { Session } from "./sessions";

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
