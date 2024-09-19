"use client";

import { SendDataCallout } from "@/components/callouts/import-data";
import { SetupSessionCallout } from "@/components/callouts/setup-sessions";
import { SessionsDataviz } from "@/components/sessions/session-dataviz";
import { SessionsTable } from "@/components/sessions/sessions-table";
// import { useSearchParams } from "next/navigation";
import React from "react";

export default function Page() {
  return (
    <>
      <SendDataCallout />
      <SetupSessionCallout />
      <SessionsDataviz />
      <SessionsTable />
    </>
  );
}
