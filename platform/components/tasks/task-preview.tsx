import { TaskOverview } from "./task";

function TaskPreview({ task_id }: { task_id: string | null }) {
  if (!task_id) {
    return null;
  }
  return (
    <div className="flex flex-col space-y-4">
      <TaskOverview task_id={task_id} showGoToTask={true} />
    </div>
  );
}

export { TaskPreview };
