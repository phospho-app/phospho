"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useToast } from "@/components/ui/use-toast";
import { authFetcher } from "@/lib/fetcher";
import { cn } from "@/lib/utils";
import { dataStateStore, navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import React from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import useSWR from "swr";

const DatavizGraph = ({
  metric,
  selectedMetricMetadata,
  breakdown_by,
}: {
  metric: string;
  selectedMetricMetadata?: string | null;
  breakdown_by: string;
}) => {
  const { accessToken } = useUser();
  const { toast } = useToast();
  const project_id = navigationStateStore((state) => state.project_id);

  const selectedProject = dataStateStore((state) => state.selectedProject);
  const dataFilters = navigationStateStore((state) => state.dataFilters);

  const { data } = useSWR(
    [`/api/metadata/${project_id}/fields`, accessToken],
    ([url, accessToken]) => authFetcher(url, accessToken, "POST"),
    {
      keepPreviousData: true,
    },
  );
  const numberMetadataFields: string[] | undefined = data?.number;
  const categoryMetadataFields: string[] | undefined = data?.string;

  const { data: pivotData, isLoading: pivotLoading } = useSWR(
    [
      `/api/metadata/${project_id}/pivot/`,
      accessToken,
      metric,
      selectedMetricMetadata,
      breakdown_by,
      numberMetadataFields,
      categoryMetadataFields,
      JSON.stringify(dataFilters),
    ],
    ([url, accessToken]) =>
      authFetcher(url, accessToken, "POST", {
        metric: metric,
        metric_metadata: selectedMetricMetadata,
        breakdown_by: breakdown_by,
        number_metadata_fields: numberMetadataFields,
        category_metadata_fields: categoryMetadataFields,
        filters: dataFilters,
      }).then((response) => {
        return response?.pivot_table;
      }),
    {
      keepPreviousData: true,
    },
  );

  const graphColors = [
    "#22c55e",
    "#ff7c7c",
    "#ffbb43",
    "#4a90e2",
    "#a259ff",
    "#FFDE82",
    "#CBA74E",
    "#917319",
    "#E2E3D8",
    "#68EDCB",
    "#00C4FF",
    "#9FAFA1",
    "#EB6D00",
    "#D3D663",
    "#92CF56",
    "#FFDE82",
    "#FA003C",
    "#9FA8DF",
    "#005400",
    "#505C8D",
  ];
  const isStacked = pivotData?.length > 1 && "stack" in pivotData[0];

  if (!numberMetadataFields || !categoryMetadataFields) {
    return <></>;
  }

  if (
    breakdown_by === "language" &&
    !categoryMetadataFields.includes("language")
  ) {
    return <>No language metadata found</>;
  }
  if (
    selectedMetricMetadata === "sentiment_score" &&
    !numberMetadataFields.includes("sentiment_score")
  ) {
    return <></>;
  }

  // Display the data or "Loading..."
  return (
    <>
      {!pivotData && pivotLoading && <p>Loading...</p>}
      {(pivotData === null || pivotData?.length == 0) && <>no data</>}
      {pivotData?.length == 1 && (
        <>
          <Card>
            <CardHeader>
              <CardTitle className="text-xl font-light tracking-tight">
                {!pivotData[0]["breakdown_by"] && (
                  <p>{pivotData[0]["breakdown_by"]}</p>
                )}
                {pivotData[0]["breakdown_by"] === "NaN" && <p>No breakdown</p>}
              </CardTitle>
            </CardHeader>
            <CardContent className="text-xl font-extrabold">
              <p>
                {Math.round(
                  pivotData[0][`${metric}${selectedMetricMetadata ?? ""}`] *
                    10000,
                ) / 10000}
              </p>
            </CardContent>
          </Card>
        </>
      )}
      {pivotData?.length > 1 && (
        <ResponsiveContainer width="100%" height="100%" minHeight="14rem">
          <BarChart
            data={pivotData}
            layout="vertical"
            margin={{
              top: 0,
              right: 0,
              bottom: 0,
              left: 0,
            }}
          >
            <CartesianGrid />
            <Tooltip
              formatter={(value) => {
                if (typeof value === "string") return value;
                if (typeof value === "number")
                  return `${Math.round(value * 100) / 100}`;
              }}
              content={({ active, payload, label }) => {
                if (active && payload && payload.length) {
                  return (
                    <div className="bg-primary shadow-md p-2 rounded-md space-y-1">
                      <div className="text-secondary font-semibold">{`${breakdown_by}: ${label}`}</div>
                      <div>
                        {payload.map((item: any) => {
                          const itemName = item.name.split(".")[1]
                            ? item.name.split(".")[1]
                            : item.name;
                          const formatedValue =
                            typeof item.value === "number"
                              ? Math.round(item.value * 1000) / 1000
                              : item.value;

                          // Get the color of the bar
                          let index = 0;
                          if (isStacked) {
                            // use Object.keys(selectedProject?.settings?.events to get the index color
                            index = Object.keys(
                              selectedProject?.settings?.events ?? {},
                            ).indexOf(item.name.split(".")[1]);
                          }
                          const color = graphColors[index % graphColors.length];

                          return (
                            <div className="flex flex-row space-x-2 items-center">
                              <div
                                className="w-4 h-4"
                                style={{ backgroundColor: color }}
                              ></div>
                              <div key={item.name} className="text-secondary">
                                {itemName}: {formatedValue}
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  );
                }
              }}
            />
            <YAxis
              dataKey={"breakdown_by"}
              stroke="#888888"
              fontSize={12}
              tickLine={false}
              axisLine={false}
              type="category"
              tickFormatter={(value: any) => {
                // if value is a string and is too long, truncate it
                if (typeof value === "string" && value.length > 30) {
                  return value.slice(0, 30) + "...";
                }
                return value;
              }}
              width={100}
            />
            <XAxis
              stroke="#888888"
              fontSize={12}
              type="number"
              domain={[0, "dataMax + 1"]}
              // tickLine={false}
              // axisLine={false}
              tickFormatter={(value) => `${Math.round(value * 100) / 100}`}
            />
            {!isStacked && (
              <Bar
                dataKey={"metric"}
                fill="#22c55e"
                stackId="a"
                // radius={[0, 20, 20, 0]}
                onClick={(data) => {
                  // Copy the Y value to the clipboard
                  navigator.clipboard.writeText(data["_id"]);
                  toast({
                    title: "Copied to clipboard",
                    description: data["_id"],
                  });
                }}
              />
            )}
            {isStacked &&
              // Loop over the keys of the dict and create a bar for each key
              Object.keys(selectedProject?.settings?.events ?? {}).map(
                (key, index) => {
                  return (
                    <Bar
                      key={key}
                      dataKey={`stack.${key}`}
                      fill={graphColors[index % graphColors.length]}
                      stackId="a"
                      // radius={[0, 20, 20, 0]}
                      onClick={(data) => {
                        // Copy the Y value to the clipboard
                        navigator.clipboard.writeText(data["_id"]);
                        toast({
                          title: "Copied to clipboard",
                          description: data["_id"],
                        });
                      }}
                    />
                  );
                },
              )}
          </BarChart>
        </ResponsiveContainer>
      )}
    </>
  );
};

export default DatavizGraph;
