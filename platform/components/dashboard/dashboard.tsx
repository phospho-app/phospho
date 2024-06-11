"use client";

import EventsLast7Days from "@/components/dashboard/events-last7days";
import EventsLast30m from "@/components/dashboard/events-last30m";
import OverviewLast7Days from "@/components/dashboard/overview-last7days";
import UsageLast30m from "@/components/dashboard/usage-last30m";
import { CenteredSpinner } from "@/components/small-spinner";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { authFetcher } from "@/lib/fetcher";
import { dataStateStore, navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import React from "react";
import useSWR from "swr";

const Dashboard: React.FC = () => {
  const project_id = navigationStateStore((state) => state.project_id);
  const { accessToken } = useUser();

  const { data: hasTasksData } = useSWR(
    project_id ? [`/api/explore/${project_id}/has-tasks`, accessToken] : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "POST"),
    { keepPreviousData: true },
  );
  const hasTasks: boolean = hasTasksData?.has_tasks ?? false;

  if (!project_id) {
    return <></>;
  }

  // The normal dashboard displays a session overview
  const normalDashboard = (
    <>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        <Card className="col-span-full lg:col-span-5">
          <CardHeader>
            <CardTitle>Number of Daily Tasks</CardTitle>
          </CardHeader>
          <CardContent className="pl-2 mx-2">
            <OverviewLast7Days project_id={project_id} />
          </CardContent>
        </Card>
        <Card className="col-span-full lg:col-span-2">
          <CardHeader>
            <CardTitle>Last 30 min</CardTitle>
          </CardHeader>
          <CardContent className="pl-2">
            <UsageLast30m project_id={project_id} />
          </CardContent>
        </Card>
      </div>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        <Card className="col-span-full lg:col-span-5">
          <CardHeader>
            <CardTitle>Number of Daily Events</CardTitle>
          </CardHeader>
          <CardContent className="pl-2 mx-2">
            <EventsLast7Days project_id={project_id} />
          </CardContent>
        </Card>

        <Card className="col-span-full lg:col-span-2">
          <CardHeader>
            <CardTitle>Last 30 min</CardTitle>
          </CardHeader>
          <CardContent className="pl-2">
            <EventsLast30m project_id={project_id} />
          </CardContent>
        </Card>
      </div>
    </>
  );

  // The no data dashboard displays a message to setup phospho in the app

  return (
    <>
      <div className="flex flex-1 flex-col space-y-4">
        {hasTasks === null && <CenteredSpinner />}
        {normalDashboard}
      </div>
    </>
  );
};

export default Dashboard;
