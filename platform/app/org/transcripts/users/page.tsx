"use client";

import TopRowKpis from "@/components/insights/top-row";
import { UsersTable } from "@/components/transcripts/users/users-table";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { authFetcher } from "@/lib/fetcher";
import { navigationStateStore } from "@/store/store";
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

  // Fetch all users
  const { data: usersData } = useSWR(
    project_id ? [`/api/projects/${project_id}/users`, accessToken] : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "GET"),
    {
      keepPreviousData: true,
    },
  );
  const usersMetadata = usersData?.users;

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
            <div className="flex">
              <HeartHandshake className="mr-4 h-16 w-16 hover:text-green-500 transition-colors" />
              <div className="flex flex-grow justify-between items-center">
                <div>
                  <CardTitle className="flex flex-row text-2xl font-bold tracking-tight items-center">
                    Analyze user activity
                  </CardTitle>
                  <CardDescription>
                    Group your tasks by user by adding a <code>user_id</code> in
                    metadata when logging.
                  </CardDescription>
                </div>
                <Link
                  href="https://docs.phospho.ai/guides/sessions-and-users#users"
                  target="_blank"
                >
                  <Button variant="default">Set up user tracking</Button>
                </Link>
              </div>
            </div>
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
