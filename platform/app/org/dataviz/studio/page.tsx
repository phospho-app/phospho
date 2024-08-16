"use client";

import { useEffect } from "react";
import { DatavizCallout } from "@/components/callouts/import-data";
import { DatePickerWithRange } from "@/components/date-range";
import FilterComponent from "@/components/filters";
import DatavizGraph from "@/components/insights/dataviz";
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
import { useToast } from "@/components/ui/use-toast";
import { authFetcher } from "@/lib/fetcher";
import { DashboardTile, Project } from "@/models/models";
import { navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import {
  ChevronDown,
  Code,
  Flag,
  LayoutDashboard,
  List,
  MessagesSquare,
  Plus,
  TextSearch,
  Timer,
} from "lucide-react";
import { useRouter } from "next/navigation";
import React from "react";
import useSWR, { mutate } from "swr";
import GenericDataviz from "@/components/dataviz/generic-dataviz";
import { AnalyticsQuery } from "@/models/models";
import { set } from "date-fns";
import { fi } from "date-fns/locale";

const MetadataForm: React.FC = () => {
  // create a page with 2 dropdowns :
  // 1. Metric: count of tasks, avg session length, sum of a metadata field,
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

  // New elements fo the AnanlyticsQuery
  const selectedAnalyticsQuery = navigationStateStore(
    (state) => state.selectedAnalyticsQuery,
  );
  const setSelectAnalyticsQuery = navigationStateStore(
    (state) => state.setSelectAnalyticsQuery,
  );

  const updateAnalyticsQuery = (updates: Partial<AnalyticsQuery>) => {
    setSelectAnalyticsQuery({
      ...selectedAnalyticsQuery,
      ...updates,
    });
  };

  const chartType = navigationStateStore((state) => state.chartType);
  const setChartType = navigationStateStore((state) => state.setChartType);

  const { data: selectedProject }: { data: Project } = useSWR(
    project_id ? [`/api/projects/${project_id}`, accessToken] : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "GET"),
    {
      keepPreviousData: true,
    },
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

  // Hardcoded fields that can be selected as aggregation fields
  const TasksFields = ["sentiment.score", "sentiment.magnitude", "sentiment.label", "task_position"];
  const SessionsFields = ["stats.avg_sentiment_score", "stats.avg_magnitude_score", "stats.avg_sentiment_label", "session_length"];

  // Add the numberMetadataFields to the list of TasksFields that can be selected as aggregation fields for tasks with a prefrix `metadata.`
  numberMetadataFields?.forEach((field) => {
    TasksFields.push(`metadata.${field}`);
  });

  // Hardcoded fields that can be selected as dimensions
  const TimeDimensions = ["day"]; // "minute", "hour", month
  const TasksDimensions = ["flag", "last_eval", "language", "environment", "task_position", "is_last_task"];
  const SessionsDimensions = ["stats.most_common_sentiment_label", "stats.most_common_language", "stats.most_common_flag", "stats.human_eval", "environment", "session_length"];
  const EventsDimension = ["event_name"];

  // Add the categoryMetadataFields to the list of TasksFields that can be selected as dimensions for tasks with a prefrix `metadata.`
  categoryMetadataFields?.forEach((field) => {
    TasksDimensions.push(`metadata.${field}`);
  });

  // Types of charts available
  const ChartTypes = ["line", "stackedBar", "pie"];

  // Update the AnalyticsQuery with the current project_id
  useEffect(() => {
    if (selectedProject) {
      updateAnalyticsQuery({
        project_id: selectedProject.id,
      });
    }
  }, [selectedProject]);

  // Get the selected DateRangePreset from the navigationStateStore
  const dateRangePreset = navigationStateStore((state) => state.dateRangePreset);

  // Handle date selection in the date picker
  useEffect(() => {
    // Handle the date range preset cases
    if (dateRangePreset === "last-24-hours") {
      updateAnalyticsQuery(
        {
          filters: {
            created_at_start: Math.floor(Date.now() / 1000) - 60 * 60 * 24,
          }
        });
    }
    if (dateRangePreset === "last-7-days") {
      updateAnalyticsQuery(
        {
          filters: {
            created_at_start: Math.floor(Date.now() / 1000) - 60 * 60 * 24 * 7,
          }
        });
    }
    if (dateRangePreset === "last-30-days") {
      updateAnalyticsQuery(
        {
          filters: {
            created_at_start: Math.floor(Date.now() / 1000) - 60 * 60 * 24 * 30,
          }
        });
    }
    if (dateRangePreset === "all-time") {
      updateAnalyticsQuery(
        {
          filters: {}
        });
    }
  }, [navigationStateStore((state) => state.dateRange)]);

  console.log("selectedProject ->", selectedProject);

  console.log("selectedAnalyticsQuery ->", selectedAnalyticsQuery)

  return (
    <>
      <div className="flex flex-col space-y-2">
        <DatavizCallout />
        <div className="flex flex-row space-x-2 items-center">
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline">
                Collection: {selectedAnalyticsQuery.collection}
                <ChevronDown className="h-4 w-4 ml-2" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem
                onClick={() => {
                  updateAnalyticsQuery({
                    collection: "sessions",
                    dimensions: [],
                  });
                }}
              >
                sessions
              </DropdownMenuItem>
              <DropdownMenuItem
                onClick={() => {
                  updateAnalyticsQuery({
                    collection: "tasks",
                    dimensions: []
                  });
                }}
              >
                tasks
              </DropdownMenuItem>
              <DropdownMenuItem
                onClick={() => {
                  updateAnalyticsQuery({
                    collection: "events",
                    dimensions: []
                  });
                }}
              >
                events
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline">
                Operation: {selectedAnalyticsQuery.aggregation_operation}
                <ChevronDown className="h-4 w-4 ml-2" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              {selectedAnalyticsQuery.collection === "events" ? (
                <DropdownMenuItem
                  onClick={() => {
                    updateAnalyticsQuery({
                      aggregation_operation: "count",
                    });
                  }}
                >
                  count
                </DropdownMenuItem>
              ) : (
                <>
                  <DropdownMenuItem
                    onClick={() => {
                      updateAnalyticsQuery({
                        aggregation_operation: "count",
                      });
                    }}
                  >
                    count
                  </DropdownMenuItem>
                  <DropdownMenuItem
                    onClick={() => {
                      updateAnalyticsQuery({
                        aggregation_operation: "sum",
                      });
                    }}
                  >
                    sum
                  </DropdownMenuItem>
                  <DropdownMenuItem
                    onClick={() => {
                      updateAnalyticsQuery(
                        {
                          aggregation_operation: "avg",
                        });
                    }}
                  >
                    avg
                  </DropdownMenuItem>
                  <DropdownMenuItem
                    onClick={() => {
                      updateAnalyticsQuery(
                        {
                          aggregation_operation: "min",
                        });
                    }}
                  >
                    min
                  </DropdownMenuItem>
                  <DropdownMenuItem
                    onClick={() => {
                      updateAnalyticsQuery(
                        {
                          aggregation_operation: "max",
                        });
                    }}
                  >
                    max
                  </DropdownMenuItem>
                </>)}
            </DropdownMenuContent>
          </DropdownMenu>
          {selectedAnalyticsQuery.aggregation_operation !== "count" && (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline">
                  OperationField: {selectedAnalyticsQuery.aggregation_field ?? "Select field"}
                  <ChevronDown className="h-4 w-4 ml-2" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                {selectedAnalyticsQuery.collection === "tasks"
                  ? TasksFields.map((field) => (
                    <DropdownMenuItem
                      key={field}
                      onClick={() => {
                        updateAnalyticsQuery({
                          aggregation_field: field,
                        });
                      }}
                    >
                      {field}
                    </DropdownMenuItem>
                  ))
                  : SessionsFields.map((field) => (
                    <DropdownMenuItem
                      key={field}
                      onClick={() => {
                        updateAnalyticsQuery({
                          aggregation_field: field,
                        });
                      }}
                    >
                      {field}
                    </DropdownMenuItem>
                  ))}
              </DropdownMenuContent>
            </DropdownMenu>
          )}
        </div>

        {/* Now, we have a section where you can add a new diemnsion or delete a dimension in the selected dimensions.
        First you have the already selected dimension, with a delete button, and then a dropdown to add a new dimension */}
        <div className="flex flex-row space-x-2 items-center">
          <div className="flex flex-row space-x-2 items-center">
            <p>Dimensions: </p>
            {selectedAnalyticsQuery.dimensions?.map((dimension) => (
              <div key={dimension} className="flex flex-row space-x-2 items-center">
                <Button
                  variant="secondary"
                  onClick={() => {
                    if (!selectedAnalyticsQuery.dimensions) return;
                    updateAnalyticsQuery({
                      dimensions: selectedAnalyticsQuery.dimensions.filter((d) => d !== dimension),
                    });
                  }}
                >
                  {dimension} X
                </Button>
              </div>
            ))}
          </div>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline">
                Add dimension
                <ChevronDown className="h-4 w-4 ml-2" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              {selectedAnalyticsQuery.collection === "tasks"
                ? TasksDimensions.map((field) => (
                  <DropdownMenuItem
                    key={field}
                    onClick={() => {
                      updateAnalyticsQuery({
                        dimensions: [...(selectedAnalyticsQuery.dimensions || []), field],
                      });
                    }}
                  >
                    {field}
                  </DropdownMenuItem>
                )) : selectedAnalyticsQuery.collection === "sessions"
                  ?
                  SessionsDimensions.map((field) => (
                    <DropdownMenuItem
                      key={field}
                      onClick={() => {
                        updateAnalyticsQuery({
                          dimensions: [...(selectedAnalyticsQuery.dimensions || []), field],
                        });
                      }}
                    >
                      {field}
                    </DropdownMenuItem>
                  )) : EventsDimension.map((field) => (
                    <DropdownMenuItem
                      key={field}
                      onClick={() => {
                        updateAnalyticsQuery({
                          dimensions: [...(selectedAnalyticsQuery.dimensions || []), field],
                        });
                      }}
                    >
                      {field}
                    </DropdownMenuItem>
                  ))}
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
        {/* yo */}
        <div className="flex flex-row space-x-2 items-center">
          <div className="flex flex-row space-x-2 items-center">
            <p>Chart type: </p>
          </div>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline">
                {chartType}
                <ChevronDown className="h-4 w-4 ml-2" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              {ChartTypes.map((field) => (
                <DropdownMenuItem
                  key={field}
                  onClick={() => {
                    setChartType(field);
                    // If it is pie, we update the time step to Null
                    if (field === "pie") {
                      updateAnalyticsQuery({
                        time_step: undefined,
                      });
                    }
                    else {
                      updateAnalyticsQuery({
                        time_step: "day",
                      });
                    }
                  }
                  }
                >
                  {field}
                </DropdownMenuItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>
          {chartType !== "pie" && (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline">
                  Time step: {selectedAnalyticsQuery.time_step ?? ""}
                  <ChevronDown className="h-4 w-4 ml-2" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                {TimeDimensions.map((field) => (
                  <DropdownMenuItem
                    key={field}
                    onClick={() => { // update the tiem_step field of the updateAnalyticsQuery
                      updateAnalyticsQuery({
                        time_step: field,
                      });
                    }}
                  >
                    {field}
                  </DropdownMenuItem>
                ))}
              </DropdownMenuContent>
            </DropdownMenu>
          )}

        </div>
        {/* start to delete */}
        <div className="flex flex-row justify-between">
          <div className="flex flex-row space-x-2 items-center">
            <DatePickerWithRange />
          </div>
          <Button
            onClick={async () => {
              // Add a new tile to the selectedProjectSettings and update it server side
              if (!selectedProject) return;
              if (!selectedProject.settings) return;

              // Generate a tile name based on the query
              //
              let tileName = `${selectedAnalyticsQuery.collection}`;

              if (selectedAnalyticsQuery.aggregation_operation && selectedAnalyticsQuery.aggregation_operation !== "count") {
                tileName += ` - ${selectedAnalyticsQuery.aggregation_operation} of ${selectedAnalyticsQuery.aggregation_field}`;
              }

              if (selectedAnalyticsQuery.dimensions && selectedAnalyticsQuery.dimensions.length > 0) {
                tileName += ` by ${selectedAnalyticsQuery.dimensions.join(", ")}`;
              }

              if (selectedAnalyticsQuery.time_step) {
                tileName += ` every ${selectedAnalyticsQuery.time_step}`;
              }

              // If a date range is specified, include it in the tile name
              if (selectedAnalyticsQuery.filters?.created_at_start) {
                const startDate = new Date(selectedAnalyticsQuery.filters.created_at_start * 1000);
                const endDate = selectedAnalyticsQuery.filters.created_at_end
                  ? new Date(selectedAnalyticsQuery.filters.created_at_end * 1000)
                  : new Date();
                tileName += ` from ${startDate.toLocaleDateString()} to ${endDate.toLocaleDateString()}`;
              } else {
                tileName += ` (All time)`;
              }

              const newTile = {
                tile_name: tileName,
                query: selectedAnalyticsQuery,
                type: chartType,
              } as DashboardTile;
              selectedProject.settings.dashboard_tiles.push(newTile);

              // Push updates
              try {
                const creation_response = await fetch(
                  `/api/projects/${selectedProject.id}`,
                  {
                    method: "POST",
                    headers: {
                      Authorization: "Bearer " + accessToken,
                      "Content-Type": "application/json",
                    },
                    body: JSON.stringify(selectedProject),
                  },
                ).then((response) => {
                  mutate(
                    [`/api/projects/${selectedProject.id}`, accessToken],
                    async (data: any) => {
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
            <LayoutDashboard className="h-4 w-4 mr-2" />
            Add to dashboard
          </Button>
        </div>
      </div >
      {
        chartType !== "pie" ? (
          <GenericDataviz analyticsQuery={selectedAnalyticsQuery} xField={selectedAnalyticsQuery?.time_step ?? "day"} yFields={selectedAnalyticsQuery.dimensions ?? []} chartType={chartType} />
        ) : (
          <GenericDataviz analyticsQuery={selectedAnalyticsQuery} xField={selectedAnalyticsQuery.dimensions ? selectedAnalyticsQuery.dimensions[0] : ""} yFields={["value"]} chartType={chartType} />
        )
      }
    </>
  );
};

export default MetadataForm;
