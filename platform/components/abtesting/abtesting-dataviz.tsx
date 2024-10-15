// This component displays a bar chart showing the number of events detected in each task with the version number
// Each event has 2 bars, one for each version
import { SendDataAlertDialog } from "@/components/callouts/import-data";
import { InteractiveDatetime } from "@/components/interactive-datetime";
import { AlertDialog } from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Skeleton } from "@/components/ui/skeleton";
import { authFetcher } from "@/lib/fetcher";
import { ABTest, Project } from "@/models/models";
import { navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import { Check, ChevronDown, ChevronRight } from "lucide-react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useCallback } from "react";
import React, { useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  Legend,
  ResponsiveContainer,
  Tooltip,
  TooltipProps,
  XAxis,
} from "recharts";
import {
  NameType,
  ValueType,
} from "recharts/types/component/DefaultTooltipContent";
import useSWR from "swr";

import CreateNewABTestButton from "./create-new-ab-test-button";

export const ABTestingDataviz = () => {
  /**
   *  In the URL, use the search params ?a=version_id&b=version_id to set the default versions in the dropdown
   */

  const { accessToken } = useUser();
  const project_id = navigationStateStore((state) => state.project_id);

  // Fetch ABTests
  const { data: abTests }: { data: ABTest[] | null | undefined } = useSWR(
    project_id ? [`/api/explore/${project_id}/ab-tests`, accessToken] : null,
    ([url, accessToken]) =>
      authFetcher(url, accessToken).then((res) => {
        if (res === undefined) return undefined;
        if (!res.abtests) return null;
        const abtests = res.abtests as ABTest[];
        // Round the score and score_std to 2 decimal places
        abtests.forEach((abtest) => {
          abtest.score = Math.round(abtest.score * 10000) / 100;
          if (abtest.score_std) {
            abtest.score_std = Math.round(abtest?.score_std * 10000) / 100;
          }
        });
        return abtests;
      }),
    {
      keepPreviousData: true,
    },
  );

  // Get the version IDs from the URL. If not present, use the first two version IDs
  const searchParams = useSearchParams();

  const abTestJSON = JSON.stringify(abTests);

  const computeVersionsIds = useCallback(() => {
    let currVersionA = null;
    let currVersionB = null;

    if (!abTests) return { currVersionA, currVersionB };
    if (!abTestJSON) return { currVersionA, currVersionB };

    if (abTests.length === 1) {
      currVersionA = abTests[0].version_id;
      currVersionB = abTests[0].version_id;
    } else if (abTests.length >= 2) {
      currVersionA = abTests[1].version_id;
      currVersionB = abTests[0].version_id;
    }

    // Override the default versions if the URL has the search params
    if (searchParams.get("a")) {
      currVersionA = searchParams.get("a");
    }
    if (searchParams.get("b")) {
      currVersionB = searchParams.get("b");
    }

    return { currVersionA, currVersionB };
  }, [abTests, abTestJSON, searchParams]);

  const [versionIDA, setVersionIDA] = useState<string | null>(null);
  const [versionIDB, setVersionIDB] = useState<string | null>(null);
  const [open, setOpen] = useState(false);

  // Used to mark the hint as "done" when the user has set up analytics
  const { data: selectedProject }: { data: Project } = useSWR(
    project_id ? [`/api/projects/${project_id}`, accessToken] : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "GET"),
    {
      keepPreviousData: true,
    },
  );
  const noEventDefinitions =
    selectedProject?.settings?.events === undefined ||
    Object.keys(selectedProject?.settings?.events).length === 0;

  // Used to mark the hint as "done" when the user has sent data
  const { data: hasTasksData } = useSWR(
    project_id ? [`/api/explore/${project_id}/has-tasks`, accessToken] : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "POST"),
    { keepPreviousData: true },
  );
  const hasTasks: boolean = hasTasksData?.has_tasks;

  useEffect(() => {
    const { currVersionA, currVersionB } = computeVersionsIds();
    setVersionIDA(currVersionA);
    setVersionIDB(currVersionB);
  }, [computeVersionsIds]);

  const { data: graphData } = useSWR(
    project_id
      ? [
          `/api/explore/${encodeURI(project_id)}/ab-tests/compare-versions`,
          accessToken,
          versionIDA,
          versionIDB,
        ]
      : null,
    ([url, accessToken]) =>
      authFetcher(url, accessToken, "POST", {
        versionA: versionIDA,
        versionB: versionIDB,
      }),
    {
      keepPreviousData: true,
    },
  );

  return (
    <>
      <AlertDialog open={open}>
        <SendDataAlertDialog setOpen={setOpen} key="ab_testing" />
        <div className="flex z-0 space-x-2">
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline">
                <div className="flex flex-row items-center justify-between min-w-[10rem]">
                  <span className="font-semibold mr-1">Reference A: </span>
                  {versionIDA} <ChevronDown className="h-4 w-4 ml-2" />
                </div>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent
              align="end"
              className="overflow-y-auto max-h-[40rem] "
            >
              {abTests?.map((abTest) => (
                <DropdownMenuItem
                  key={`${abTest.version_id}_A`}
                  onClick={() => setVersionIDA(abTest.version_id)}
                  asChild
                >
                  <div className="min-w-[10rem] flex flex-row justify-between gap-x-8">
                    <div className="flex flex-row gap-x-2 items-center">
                      {abTest.version_id === versionIDA && (
                        <Check className="h-4 w-4 mr-2 text-green-500" />
                      )}
                      {abTest.version_id}
                    </div>
                    <InteractiveDatetime timestamp={abTest.first_task_ts} />
                  </div>
                </DropdownMenuItem>
              ))}
              {abTests?.length === 0 && (
                <DropdownMenuItem disabled className="min-w-[10rem]">
                  <p>
                    No <code>version_id</code> found
                  </p>
                </DropdownMenuItem>
              )}
            </DropdownMenuContent>
          </DropdownMenu>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline">
                <div className="flex flex-row items-center justify-between min-w-[10rem]">
                  <span className="font-semibold mr-1">Candidate B:</span>
                  {versionIDB} <ChevronDown className="h-4 w-4 ml-2" />
                </div>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent
              align="end"
              className="overflow-y-auto max-h-[40rem]"
            >
              {abTests?.map((abTest) => (
                <DropdownMenuItem
                  key={`${abTest.version_id}_B`}
                  onClick={() => setVersionIDB(abTest.version_id)}
                  asChild
                >
                  <div className="min-w-[10rem] flex flex-row justify-between gap-x-8">
                    <div className="flex flex-row gap-x-2 items-center">
                      {abTest.version_id === versionIDB && (
                        <Check className="h-4 w-4 mr-2 text-green-500" />
                      )}
                      {abTest.version_id}
                    </div>
                    <InteractiveDatetime timestamp={abTest.first_task_ts} />
                  </div>
                </DropdownMenuItem>
              ))}
              {abTests?.length === 0 && (
                <DropdownMenuItem disabled>
                  <p>
                    No <code>version_id</code> found
                  </p>
                </DropdownMenuItem>
              )}
            </DropdownMenuContent>
          </DropdownMenu>
          <CreateNewABTestButton />
        </div>
        <div className="flex flex-col items-center my-2">
          {graphData === undefined && (
            <Skeleton className="w-[100%] h-[400px]" />
          )}
          {graphData && (!versionIDA || !abTests || graphData.length == 0) && (
            <div className="h-[400px] w-[100%] flex items-center justify-center">
              <div className="flex space-x-40 text-center items-center">
                <div className="mb-20">
                  <p className="text-muted-foreground mb-2 text-sm pt-6">
                    1 - Start sending data
                  </p>
                  {!hasTasks && (
                    <Button variant="outline" onClick={() => setOpen(true)}>
                      Import data
                      <ChevronRight className="ml-2" />
                    </Button>
                  )}
                  {hasTasks && (
                    <Button variant="outline" disabled>
                      <Check className="mr-1" />
                      Done
                    </Button>
                  )}
                </div>
                <div className="mb-20">
                  <p className="text-muted-foreground mb-2 text-sm pt-6">
                    2 - Setup analytics
                  </p>
                  {noEventDefinitions && (
                    <Link href="/org/insights/events">
                      <Button variant="outline">
                        Setup analytics
                        <ChevronRight className="ml-2" />
                      </Button>
                    </Link>
                  )}
                  {!noEventDefinitions && (
                    <Button variant="outline" disabled>
                      <Check className="mr-1" />
                      Done
                    </Button>
                  )}
                </div>
              </div>
            </div>
          )}
          {graphData && versionIDA && versionIDB && graphData.length > 0 && (
            <ResponsiveContainer width={"100%"} height={400}>
              <BarChart data={graphData}>
                <XAxis dataKey="event_name" />
                <Tooltip content={<CustomTooltip />} />
                <Legend />
                <Bar dataKey={versionIDA} fill="#28BB62" />
                <Bar dataKey={versionIDB} fill="#82ca9d" />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </AlertDialog>
    </>
  );
};

interface CustomPayloadItem {
  dataKey: string;
  name: string;
  value: ValueType;
  payload: {
    [key: string]: number;
  };
  color?: string;
}

export const CustomTooltip: React.FC<TooltipProps<ValueType, NameType>> = ({
  active,
  payload,
  label,
}) => {
  if (active && payload && payload.length) {
    return (
      <div className="custom-tooltip">
        <Card>
          <CardHeader className="label">
            <CardTitle>{label}</CardTitle>
            <CardDescription>
              Number of detections, adjusted per number of user messages
            </CardDescription>
          </CardHeader>
          <CardContent>
            {payload.map((pld, index) => {
              const typedPld = pld as unknown as CustomPayloadItem;
              return (
                <div
                  key={typedPld.dataKey || index}
                  style={{ display: "inline-block", padding: 10 }}
                >
                  <div>
                    {typedPld.payload[`${typedPld.dataKey}_tooltip`]?.toFixed(
                      2,
                    )}
                  </div>
                  <div>{typedPld.dataKey}</div>
                </div>
              );
            })}
          </CardContent>
        </Card>
      </div>
    );
  }

  return null;
};
