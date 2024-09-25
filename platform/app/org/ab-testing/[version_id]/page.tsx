"use client";

import { TasksTable } from "@/components/tasks/tasks-table";
import { Button } from "@/components/ui/button";
import { navigationStateStore } from "@/store/store";
import { ChevronLeft } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function Page({ params }: { params: { version_id: string } }) {
  const version_id = decodeURIComponent(params.version_id);
  const router = useRouter();
  const setDateRangePreset = navigationStateStore(
    (state) => state.setDateRangePreset,
  );

  useEffect(() => {
    setDateRangePreset("all-time");
  }, [setDateRangePreset]);

  return (
    <>
      <Button onClick={() => router.back()}>
        <ChevronLeft className="w-4 h-4 mr-1" /> Back
      </Button>
      <div>
        <div className="pb-4">
          <div className="text-2xl font-bold tracking-tight mr-8">
            Messages of version &apos;{version_id}&apos;
          </div>
        </div>
        <div className="hidden h-full flex-1 flex-col space-y-2 md:flex relative">
          <TasksTable forcedDataFilters={{ version_id: version_id }} />
        </div>
      </div>
    </>
  );
}
