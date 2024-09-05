"use client";

import { SessionsTable } from "@/components/transcripts/sessions/sessions-table";
import { TasksTable } from "@/components/transcripts/tasks/tasks-table";
import { Button } from "@/components/ui/button";
import { authFetcher } from "@/lib/fetcher";
import { Cluster } from "@/models/models";
import { navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import { ChevronLeft } from "lucide-react";
import { useRouter } from "next/navigation";
import useSWR from "swr";

export default function Page({ params }: { params: { id: string } }) {
  const router = useRouter();
  const { accessToken } = useUser();
  const project_id = navigationStateStore((state) => state.project_id);
  const cluster_id = decodeURIComponent(params.id);

  // todo: fetch from server
  const { data: cluster }: { data: Cluster | undefined | null } = useSWR(
    project_id
      ? [`/api/explore/${project_id}/clusters/${cluster_id}`, accessToken]
      : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "POST"),
    { keepPreviousData: true },
  );
  const tasks_ids = cluster?.tasks_ids;
  const sessions_ids = cluster?.sessions_ids;

  return (
    <>
      <Button onClick={() => router.back()}>
        <ChevronLeft className="w-4 h-4 mr-1" /> Back
      </Button>
      <div>
        <div className="pb-4">
          {cluster?.name && (
            <div className="text-3xl font-bold tracking-tight mr-8">
              Cluster '{cluster.name}'
            </div>
          )}
          {cluster?.description && (
            <div className="text-muted-foreground">{cluster.description}</div>
          )}
        </div>
        {Array.isArray(tasks_ids) && tasks_ids.length > 0 && (
          <div className="hidden h-full flex-1 flex-col space-y-2 md:flex relative">
            <TasksTable tasks_ids={tasks_ids} />
          </div>
        )}
        {Array.isArray(sessions_ids) && sessions_ids.length > 0 && (
          <div className="hidden h-full flex-1 flex-col space-y-2 md:flex relative">
            <SessionsTable sessions_ids={sessions_ids} />
          </div>
        )}
        <div className="h-10"></div>
      </div>
    </>
  );
}
