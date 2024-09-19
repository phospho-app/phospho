"use client";

import { SendDataCallout } from "@/components/callouts/import-data";
import TasksDataviz from "@/components/tasks/tasks-dataviz";
import { TasksTable } from "@/components/tasks/tasks-table";

export default function Page() {
  return (
    <>
      <SendDataCallout />
      <TasksDataviz />
      <TasksTable />
    </>
  );
}
