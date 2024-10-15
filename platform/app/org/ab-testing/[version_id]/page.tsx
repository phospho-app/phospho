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
    <div className="flex flex-col space-y-4">
      <Button onClick={() => router.back()} className="max-w-[10rem]">
        <ChevronLeft className="w-4 h-4 mr-1" /> Back
      </Button>
      <div className="text-2xl font-bold tracking-tight">
        Messages of version &apos;{version_id}&apos;
      </div>
      <TasksTable forcedDataFilters={{ version_id: version_id }} />
    </div>
  );
}
