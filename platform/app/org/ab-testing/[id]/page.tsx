"use client";

import { TasksTable } from "@/components/tasks/tasks-table";
import { Button } from "@/components/ui/button";
import { navigationStateStore } from "@/store/store";
import { ChevronLeft } from "lucide-react";
import { useRouter } from "next/navigation";

export default function Page({ params }: { params: { id: string } }) {
  const router = useRouter();
  const version_id = decodeURIComponent(params.id);
  const dataFilters = navigationStateStore((state) => state.dataFilters);
  const setDataFilters = navigationStateStore((state) => state.setDataFilters);
  const setDateRangePreset = navigationStateStore(
    (state) => state.setDateRangePreset,
  );

  if (dataFilters.metadata?.version_id !== version_id) {
    setDateRangePreset("all-time");
    setDataFilters({
      ...dataFilters,
      created_at_start: null,
      created_at_end: null,
      metadata: {
        version_id: version_id,
      },
    });
  }

  function backClick() {
    setDataFilters({
      ...dataFilters,
      created_at_end: undefined,
      created_at_start: Date.now() / 1000 - 7 * 24 * 60 * 60,
    });
    setDateRangePreset("last-7-days");
    // TODO: For some reason, the metadata is not being reset here
    router.back();
  }

  return (
    <>
      <Button onClick={backClick}>
        <ChevronLeft className="w-4 h-4 mr-1" /> Back
      </Button>
      {
        <div className="hidden h-full flex-1 flex-col space-y-2 md:flex relative">
          <TasksTable />
        </div>
      }
    </>
  );
}
