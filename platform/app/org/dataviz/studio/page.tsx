"use client";

import { DatavizCallout } from "@/components/callouts/import-data";
import DatavizGraph from "@/components/dataviz";
import { DatePickerWithRange } from "@/components/date-range";
import FilterComponent from "@/components/filters";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuPortal,
  DropdownMenuSub,
  DropdownMenuSubContent,
  DropdownMenuSubTrigger,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  HoverCard,
  HoverCardContent,
  HoverCardTrigger,
} from "@/components/ui/hover-card";
import { useToast } from "@/components/ui/use-toast";
import { authFetcher } from "@/lib/fetcher";
import { DashboardTile, Project } from "@/models/models";
import { EventDefinition, ScoreRangeType } from "@/models/models";
import { navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import {
  ArrowDown,
  ArrowUp,
  BarChart,
  ChevronDown,
  Code,
  Flag,
  LayoutDashboard,
  List,
  MessagesSquare,
  Plus,
  TextSearch,
  Timer,
  Users,
} from "lucide-react";
import { useRouter } from "next/navigation";
import React, { useState } from "react";
import useSWR, { mutate } from "swr";

const MetadataForm: React.FC = () => {
  // create a page with 2 dropdowns :
  // 1. Metric: count of tasks, avg_session_length, sum of a metadata field,
  // 2. Groupby field : None ; metadataField (user_id, version_id, etc. ) ; event_name ; flag

  // The data is fetched and then displayed as a bar chart or a table

  const { accessToken } = useUser();
  const { toast } = useToast();
  const router = useRouter();

  const project_id = navigationStateStore((state) => state.project_id);

  const selectedMetric = navigationStateStore((state) => state.selectedMetric);
  const metadata_metric = navigationStateStore(
    (state) => state.metadata_metric,
  );
  const breakdown_by = navigationStateStore((state) => state.selectedGroupBy);
  const setSelectedMetric = navigationStateStore(
    (state) => state.setSelectedMetric,
  );
  const setmetadata_metric = navigationStateStore(
    (state) => state.setmetadata_metric,
  );
  const setSelectedGroupBy = navigationStateStore(
    (state) => state.setSelectedGroupBy,
  );
  const selectedScorerId = navigationStateStore(
    (state) => state.selectedScorerId,
  );
  const setSelectedScorerId = navigationStateStore(
    (state) => state.setSelectedScorerId,
  );
  const datavizSorting = navigationStateStore((state) => state.datavizSorting);
  const setDatavizSorting = navigationStateStore(
    (state) => state.setDatavizSorting,
  );

  const dataFilters = navigationStateStore((state) => state.dataFilters);

  const [selectedScorerName, setselectedScorerName] = useState<
    string | undefined
  >(undefined);

  const { data: selectedProject }: { data: Project } = useSWR(
    project_id ? [`/api/projects/${project_id}`, accessToken] : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "GET"),
    {
      keepPreviousData: true,
    },
  );

  const rangeEvents: EventDefinition[] = Object.values(
    selectedProject?.settings?.events ?? {},
  ).filter(
    (event): event is EventDefinition =>
      event.score_range_settings?.score_type === ScoreRangeType.range,
  );

  // Fetch metadata unique metadata fields from the API
  const { data } = useSWR(
    [`/api/metadata/${project_id}/fields`, accessToken],
    ([url, accessToken]) => authFetcher(url, accessToken, "POST"),
    {
      keepPreviousData: true,
    },
  );
  const numberMetadataFields: string[] | undefined = data?.number;
  const categoryMetadataFields: string[] | undefined = data?.string;

  return (
    <>
      <div className="flex flex-col gap-y-2">
        <DatavizCallout />
        <div className="flex flex-row justify-between">
          <div className="flex flex-row space-x-2 items-center">
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline">
                  Metric: {selectedMetric} {metadata_metric ?? ""}{" "}
                  {selectedMetric === "avg_scorer_value" && selectedScorerName
                    ? `(${selectedScorerName})`
                    : ""}{" "}
                  <ChevronDown className="size-4 ml-2" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem
                  onClick={() => {
                    setSelectedMetric("nb_messages");
                    setmetadata_metric(null);
                  }}
                >
                  <MessagesSquare className="size-4 mr-2" />
                  Nb user messages
                </DropdownMenuItem>
                <DropdownMenuItem
                  onClick={() => {
                    setSelectedMetric("nb_sessions");
                    setmetadata_metric(null);
                  }}
                >
                  <List className="size-4 mr-2" />
                  Nb sessions
                </DropdownMenuItem>
                <DropdownMenuItem
                  onClick={() => {
                    setSelectedMetric("count_unique");
                    setmetadata_metric("user_id");
                  }}
                >
                  <Users className="size-4 mr-2" />
                  Nb users
                </DropdownMenuItem>
                <DropdownMenuItem
                  onClick={() => {
                    setSelectedMetric("tags_count");
                    setmetadata_metric(null);
                  }}
                >
                  <TextSearch className="size-4 mr-2" />
                  Nb tags
                </DropdownMenuItem>
                <DropdownMenuItem
                  onClick={() => {
                    setSelectedMetric("tags_distribution");
                    setmetadata_metric(null);
                  }}
                >
                  <TextSearch className="size-4 mr-2" />
                  Tags distribution
                </DropdownMenuItem>
                <DropdownMenuSub>
                  <DropdownMenuSubTrigger>
                    <TextSearch className="size-4 mr-2" />
                    Avg Scorer value
                  </DropdownMenuSubTrigger>
                  <DropdownMenuSubContent>
                    {rangeEvents.map((event) => (
                      <DropdownMenuItem
                        key={event.event_name}
                        onClick={() => {
                          setselectedScorerName(event.event_name);
                          setSelectedScorerId(event.id ?? null);
                          setSelectedMetric("avg_scorer_value");
                          setmetadata_metric(null);
                        }}
                      >
                        {event.event_name}
                      </DropdownMenuItem>
                    ))}
                  </DropdownMenuSubContent>
                </DropdownMenuSub>
                <DropdownMenuItem
                  onClick={() => {
                    setSelectedMetric("avg_success_rate");
                    setmetadata_metric(null);
                  }}
                >
                  <Flag className="size-4 mr-2" />
                  Avg Success rate
                </DropdownMenuItem>
                <DropdownMenuItem
                  onClick={() => {
                    setSelectedMetric("avg_session_length");
                    setmetadata_metric(null);
                  }}
                >
                  <List className="size-4 mr-2" />
                  Avg Session length
                </DropdownMenuItem>
                <DropdownMenuSub>
                  <DropdownMenuSubTrigger>
                    <Code className="size-4 mr-2" />
                    Nb unique metadata
                  </DropdownMenuSubTrigger>
                  <DropdownMenuSubContent>
                    {categoryMetadataFields?.length === 0 && (
                      <DropdownMenuItem disabled>
                        No categorical metadata found
                      </DropdownMenuItem>
                    )}
                    {categoryMetadataFields?.map((field) => (
                      <DropdownMenuItem
                        key={field}
                        onClick={() => {
                          setSelectedMetric("count_unique");
                          setmetadata_metric(field);
                        }}
                      >
                        {field}
                      </DropdownMenuItem>
                    ))}
                  </DropdownMenuSubContent>
                </DropdownMenuSub>
                <DropdownMenuSub>
                  <DropdownMenuSubTrigger>
                    <Code className="size-4 mr-2" />
                    Avg of metadata
                  </DropdownMenuSubTrigger>
                  <DropdownMenuPortal>
                    <DropdownMenuSubContent>
                      {numberMetadataFields?.length === 0 && (
                        <DropdownMenuItem disabled>
                          No numeric metadata found
                        </DropdownMenuItem>
                      )}
                      {numberMetadataFields?.map((field) => (
                        // TODO : Add a way to indicate this is a sum
                        <DropdownMenuItem
                          key={field}
                          onClick={() => {
                            setSelectedMetric("Avg");
                            setmetadata_metric(field);
                          }}
                        >
                          {field}
                        </DropdownMenuItem>
                      ))}
                    </DropdownMenuSubContent>
                  </DropdownMenuPortal>
                </DropdownMenuSub>
                <DropdownMenuSub>
                  <DropdownMenuSubTrigger>
                    <Code className="size-4 mr-2" />
                    Sum of metadata
                  </DropdownMenuSubTrigger>
                  <DropdownMenuPortal>
                    <DropdownMenuSubContent>
                      {numberMetadataFields?.length === 0 && (
                        <DropdownMenuItem disabled>
                          No numeric metadata found
                        </DropdownMenuItem>
                      )}
                      {numberMetadataFields?.map((field) => (
                        // TODO : Add a way to indicate this is a sum
                        <DropdownMenuItem
                          onClick={() => {
                            setSelectedMetric("Sum");
                            setmetadata_metric(field);
                          }}
                          key={field}
                        >
                          {field}
                        </DropdownMenuItem>
                      ))}
                    </DropdownMenuSubContent>
                  </DropdownMenuPortal>
                </DropdownMenuSub>
              </DropdownMenuContent>
            </DropdownMenu>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline">
                  Breakdown by: {breakdown_by}{" "}
                  <ChevronDown className="size-4 ml-2" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem
                  onClick={() => {
                    setSelectedGroupBy("None");
                  }}
                >
                  None
                </DropdownMenuItem>
                <DropdownMenuItem
                  onClick={() => {
                    setSelectedGroupBy("tagger_name");
                  }}
                >
                  <TextSearch className="size-4 mr-2" />
                  Tagger name
                </DropdownMenuItem>
                <DropdownMenuItem
                  onClick={() => {
                    setSelectedGroupBy("scorer_name");
                  }}
                >
                  <TextSearch className="size-4 mr-2" />
                  Scorer name
                </DropdownMenuItem>
                <DropdownMenuItem
                  onClick={() => {
                    setSelectedGroupBy("flag");
                  }}
                >
                  <Flag className="size-4 mr-2" />
                  Human rating
                </DropdownMenuItem>
                <DropdownMenuItem
                  onClick={() => {
                    setSelectedGroupBy("task_position");
                  }}
                >
                  <List className="size-4 mr-2" />
                  Message position
                </DropdownMenuItem>
                <DropdownMenuItem
                  onClick={() => {
                    setSelectedGroupBy("session_length");
                  }}
                >
                  <List className="size-4 mr-2" />
                  Session length
                </DropdownMenuItem>
                <DropdownMenuSub>
                  <DropdownMenuSubTrigger>
                    <Timer className="size-4 mr-2" />
                    Time
                  </DropdownMenuSubTrigger>
                  <DropdownMenuPortal>
                    <DropdownMenuSubContent>
                      <DropdownMenuItem
                        onClick={() => {
                          setSelectedGroupBy("day");
                        }}
                      >
                        Day
                      </DropdownMenuItem>
                      <DropdownMenuItem
                        onClick={() => {
                          setSelectedGroupBy("week");
                        }}
                      >
                        Week
                      </DropdownMenuItem>
                      <DropdownMenuItem
                        onClick={() => {
                          setSelectedGroupBy("month");
                        }}
                      >
                        Month
                      </DropdownMenuItem>
                    </DropdownMenuSubContent>
                  </DropdownMenuPortal>
                </DropdownMenuSub>
                <DropdownMenuSub>
                  <DropdownMenuSubTrigger>
                    <Code className="size-4 mr-2" />
                    Metadata
                  </DropdownMenuSubTrigger>
                  <DropdownMenuPortal>
                    <DropdownMenuSubContent>
                      {categoryMetadataFields?.length === 0 && (
                        <DropdownMenuItem disabled>
                          No categorical metadata found
                        </DropdownMenuItem>
                      )}
                      {categoryMetadataFields?.map((field) => (
                        <DropdownMenuItem
                          onClick={() => setSelectedGroupBy(field)}
                          key={`${field}_metadata`}
                        >
                          {field}
                        </DropdownMenuItem>
                      ))}
                    </DropdownMenuSubContent>
                  </DropdownMenuPortal>
                </DropdownMenuSub>
              </DropdownMenuContent>
            </DropdownMenu>
            <HoverCard openDelay={0} closeDelay={0}>
              <HoverCardTrigger asChild>
                <Button
                  size="icon"
                  variant="ghost"
                  onClick={() => {
                    setDatavizSorting({
                      ...datavizSorting,
                      desc: !datavizSorting.desc,
                    });
                  }}
                >
                  {datavizSorting.desc && <ArrowDown className="size-4" />}
                  {!datavizSorting.desc && <ArrowUp className="size-4" />}
                </Button>
              </HoverCardTrigger>
              <HoverCardContent className="text-xs">
                Sorting: {datavizSorting.desc ? "Descending" : "Ascending"}
              </HoverCardContent>
            </HoverCard>
            <HoverCard openDelay={0} closeDelay={0}>
              <HoverCardTrigger asChild>
                <Button
                  size="icon"
                  variant="ghost"
                  onClick={() => {
                    setDatavizSorting({
                      ...datavizSorting,
                      id:
                        datavizSorting.id === "breakdown_by"
                          ? "metric"
                          : "breakdown_by",
                    });
                  }}
                >
                  {datavizSorting.id === "breakdown_by" && (
                    <BarChart className="size-4 rotate-90" />
                  )}
                  {datavizSorting.id === "metric" && (
                    <BarChart className="size-4 transform -rotate-90" />
                  )}
                </Button>
              </HoverCardTrigger>
              <HoverCardContent className="text-xs">
                Sorting by: {datavizSorting.id}
              </HoverCardContent>
            </HoverCard>
          </div>
          <Button
            onClick={async () => {
              // Add a new tile to the selectedProjectSettings and update it server side
              if (!selectedProject) return;
              if (!selectedProject.settings) return;

              const tileName = metadata_metric
                ? `${metadata_metric} by ${breakdown_by}`
                : `${selectedMetric} by ${breakdown_by}`;

              const newTile = {
                tile_name: tileName,
                metric: selectedMetric,
                metadata_metric: metadata_metric,
                breakdown_by: breakdown_by,
                scorer_id: selectedScorerId,
                filters: dataFilters,
              } as DashboardTile;
              selectedProject.settings.dashboard_tiles.push(newTile);

              // Push updates
              try {
                await fetch(`/api/projects/${selectedProject.id}`, {
                  method: "POST",
                  headers: {
                    Authorization: "Bearer " + accessToken,
                    "Content-Type": "application/json",
                  },
                  body: JSON.stringify(selectedProject),
                }).then(() => {
                  mutate(
                    [`/api/projects/${selectedProject.id}`, accessToken],
                    async () => {
                      return { project: selectedProject };
                    },
                  );
                  // Redirect to the dashboard
                  router.push("/org/dataviz/dashboard");
                });
              } catch (error) {
                toast({
                  title: "Error when creating tile",
                  description: `${error}`,
                });
              }
            }}
          >
            <Plus className="h-3 w-3" />
            <LayoutDashboard className="size-4 mr-2" />
            Add to dashboard
          </Button>
        </div>
        <div className="flex flex-row space-x-2 items-end">
          <DatePickerWithRange />
          <FilterComponent variant="tasks" />
        </div>
        <div className="h-[80vh] overflow-y-auto">
          <DatavizGraph
            metric={selectedMetric}
            metadata_metric={metadata_metric}
            breakdown_by={breakdown_by}
            scorer_id={
              selectedMetric === "avg_scorer_value" ? selectedScorerId : null
            }
            sorting={datavizSorting}
          />
        </div>
      </div>
    </>
  );
};

export default MetadataForm;
