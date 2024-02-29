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