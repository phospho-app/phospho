"use client";

import SmallSpinner from "@/components/small-spinner";
import TaskOverview from "@/components/transcripts/tasks/task";
import { authFetcher } from "@/lib/fetcher";
import { UserMetadata } from "@/models/metadata";
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
      {(userMetadata === null && <SmallSpinner />) || (
        <div>
          {userMetadata?.tasks_id.map((task_id) => {
            return <TaskOverview task_id={task_id} />;
          })}
        </div>
      )}
    </>
  );
};

export default User;
