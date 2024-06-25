"use client";

import EventsLast7Days from "@/components/dashboard/events-last7days";
import EventsLast30m from "@/components/dashboard/events-last30m";
import OverviewLast7Days from "@/components/dashboard/overview-last7days";
import UsageLast30m from "@/components/dashboard/usage-last30m";
import DatavizGraph from "@/components/dataviz";
import { CenteredSpinner } from "@/components/small-spinner";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { authFetcher } from "@/lib/fetcher";
import { navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import { GridStack } from "gridstack";
import "gridstack/dist/gridstack-extra.min.css";
import "gridstack/dist/gridstack.min.css";
import React, { useEffect } from "react";
import useSWR from "swr";

interface DashboardCardProps {
  children: React.ReactNode;
  cardTitle: string;
  className?: string;
}

const DashboardCard: React.FC<DashboardCardProps> = ({
  children,
  cardTitle,
  className,
}) => {
  return (
    <Card className="grid-stack-item" gs-w={"4"} gs-h={"2"}>
      <div className="grid-stack-item-content">
        <CardHeader>
          <CardTitle>{cardTitle}</CardTitle>
        </CardHeader>
        <CardContent className="h-4/5">{children}</CardContent>
      </div>
    </Card>
  );
};

const Dashboard: React.FC = () => {
  const project_id = navigationStateStore((state) => state.project_id);
  const { accessToken } = useUser();

  const { data: hasTasksData } = useSWR(
    project_id ? [`/api/explore/${project_id}/has-tasks`, accessToken] : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "POST"),
    { keepPreviousData: true },
  );
  const hasTasks: boolean = hasTasksData?.has_tasks ?? false;

  useEffect(() => {
    var grid = GridStack.init({
      column: 8,
      minRow: 1,
      margin: 12,
      removable: true,
    });
  });

  if (!project_id) {
    return <></>;
  }

  // The normal dashboard displays a session overview
  const normalDashboard = (
    <>
      <div className="grid-stack">
        <DashboardCard cardTitle="Average sentiment score per task position">
          <DatavizGraph
            metric="Avg"
            selectedMetricMetadata="sentiment_score"
            breakdown_by="task_position"
          />
        </DashboardCard>
        <DashboardCard cardTitle="Average success rate per event name">
          <DatavizGraph
            metric="Avg Success rate"
            breakdown_by="event_name"
            selectedMetricMetadata=""
          />
        </DashboardCard>
        <DashboardCard cardTitle="Success rate per language">
          <DatavizGraph metric="Avg Success rate" breakdown_by="language" />
        </DashboardCard>
        <DashboardCard cardTitle="Success rate per task position">
          <DatavizGraph
            metric="Avg Success rate"
            breakdown_by="task_position"
            selectedMetricMetadata=""
          />
        </DashboardCard>
      </div>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-6">
        <Card className="col-span-full lg:col-span-4">
          <CardHeader>
            <CardTitle>Number of Daily Tasks</CardTitle>
          </CardHeader>
          <CardContent>
            <OverviewLast7Days />
          </CardContent>
        </Card>
        <Card className="col-span-full lg:col-span-2">
          <CardHeader>
            <CardTitle>Last 30 min</CardTitle>
          </CardHeader>
          <CardContent>
            <UsageLast30m />
          </CardContent>
        </Card>
      </div>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-6">
        <Card className="col-span-full lg:col-span-4">
          <CardHeader>
            <CardTitle>Number of Daily Events</CardTitle>
          </CardHeader>
          <CardContent>
            <EventsLast7Days />
          </CardContent>
        </Card>

        <Card className="col-span-full lg:col-span-2">
          <CardHeader>
            <CardTitle>Last 30 min</CardTitle>
          </CardHeader>
          <CardContent>
            <EventsLast30m />
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
