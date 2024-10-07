"use client";

import { SendDataCallout } from "@/components/callouts/import-data";
import { SetupSessionCallout } from "@/components/callouts/setup-sessions";
import { DatePickerWithRange } from "@/components/date-range";
import { SessionsDataviz } from "@/components/sessions/session-dataviz";
import { SessionsTable } from "@/components/sessions/sessions-table";
import { searchParamsToProjectDataFilters } from "@/lib/utils";
import { useSearchParams } from "next/navigation";

export default function Page() {
  const searchParams = useSearchParams();
  const parsedDataFilters = searchParamsToProjectDataFilters({ searchParams });

  return (
    <div className="flex flex-col space-y-2">
      <SendDataCallout />
      <SetupSessionCallout />
      <DatePickerWithRange />
      <SessionsDataviz forcedDataFilters={parsedDataFilters} />
      <SessionsTable forcedDataFilters={parsedDataFilters} />
    </div>
  );
}
