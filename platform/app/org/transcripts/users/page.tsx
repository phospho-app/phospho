"use client";

import { SetupUsersCallout } from "@/components/callouts/setup-users";
import { UsersDataviz } from "@/components/users/users-dataviz";
import { UsersTable } from "@/components/users/users-table";
import { searchParamsToProjectDataFilters } from "@/lib/utils";
import { navigationStateStore } from "@/store/store";
import { useSearchParams } from "next/navigation";
import { useEffect } from "react";

export default function Page() {
  const searchParams = useSearchParams();
  const parsedDataFilters = searchParamsToProjectDataFilters({ searchParams });

  return (
    <>
      <SetupUsersCallout />
      <UsersDataviz />
      <UsersTable parsedDataFilters={parsedDataFilters} />
    </>
  );
}
