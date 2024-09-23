"use client";

import { SendDataCallout } from "@/components/callouts/import-data";
import { SetupSessionCallout } from "@/components/callouts/setup-sessions";
import { SessionsDataviz } from "@/components/sessions/session-dataviz";
import { SessionsTable } from "@/components/sessions/sessions-table";
import { searchParamsToProjectDataFilters } from "@/lib/utils";
import { useSearchParams } from "next/navigation";

export default function Page() {
  const searchParams = useSearchParams();
  const parsedDataFilters = searchParamsToProjectDataFilters({ searchParams });

  return (
    <>
      <SendDataCallout />
      <SetupSessionCallout />
      <SessionsDataviz forcedDataFilters={parsedDataFilters} />
      <SessionsTable forcedDataFilters={parsedDataFilters} />
    </>
  );
}
