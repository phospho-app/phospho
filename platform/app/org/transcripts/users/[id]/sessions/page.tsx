"use client";

import { SessionsTable } from "@/components/sessions/sessions-table";
import { CenteredSpinner } from "@/components/small-spinner";
import { authFetcher } from "@/lib/fetcher";
import { navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import useSWR from "swr";

const User = ({ params }: { params: { id: string } }) => {
  const user_id = decodeURIComponent(params.id);
  const project_id = navigationStateStore((state) => state.project_id);
  const { accessToken } = useUser();

  const { data } = useSWR(
    [`/api/metadata/${project_id}/user/${user_id}`, accessToken],
    ([url, accessToken]) => authFetcher(url, accessToken, "GET"),
    {
      keepPreviousData: true,
    },
  );
  const userMetadata = data;

  if (!project_id) {
    return <div>No project selected</div>;
  }

  return (
    <>
      {(userMetadata === null && <CenteredSpinner />) || (
        <div>
          <SessionsTable userFilter={user_id} />
        </div>
      )}
    </>
  );
};

export default User;
