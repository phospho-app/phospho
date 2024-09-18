import { TaskOverview } from "./task";

function TaskPreview({ task_id }: { task_id: string | null }) {
  if (!task_id) {
    return null;
  }
  return (
    <>
      <TaskOverview task_id={task_id} showGoToTask={true} />
    </>
  );
}

export { TaskPreview };
