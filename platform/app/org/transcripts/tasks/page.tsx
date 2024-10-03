"use client";

import { SendDataCallout } from "@/components/callouts/import-data";
import { DatePickerWithRange } from "@/components/date-range";
import TasksDataviz from "@/components/tasks/tasks-dataviz";
import { TasksTable } from "@/components/tasks/tasks-table";
import { searchParamsToProjectDataFilters } from "@/lib/utils";
import { useSearchParams } from "next/navigation";
import useSWR from "swr";

export default function Page() {
  const searchParams = useSearchParams();
  const parsedDataFilters = searchParamsToProjectDataFilters({ searchParams });

  return (
    <>
      <SendDataCallout />
      <DatePickerWithRange />
      <TasksDataviz forcedDataFilters={parsedDataFilters} />
      <TasksTable forcedDataFilters={parsedDataFilters} />
    </>
  );
}
