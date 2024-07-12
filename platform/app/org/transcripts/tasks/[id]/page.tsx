"use client";

import TaskOverview from "@/components/transcripts/tasks/Task";
import { Button } from "@/components/ui/Button";
import { ChevronLeft } from "lucide-react";
import { useRouter } from "next/navigation";

export default function Page({ params }: { params: { id: string } }) {
  const task_id = decodeURIComponent(params.id);
  const router = useRouter();

  return (
    <>
      <Button
        onClick={() => {
          router.back();
        }}
      >
        <ChevronLeft className="w-4 h-4 mr-1" /> Back
      </Button>
      <TaskOverview key={params.id} task_id={task_id}></TaskOverview>
    </>
  );
}
