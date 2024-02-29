import { Event } from "./events";
import { Eval } from "./evals";
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

export interface TaskWithEvents extends Task {
    events: Event[];
}