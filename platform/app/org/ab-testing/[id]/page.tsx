"use client";

import { TasksTable } from "@/components/transcripts/tasks/tasks-table";
import { Button } from "@/components/ui/button";
import { navigationStateStore } from "@/store/store";
import { ChevronLeft } from "lucide-react";
import { useRouter } from "next/navigation";
import { use, useEffect } from "react";

export default function Page({ params }: { params: { id: string } }) {
  const router = useRouter();
  const version_id =
    params.id === "None" ? null : decodeURIComponent(params.id);
  const dataFilters = navigationStateStore((state) => state.dataFilters);
  const setDataFilters = navigationStateStore((state) => state.setDataFilters);

  if (dataFilters.metadata?.version_id !== version_id) {
    setDataFilters({
      ...dataFilters,
      metadata: {
        version_id: version_id,
      },
    });
  }

  // On component unmount, remove the version_id filter
  useEffect(() => {
    return () => {
      delete dataFilters.metadata?.version_id;
      setDataFilters({
        ...dataFilters,
      });
    };
  }, []);

  return (
    <>
      <Button onClick={() => router.back()}>
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
