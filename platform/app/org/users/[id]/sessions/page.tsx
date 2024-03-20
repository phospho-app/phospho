"use client";

import SmallSpinner from "@/components/small-spinner";
import { SessionsTable } from "@/components/transcripts/sessions/sessions-table";
import { authFetcher } from "@/lib/fetcher";
import { dataStateStore, navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import useSWR from "swr";

const User = ({ params }: { params: { id: string } }) => {
  const user_id = decodeURIComponent(params.id);
  const project_id = navigationStateStore((state) => state.project_id);
  const { accessToken } = useUser();
  const setSessionsWithEvents = dataStateStore(
    (state) => state.setSessionsWithEvents,
  );

  const { data } = useSWR(
    [`/api/metadata/${project_id}/user/${user_id}`, accessToken],
    ([url, accessToken]) => authFetcher(url, accessToken, "GET"),
    {
      keepPreviousData: true,
    },
  );
  const userMetadata = data;
  if (data?.sessions) {
    setSessionsWithEvents(data.sessions);
  }

  if (!project_id) {
    return <div>No project selected</div>;
  }

  return (
    <>
      {(userMetadata === null && <SmallSpinner />) || (
        <div>
          <SessionsTable />
        </div>
      )}
    </>
  );
};

export default User;
