"use client";

import TopRowKpis from "@/components/insights/top-row";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { UsersTable } from "@/components/users/users-table";
import { authFetcher } from "@/lib/fetcher";
import { UserMetadata } from "@/models/metadata";
import { dataStateStore, navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import { HeartHandshake } from "lucide-react";
import Link from "next/link";
import React, { useEffect } from "react";
import useSWR from "swr";

// const Handshake = ({ ...props }) => (
//   <svg
//     xmlns="http://www.w3.org/2000/svg"
//     width="24"
//     height="24"
//     viewBox="0 0 24 24"
//     fill="none"
//     stroke="currentColor"
//     stroke-width="2"
//     stroke-linecap="round"
//     stroke-linejoin="round"
//     // class="lucide lucide-handshake"
//     {...props}
//   >
//     <path d="m11 17 2 2a1 1 0 1 0 3-3" />
//     <path d="m14 14 2.5 2.5a1 1 0 1 0 3-3l-3.88-3.88a3 3 0 0 0-4.24 0l-.88.88a1 1 0 1 1-3-3l2.81-2.81a5.79 5.79 0 0 1 7.06-.87l.47.28a2 2 0 0 0 1.42.25L21 4" />
//     <path d="m21 3 1 11h-2" />
//     <path d="M3 3 2 14l6.5 6.5a1 1 0 1 0 3-3" />
//     <path d="M3 4h8" />
//   </svg>
// );

const Users = () => {
  const { accessToken } = useUser();
  const selectedProject = navigationStateStore(
    (state) => state.selectedProject,
  );
  const project_id = selectedProject?.id;
  const usersMetadata = dataStateStore((state) => state.usersMetadata);
  const setUniqueEventNamesInData = dataStateStore(
    (state) => state.setUniqueEventNamesInData,
  );

  // Set the unique event names in the data (for the filter in the table)
  useEffect(() => {
    if (usersMetadata !== null && usersMetadata.length > 0) {
      const uniqueEventNames: string[] = Array.from(
        new Set(
          usersMetadata
            .map((task: UserMetadata) => task.events)
            .flat()
            .map((event: any) => event.event_name as string),
        ),
      );
      setUniqueEventNamesInData(uniqueEventNames);
    }
  }, [project_id, usersMetadata?.length]);

  // Fetch graph data

  const { data: userCountData, error: fetchUserCountError } = useSWR(
    [`/api/metadata/${project_id}/count/tasks/user_id`, accessToken],
    ([url, accessToken]) => authFetcher(url, accessToken, "GET"),
    {
      keepPreviousData: true,
    },
  );
  const userCount = userCountData?.value;

  const { data: userAverageData, error: fetchUserAverageError } = useSWR(
    [`/api/metadata/${project_id}/average/tasks/user_id`, accessToken],
    ([url, accessToken]) => authFetcher(url, accessToken, "GET"),
    {
      keepPreviousData: true,
    },
  );
  const userAverage = Math.round(userAverageData?.value * 100) / 100;

  const { data: userTop10Data, error: fetchUserTop10Error } = useSWR(
    [`/api/metadata/${project_id}/top10/tasks/user_id`, accessToken],
    ([url, accessToken]) => authFetcher(url, accessToken, "GET"),
    {
      keepPreviousData: true,
    },
  );
  const userTop10 = userTop10Data?.value;

  const { data: userBottom10Data, error: fetchUserBottom10Error } = useSWR(
    [`/api/metadata/${project_id}/bottom10/tasks/user_id`, accessToken],
    ([url, accessToken]) => authFetcher(url, accessToken, "GET"),
    {
      keepPreviousData: true,
    },
  );
  const userBottom10 = userBottom10Data?.value;

  if (!project_id) {
    return <p>No project selected</p>;
  }

  return (
    <>
      {userCount === 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex flex-row text-2xl font-bold tracking-tight items-center">
              Get to meet your users <HeartHandshake className="ml-2 h-6 w-6" />
            </CardTitle>
            <CardContent>
              <p className="text-gray-500">
                Discover who your users are and what they do in your app. Pass a
                user_id when logging metadata to get started.
              </p>
              <div className="flex flex-col justify-center items-center m-2">
                <Link
                  href="https://docs.phospho.ai/guides/sessions-and-users#users"
                  target="_blank"
                >
                  <Button variant="default">Read the guide</Button>
                </Link>
              </div>
            </CardContent>
          </CardHeader>
        </Card>
      )}
      <TopRowKpis
        name="Users"
        count={userCount}
        bottom10={userBottom10}
        average={userAverage}
        top10={userTop10}
      />
      <UsersTable project_id={project_id} />
    </>
  );
};

export default Users;
