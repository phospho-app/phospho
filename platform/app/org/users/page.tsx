"use client";

import TopRowKpis from "@/components/insights/top-row";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { UsersTable } from "@/components/users/users-table";
import { authFetcher } from "@/lib/fetcher";
import { UserMetadata } from "@/models/models";
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
  const project_id = navigationStateStore((state) => state.project_id);
  const setUniqueEventNamesInData = dataStateStore(
    (state) => state.setUniqueEventNamesInData,
  );

  // Fetch all users
  const { data: usersData } = useSWR(
    project_id ? [`/api/projects/${project_id}/users`, accessToken] : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "GET"),
    {
      keepPreviousData: true,
    },
  );
  const usersMetadata = usersData?.users;

  // Set the unique event names in the data (for the filter in the table)
  useEffect(() => {
    if (
      usersMetadata !== undefined &&
      usersMetadata !== null &&
      usersMetadata.length > 0
    ) {
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
        <Card className="bg-secondary">
          <CardHeader>
            <CardTitle className="flex flex-row text-2xl font-bold tracking-tight items-center">
              Breakdown tasks and sessions by user{" "}
              <HeartHandshake className="ml-2 h-6 w-6" />
            </CardTitle>
            <CardDescription className="flex justify-between">
              <div>
                Add a user_id in metadata when logging tasks to group them by
                user.
              </div>
              <Link
                href="https://docs.phospho.ai/guides/sessions-and-users#users"
                target="_blank"
              >
                <Button variant="default">Setup user tracking</Button>
              </Link>
            </CardDescription>
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
      <UsersTable usersMetadata={usersMetadata} />
    </>
  );
};

export default Users;
