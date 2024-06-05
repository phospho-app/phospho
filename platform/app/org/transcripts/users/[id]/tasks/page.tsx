"use client";

import { TasksTable } from "@/components/transcripts/tasks/tasks-table";
import { authFetcher } from "@/lib/fetcher";
import { UserMetadata } from "@/models/models";
import { navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import useSWR from "swr";

const User = ({ params }: { params: { id: string } }) => {
  const user_id = decodeURIComponent(params.id);
  const project_id = navigationStateStore((state) => state.project_id);
  const { accessToken } = useUser();

  const {
    data: userMetadata,
  }: {
    data: UserMetadata | null | undefined;
  } = useSWR(
    [`/api/metadata/${project_id}/user/${user_id}`, accessToken],
    ([url, accessToken]) => authFetcher(url, accessToken, "GET"),
    {
      keepPreviousData: true,
    },
  );

  return (
    <>
      {userMetadata?.tasks_id && (
        <div className="hidden h-full flex-1 flex-col space-y-2 md:flex relative">
          <TasksTable tasks_ids={userMetadata.tasks_id} />
        </div>
      )}
    </>
  );
};

export default User;
