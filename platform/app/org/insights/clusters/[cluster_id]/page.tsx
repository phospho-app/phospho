"use client";

import ComingSoonAlert from "@/components/coming-soon";
import { SessionsTable } from "@/components/sessions/sessions-table";
import { TasksTable } from "@/components/tasks/tasks-table";
import { Button } from "@/components/ui/button";
import { authFetcher } from "@/lib/fetcher";
import { Cluster } from "@/models/models";
import { navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import { ChevronLeft } from "lucide-react";
import { useRouter } from "next/navigation";
import useSWR from "swr";

export default function Page({ params }: { params: { cluster_id: string } }) {
  const router = useRouter();
  const { accessToken } = useUser();
  const project_id = navigationStateStore((state) => state.project_id);
  const cluster_id = decodeURIComponent(params.cluster_id);

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
            <div className="text-2xl font-bold tracking-tight mr-8">
              Cluster &apos;{cluster.name}&apos;
            </div>
          )}
          {cluster?.description && (
            <div className="text-muted-foreground">{cluster.description}</div>
          )}
        </div>
        {Array.isArray(tasks_ids) && tasks_ids.length > 0 && (
          <div className="hidden h-full flex-1 flex-col space-y-2 md:flex relative">
            <TasksTable forcedDataFilters={{ clusters_ids: [cluster_id] }} />
          </div>
        )}
        {Array.isArray(sessions_ids) && sessions_ids.length > 0 && (
          <div className="hidden h-full flex-1 flex-col space-y-2 md:flex relative">
            <SessionsTable forcedDataFilters={{ clusters_ids: [cluster_id] }} />
          </div>
        )}
        {/* TODO: User scope is not supported yet */}
        {cluster?.scope === "users" && <ComingSoonAlert />}
        <div className="h-10"></div>
      </div>
    </>
  );
}
