"use client";

import TaskOverview from "@/components/transcripts/tasks/task";
import { Button } from "@/components/ui/button";
import { ChevronLeft } from "lucide-react";
import { useRouter } from "next/navigation";

export default function Page({ params }: { params: { id: string } }) {
  const task_id = decodeURIComponent(params.id);
  const router = useRouter();

  return (
    <>
      <Button onClick={() => router.push("/org/transcripts/tasks/")}>
        <ChevronLeft className="w-4 h-4 mr-1" /> Back to Tasks
      </Button>
      <TaskOverview key={params.id} task_id={task_id}></TaskOverview>
    </>
  );
}
