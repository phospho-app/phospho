"use client";

import { DatavizCallout } from "@/components/callouts/import-data";
import DatavizGraph from "@/components/dataviz";
import { DatePickerWithRange } from "@/components/date-range";
import FilterComponent from "@/components/filters";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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
import { authFetcher } from "@/lib/fetcher";
import { navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import {
  ChevronDown,
  Code,
  Flag,
  List,
  MessagesSquare,
  TextSearch,
} from "lucide-react";
import React from "react";
import useSWR from "swr";

const MetadataForm: React.FC = () => {
  // create a page with 2 dropdowns :
  // 1. Metric: count of tasks, avg session length, sum of a metadata field,
  // 2. Groupby field : None ; metadataField (user_id, version_id, etc. ) ; event_name ; flag

  // The data is fetched and then displayed as a bar chart or a table

  const { accessToken } = useUser();
  const project_id = navigationStateStore((state) => state.project_id);

  const selectedMetric = navigationStateStore((state) => state.selectedMetric);
  const selectedMetricMetadata = navigationStateStore(
    (state) => state.selectedMetricMetadata,
  );
  const selectedGroupBy = navigationStateStore(
    (state) => state.selectedGroupBy,
  );
  const setSelectedMetric = navigationStateStore(
    (state) => state.setSelectedMetric,
  );
  const setSelectedMetricMetadata = navigationStateStore(
    (state) => state.setSelectedMetricMetadata,
  );
  const setSelectedGroupBy = navigationStateStore(
    (state) => state.setSelectedGroupBy,
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
      <div className="flex flex-col space-y-2">
        <DatavizCallout />
        <div className="flex flex-row space-x-2 items-center">
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline">
                Metric: {selectedMetric} {selectedMetricMetadata ?? ""}{" "}
                <ChevronDown className="h-4 w-4 ml-2" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem
                onClick={() => {
                  setSelectedMetric("Nb tasks");
                  setSelectedMetricMetadata(null);
                }}
              >
                <MessagesSquare className="h-4 w-4 mr-2" />
                Tasks count
              </DropdownMenuItem>
              <DropdownMenuItem
                onClick={() => {
                  setSelectedMetric("Event count");
                  setSelectedMetricMetadata(null);
                }}
              >
                <TextSearch className="h-4 w-4 mr-2" />
                Event count
              </DropdownMenuItem>
              <DropdownMenuItem
                onClick={() => {
                  setSelectedMetric("Event distribution");
                  setSelectedMetricMetadata(null);
                }}
              >
                <TextSearch className="h-4 w-4 mr-2" />
                Event distribution
              </DropdownMenuItem>
              <DropdownMenuItem
                onClick={() => {
                  setSelectedMetric("Avg Success rate");
                  setSelectedMetricMetadata(null);
                }}
              >
                <Flag className="h-4 w-4 mr-2" />
                Success rate
              </DropdownMenuItem>
              <DropdownMenuItem
                onClick={() => {
                  setSelectedMetric("Avg session length");
                  setSelectedMetricMetadata(null);
                }}
              >
                <List className="h-4 w-4 mr-2" />
                Avg session length
              </DropdownMenuItem>
              <DropdownMenuSub>
                <DropdownMenuSubTrigger>
                  <Code className="h-4 w-4 mr-2" />
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
                          setSelectedMetricMetadata(field);
                        }}
                      >
                        {`${field}_avg`}
                      </DropdownMenuItem>
                    ))}
                  </DropdownMenuSubContent>
                </DropdownMenuPortal>
              </DropdownMenuSub>
              <DropdownMenuSub>
                <DropdownMenuSubTrigger>
                  <Code className="h-4 w-4 mr-2" />
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
                          setSelectedMetricMetadata(field);
                        }}
                        key={`${field}_sum`}
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
                Breakdown by: {selectedGroupBy}{" "}
                <ChevronDown className="h-4 w-4 ml-2" />
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
                  setSelectedGroupBy("event_name");
                }}
              >
                <TextSearch className="h-4 w-4 mr-2" />
                Event name
              </DropdownMenuItem>
              <DropdownMenuItem
                onClick={() => {
                  setSelectedGroupBy("flag");
                }}
              >
                <Flag className="h-4 w-4 mr-2" />
                Eval
              </DropdownMenuItem>
              <DropdownMenuItem
                onClick={() => {
                  setSelectedGroupBy("task_position");
                }}
              >
                <List className="h-4 w-4 mr-2" />
                Task position
              </DropdownMenuItem>
              <DropdownMenuSub>
                <DropdownMenuSubTrigger>
                  <Code className="h-4 w-4 mr-2" />
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
        </div>
        <div className="flex flex-row space-x-2 items-center">
          <DatePickerWithRange />
          <FilterComponent variant="tasks" />
        </div>
      </div>
      <div className="h-3/4">
        <DatavizGraph
          metric={selectedMetric}
          selectedMetricMetadata={selectedMetricMetadata}
          breakdown_by={selectedGroupBy}
        />
      </div>
    </>
  );
};

export default MetadataForm;
