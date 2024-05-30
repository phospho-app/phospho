"use client";

import { TasksTable } from "@/components/transcripts/tasks/tasks-table";
import { Button } from "@/components/ui/button";
import { authFetcher } from "@/lib/fetcher";
import { navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import { ChevronLeft } from "lucide-react";
import { useRouter } from "next/navigation";
import useSWR from "swr";

export default function Page({ params }: { params: { id: string } }) {
  const router = useRouter();
  const { accessToken } = useUser();
  const project_id = navigationStateStore((state) => state.project_id);
  const topic_id = decodeURIComponent(params.id);

  // todo: fetch from server
  const { data: topic } = useSWR(
    project_id
      ? [`/api/explore/${project_id}/topics/${topic_id}`, accessToken]
      : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "POST"),
    { keepPreviousData: true },
  );
  const tasks_ids = topic?.tasks_ids;

  return (
    <>
      <Button onClick={() => router.back()}>
        <ChevronLeft className="w-4 h-4 mr-1" /> Back
      </Button>
      {topic?.name && (
        <div className="text-3xl font-bold tracking-tight mr-8">
          Topic '{topic.name}'
        </div>
      )}
      <div className="hidden h-full flex-1 flex-col space-y-2 md:flex relative">
        <TasksTable tasks_ids={tasks_ids} />
      </div>
    </>
  );
}
