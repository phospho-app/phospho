import { Event } from "./events";
import { Task } from "./tasks";

export interface Session {
  id: string;
  created_at: number;
  project_id: string;
  metadata?: Record<string, any>;
  data?: Record<string, any>;
  preview?: string;
  environment?: string;
  notes?: string;
}

export interface SessionWithEvents extends Session {
  events: Event[];
}
export interface SessionWithTasks extends Session {
  tasks: Task[];
}
