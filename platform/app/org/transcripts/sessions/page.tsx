"use client";

import { SendDataCallout } from "@/components/callouts/import-data";
import { SetupSessionCallout } from "@/components/callouts/setup-sessions";
import { SessionsDataviz } from "@/components/sessions/session-dataviz";
import { SessionsTable } from "@/components/sessions/sessions-table";
import { searchParamsToProjectDataFilters } from "@/lib/utils";
import { navigationStateStore } from "@/store/store";
import { useSearchParams } from "next/navigation";
import { useEffect } from "react";

export default function Page() {
  const searchParams = useSearchParams();
  const parsedDataFilters = searchParamsToProjectDataFilters({ searchParams });
  const setDataFilters = navigationStateStore((state) => state.setDataFilters);

  useEffect(() => {
    // If the parsedDataFilters are not null, set the data filters
    if (parsedDataFilters !== null) {
      setDataFilters(parsedDataFilters);
    }
  }, [parsedDataFilters]);

  return (
    <>
      <SendDataCallout />
      <SetupSessionCallout />
      <SessionsDataviz />
      <SessionsTable />
    </>
  );
}
