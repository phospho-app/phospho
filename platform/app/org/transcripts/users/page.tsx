"use client";

import { SetupUsersCallout } from "@/components/callouts/setup-users";
import { DatePickerWithRange } from "@/components/date-range";
import { UsersDataviz } from "@/components/users/users-dataviz";
import { UsersTable } from "@/components/users/users-table";
import { searchParamsToProjectDataFilters } from "@/lib/utils";
import { useSearchParams } from "next/navigation";

export default function Page() {
  const searchParams = useSearchParams();
  const parsedDataFilters = searchParamsToProjectDataFilters({ searchParams });

  return (
    <div className="flex flex-col gap-y-2">
      <SetupUsersCallout />
      <DatePickerWithRange />
      <UsersDataviz forcedDataFilters={parsedDataFilters} />
      <UsersTable forcedDataFilters={parsedDataFilters} />
    </div>
  );
}
