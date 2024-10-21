// This component displays a bar chart showing the number of events detected in each task with the version number
// Each event has 2 bars, one for each version
import { SendDataAlertDialog } from "@/components/callouts/import-data";
import { InteractiveDatetime } from "@/components/interactive-datetime";
import { AlertDialog } from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import { Calendar } from "@/components/ui/calendar";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuPortal,
  DropdownMenuSub,
  DropdownMenuSubContent,
  DropdownMenuSubTrigger,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { authFetcher } from "@/lib/fetcher";
import { ABTest, Project, ProjectDataFilters } from "@/models/models";
import { navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import {
  Check,
  ChevronDown,
  ChevronRight,
  EllipsisVertical,
} from "lucide-react";
import Link from "next/link";
import React, { useState } from "react";
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
  const [filtersA, setFiltersA] = useState<ProjectDataFilters>({
    created_at_start: undefined,
    created_at_end: undefined,
  });
  const [filtersB, setFiltersB] = useState<ProjectDataFilters>({
    created_at_start: undefined,
    created_at_end: undefined,
  });

  const [dateRangeA, setDateRangeA] = useState<string>("Select a date range");
  const [dateRangeB, setDateRangeB] = useState<string>("Select a date range");

  // Fetch ABTests
  const { data: abTests }: { data: ABTest[] | null | undefined } = useSWR(
    project_id ? [`/api/explore/${project_id}/ab-tests`, accessToken] : null,
    ([url, accessToken]) =>
      authFetcher(url, accessToken).then((res) => {
        if (res === undefined) return undefined;
        if (!res.abtests) return null;
        const abtests = res.abtests as ABTest[];
        return abtests;
      }),
    {
      keepPreviousData: true,
    },
  );

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

  const events = selectedProject?.settings?.events;

  const [selectedEventsIds, setSelectedEventsIds] = useState<string[] | null>(
    null,
  );

  // Used to mark the hint as "done" when the user has sent data
  const { data: hasTasksData } = useSWR(
    project_id ? [`/api/explore/${project_id}/has-tasks`, accessToken] : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "POST"),
    { keepPreviousData: true },
  );
  const hasTasks: boolean = hasTasksData?.has_tasks;

  const { data: graphData } = useSWR(
    project_id
      ? [
          `/api/explore/${encodeURI(project_id)}/ab-tests/compare-versions`,
          accessToken,
          versionIDA,
          versionIDB,
          JSON.stringify(selectedEventsIds),
          JSON.stringify(filtersA),
          JSON.stringify(filtersB),
        ]
      : null,
    ([url, accessToken]) =>
      authFetcher(url, accessToken, "POST", {
        versionA: versionIDA,
        versionB: versionIDB,
        selected_events_ids: selectedEventsIds,
        filtersA: filtersA,
        filtersB: filtersB,
      }),
    {
      keepPreviousData: true,
    },
  );

  const toggleEventSelection = (eventId: string) => {
    if (selectedEventsIds === null) {
      setSelectedEventsIds([eventId]);
    } else {
      setSelectedEventsIds(
        selectedEventsIds.includes(eventId)
          ? selectedEventsIds.filter((id) => id !== eventId)
          : [...selectedEventsIds, eventId],
      );
    }
  };

  const toggleAllEvents = (checked: boolean) => {
    if (checked && events) {
      const allEventIds = Object.values(events)
        .map((event) => event.id)
        .filter((id): id is string => id !== undefined);
      setSelectedEventsIds(allEventIds);
    } else {
      setSelectedEventsIds([]);
    }
  };

  const allEventsSelected =
    (selectedEventsIds !== null &&
      events &&
      Object.values(events).every(
        (event) => event.id && selectedEventsIds.includes(event.id),
      )) ||
    selectedEventsIds === null;

  const onClickFiltersA = (newDateRange: string) => {
    if (dateRangeA === newDateRange) {
      setDateRangeA("Select a date range");
      setVersionIDA(null);
      setFiltersA({
        created_at_start: undefined,
        created_at_end: undefined,
      });
    } else {
      setDateRangeA(newDateRange);
      if (newDateRange === "This week") {
        setFiltersA({
          created_at_start: Date.now() / 1000 - 7 * 24 * 60 * 60,
          created_at_end: undefined,
        });
        setVersionIDA("This week");
      }
      if (newDateRange === "Last week") {
        setFiltersA({
          created_at_start: Date.now() / 1000 - 14 * 24 * 60 * 60,
          created_at_end: Date.now() / 1000 - 7 * 24 * 60 * 60,
        });
        setVersionIDA("Last week");
      }
    }
  };

  const onClickFiltersB = (newDateRange: string) => {
    if (dateRangeB === newDateRange) {
      setDateRangeB("Select a date range");
      setVersionIDB(null);
      setFiltersB({
        created_at_start: undefined,
        created_at_end: undefined,
      });
    } else {
      setDateRangeB(newDateRange);
      if (newDateRange === "This week") {
        setFiltersB({
          created_at_start: Date.now() / 1000 - 7 * 24 * 60 * 60,
          created_at_end: undefined,
        });
        setVersionIDB("This week");
      }
      if (newDateRange === "Last week") {
        setFiltersB({
          created_at_start: Date.now() / 1000 - 14 * 24 * 60 * 60,
          created_at_end: Date.now() / 1000 - 7 * 24 * 60 * 60,
        });
        setVersionIDB("Last week");
      }
    }
  };

  const onClickVersionA = (version_id: string) => {
    setVersionIDA(version_id);
    setDateRangeA("Select a date range");
    setFiltersA({
      created_at_start: undefined,
      created_at_end: undefined,
    });
  };

  const onClickVersionB = (version_id: string) => {
    setVersionIDB(version_id);
    setDateRangeB("Select a date range");
    setFiltersB({
      created_at_start: undefined,
      created_at_end: undefined,
    });
  };

  return (
    <>
      <AlertDialog open={open}>
        <SendDataAlertDialog setOpen={setOpen} key="ab_testing" />
        <div className="flex flex-row items-center z-0 space-x-2">
          <div className="flex  space-x-2">
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" className="px-2">
                  <EllipsisVertical className="size-6" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent
                align="start"
                className="overflow-y-auto max-h-[40rem]"
              >
                <DropdownMenuLabel className="flex flex-row items-center ">
                  Displayed analytics
                </DropdownMenuLabel>
                {events && Object.keys(events).length > 0 ? (
                  <>
                    <Separator />
                    <DropdownMenuItem
                      className="flex items-center gap-x-2"
                      onClick={(e) => {
                        e.preventDefault();
                        toggleAllEvents(!allEventsSelected);
                      }}
                    >
                      <Checkbox id="select-all" checked={allEventsSelected} />
                      <span>Select All</span>
                    </DropdownMenuItem>
                    <Separator />
                    {Object.entries(events).map(([, event]) => {
                      if (!event.id) return null;
                      return (
                        <DropdownMenuItem
                          key={event.id}
                          className="flex items-center gap-x-2"
                          onClick={(e) => {
                            e.preventDefault();
                            if (event.id) {
                              toggleEventSelection(event.id);
                            }
                          }}
                        >
                          <Checkbox
                            id={event.id}
                            checked={
                              selectedEventsIds !== null
                                ? selectedEventsIds.includes(event.id)
                                : true
                            }
                          />
                          <span>{event.event_name}</span>
                        </DropdownMenuItem>
                      );
                    })}
                  </>
                ) : (
                  <DropdownMenuItem disabled>
                    <p>No analytics</p>
                  </DropdownMenuItem>
                )}
              </DropdownMenuContent>
            </DropdownMenu>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline">
                  <div className="flex flex-row items-center justify-between min-w-[10rem]">
                    <span className="font-semibold mr-1">Reference A: </span>
                    {versionIDA || "Select version"}{" "}
                    <ChevronDown className="size-4 ml-2" />
                  </div>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent className="overflow-y-auto max-h-[40rem] ">
                <DropdownMenuSub>
                  <DropdownMenuSubTrigger>{dateRangeA}</DropdownMenuSubTrigger>
                  <DropdownMenuPortal>
                    <DropdownMenuSubContent>
                      <DropdownMenuItem
                        onClick={() => onClickFiltersA("This week")}
                      >
                        {dateRangeA === "This week" && (
                          <Check className="h-4 w-4 mr-2 text-green-500" />
                        )}
                        This week
                      </DropdownMenuItem>
                      <DropdownMenuItem
                        onClick={() => onClickFiltersA("Last week")}
                      >
                        {dateRangeA === "Last week" && (
                          <Check className="h-4 w-4 mr-2 text-green-500" />
                        )}
                        Last week
                      </DropdownMenuItem>
                      <Separator />
                      <DropdownMenuSub>
                        <DropdownMenuSubTrigger>Custom</DropdownMenuSubTrigger>
                        <DropdownMenuSubContent>
                          <Calendar
                            initialFocus
                            mode="range"
                            onSelect={(selected) => {
                              if (selected !== undefined) {
                                // Set the time of the from date to 00:00:00
                                if (selected.from) {
                                  selected.from.setHours(0, 0, 0, 0);
                                  setFiltersA({
                                    created_at_start:
                                      selected.from.getTime() / 1000,
                                  });
                                }
                                // Set the time of the to date to 23:59:59
                                if (selected.to) {
                                  selected.to.setHours(23, 59, 59, 999);
                                  setFiltersA({
                                    created_at_end:
                                      selected.to.getTime() / 1000,
                                  });
                                }
                                setDateRangeA("Custom");
                                setVersionIDA("Custom");
                              }
                            }}
                            numberOfMonths={2}
                          />
                        </DropdownMenuSubContent>
                      </DropdownMenuSub>
                    </DropdownMenuSubContent>
                  </DropdownMenuPortal>
                </DropdownMenuSub>
                <Separator />
                {abTests?.map((abTest) => (
                  <DropdownMenuItem
                    key={`${abTest.version_id}_A`}
                    onClick={() => onClickVersionA(abTest.version_id)}
                    asChild
                  >
                    <div className="min-w-[10rem] flex flex-row justify-between gap-x-8">
                      <div className="flex flex-row gap-x-2 items-center">
                        {abTest.version_id === versionIDA && (
                          <Check className="size-4 mr-2 text-green-500" />
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
                    {versionIDB || "Select version"}{" "}
                    <ChevronDown className="size-4 ml-2" />
                  </div>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent
                className="w- 56 overflow-y-auto max-h-[40rem]"
                align="start"
              >
                <DropdownMenuSub>
                  <DropdownMenuSubTrigger>{dateRangeB}</DropdownMenuSubTrigger>
                  <DropdownMenuPortal>
                    <DropdownMenuSubContent>
                      <DropdownMenuItem
                        onClick={() => onClickFiltersB("This week")}
                      >
                        {dateRangeB === "This week" && (
                          <Check className="h-4 w-4 mr-2 text-green-500" />
                        )}
                        This week
                      </DropdownMenuItem>
                      <DropdownMenuItem
                        onClick={() => onClickFiltersB("Last week")}
                      >
                        {dateRangeB === "Last week" && (
                          <Check className="h-4 w-4 mr-2 text-green-500" />
                        )}
                        Last week
                      </DropdownMenuItem>
                      <Separator />
                      <DropdownMenuSub>
                        <DropdownMenuSubTrigger>Custom</DropdownMenuSubTrigger>
                        <DropdownMenuSubContent>
                          <Calendar
                            initialFocus
                            mode="range"
                            onSelect={(selected) => {
                              if (selected !== undefined) {
                                // Set the time of the from date to 00:00:00
                                if (selected.from) {
                                  selected.from.setHours(0, 0, 0, 0);
                                  setFiltersB({
                                    created_at_start:
                                      selected.from.getTime() / 1000,
                                  });
                                }
                                // Set the time of the to date to 23:59:59
                                if (selected.to) {
                                  selected.to.setHours(23, 59, 59, 999);
                                  setFiltersB({
                                    created_at_end:
                                      selected.to.getTime() / 1000,
                                  });
                                }
                                setDateRangeB("Custom");
                                setVersionIDB("Custom");
                              }
                            }}
                            numberOfMonths={2}
                          />
                        </DropdownMenuSubContent>
                      </DropdownMenuSub>
                    </DropdownMenuSubContent>
                  </DropdownMenuPortal>
                </DropdownMenuSub>
                <Separator />
                {abTests?.map((abTest) => (
                  <DropdownMenuItem
                    key={`${abTest.version_id}_B`}
                    onClick={() => onClickVersionB(abTest.version_id)}
                    asChild
                  >
                    <div className="min-w-[10rem] flex flex-row justify-between gap-x-8">
                      <div className="flex flex-row gap-x-2 items-center">
                        {abTest.version_id === versionIDB && (
                          <Check className="size-4 mr-2 text-green-500" />
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
