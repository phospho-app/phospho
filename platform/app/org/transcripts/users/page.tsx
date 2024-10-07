"use client";

import { SetupUsersCallout } from "@/components/callouts/setup-users";
import { UsersDataviz } from "@/components/users/users-dataviz";
import { UsersTable } from "@/components/users/users-table";
import { searchParamsToProjectDataFilters } from "@/lib/utils";
import { useSearchParams } from "next/navigation";

export default function Page() {
  const searchParams = useSearchParams();
  const parsedDataFilters = searchParamsToProjectDataFilters({ searchParams });

  return (
    <div className="flex flex-col space-y-2">
      <SetupUsersCallout />
      <UsersDataviz forcedDataFilters={parsedDataFilters} />
      <UsersTable forcedDataFilters={parsedDataFilters} />
    </div>
  );
}
