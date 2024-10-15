"use client";

import TaskOverview from "@/components/tasks/task";
import { Button } from "@/components/ui/button";
import { ChevronLeft } from "lucide-react";
import { useRouter } from "next/navigation";

export default function Page({ params }: { params: { id: string } }) {
  const task_id = decodeURIComponent(params.id);
  const router = useRouter();

  return (
    <div className="flex flex-col space-y-4">
      <Button
        onClick={() => {
          router.back();
        }}
        className="max-w-[10rem]"
      >
        <ChevronLeft className="w-4 h-4 mr-1" /> Back
      </Button>
      <TaskOverview key={params.id} task_id={task_id}></TaskOverview>
    </div>
  );
}
