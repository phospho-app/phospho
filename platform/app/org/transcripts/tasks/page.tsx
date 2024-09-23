"use client";

import { SendDataCallout } from "@/components/callouts/import-data";
import TasksDataviz from "@/components/tasks/tasks-dataviz";
import { TasksTable } from "@/components/tasks/tasks-table";
import { searchParamsToProjectDataFilters } from "@/lib/utils";
import { useSearchParams } from "next/navigation";

export default function Page() {
  const searchParams = useSearchParams();
  const parsedDataFilters = searchParamsToProjectDataFilters({ searchParams });

  return (
    <>
      <SendDataCallout />
      <TasksDataviz forcedDataFilters={parsedDataFilters} />
      <TasksTable forcedDataFilters={parsedDataFilters} />
    </>
  );
}
