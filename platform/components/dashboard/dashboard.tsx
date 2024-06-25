"use client";

import EventsLast7Days from "@/components/dashboard/events-last7days";
import EventsLast30m from "@/components/dashboard/events-last30m";
import OverviewLast7Days from "@/components/dashboard/overview-last7days";
import UsageLast30m from "@/components/dashboard/usage-last30m";
import DatavizGraph from "@/components/dataviz";
import { CenteredSpinner } from "@/components/small-spinner";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { authFetcher } from "@/lib/fetcher";
import { navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import { GridStack } from "gridstack";
import "gridstack/dist/gridstack-extra.min.css";
import "gridstack/dist/gridstack.min.css";
import { EllipsisVertical, Pencil, Trash, X } from "lucide-react";
import React, { useEffect } from "react";
import useSWR from "swr";

interface DashboardCardProps {
  children: React.ReactNode;
  cardTitle: string;
  className?: string;
  grid: GridStack | null;
  id: number;
}

const DashboardCard: React.FC<DashboardCardProps> = ({
  children,
  cardTitle,
  grid,
  id,
}) => {
  return (
    <Card
      className="grid-stack-item"
      gs-w={"4"}
      gs-h={"2"}
      id={`gridstackitem-${id}`} // this id is used to remove the card from the grid
    >
      <div className="grid-stack-item-content">
        <CardHeader className="flex flex-row justify-between items-center py-1">
          <CardTitle>{cardTitle}</CardTitle>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon">
                <EllipsisVertical />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem className="flex flex-row space-x-2 items-center">
                <Pencil className="w-4 h-4" /> <span>Edit</span>
              </DropdownMenuItem>
              <DropdownMenuItem
                className="text-red-500 flex flex-row items-center space-x-2"
                onClick={(event) => {
                  // Remove the card from the grid
                  // Get this card's parent gridstack item using the id
                  const closestParentGridStackItem = document.getElementById(
                    `gridstackitem-${id}`,
                  );
                  console.log(
                    "closestParentGridStackItem",
                    closestParentGridStackItem,
                  );
                  if (grid && closestParentGridStackItem) {
                    grid.removeWidget(
                      closestParentGridStackItem as HTMLElement,
                      true,
                    );
                    // TODO : remove it from the data to be rendered (global state)
                  }
                }}
              >
                <Trash className="w-4 h-4" /> <span>Remove</span>
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
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

  const [grid, setGrid] = React.useState<GridStack | null>(null);

  useEffect(() => {
    const initializedGrid = GridStack.init({
      column: 8,
      minRow: 1,
      margin: 12,
      // removable: true,
    });
    setGrid(initializedGrid);
  }, []);

  if (!project_id) {
    return <></>;
  }

  // TODO : turn this into a global state
  const customDashboardTiles = [
    {
      cardTitle: "Success rate per task position",
      metric: "Avg Success rate",
      breakdown_by: "task_position",
    },
    {
      cardTitle: "Average success rate per event name",
      metric: "Avg Success rate",
      breakdown_by: "event_name",
    },
    {
      cardTitle: "Average sentiment score per task position",
      metric: "Avg",
      selectedMetricMetadata: "sentiment_score",
      breakdown_by: "task_position",
    },
    {
      cardTitle: "Success rate per language",
      metric: "Avg Success rate",
      breakdown_by: "language",
    },
  ];

  // The normal dashboard displays a session overview
  const normalDashboard = (
    <>
      <div className="grid-stack">
        {customDashboardTiles.map((tile, index) => (
          <DashboardCard
            key={index}
            cardTitle={tile.cardTitle}
            grid={grid}
            id={index}
          >
            <DatavizGraph
              metric={tile.metric}
              selectedMetricMetadata={tile.selectedMetricMetadata}
              breakdown_by={tile.breakdown_by}
            />
          </DashboardCard>
        ))}
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
