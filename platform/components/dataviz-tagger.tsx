"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { authFetcher } from "@/lib/fetcher";
import { navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import { set } from "date-fns";
import { useState } from "react";
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
import useSWRImmutable from "swr/immutable";

import { PivotTableElement } from "./dataviz";

const DatavizTaggerGraph = ({
  tagger_name,
  metric,
  metadata_metric,
  breakdown_by,
  scorer_id,
}: {
  tagger_name: string;
  metric: string;
  metadata_metric?: string | null;
  breakdown_by: string;
  scorer_id: string | null;
}) => {
  const { accessToken } = useUser();

  const project_id = navigationStateStore((state) => state.project_id);
  const dataFilters = navigationStateStore((state) => state.dataFilters);

  const [otherTags, setOtherTags] = useState<Record<string, number>[]>([]);

  const { data: pivotData2 } = useSWRImmutable(
    [
      `/api/metadata/${project_id}/pivot/`,
      accessToken,
      metric,
      metadata_metric,
      breakdown_by,
      scorer_id,
      JSON.stringify(dataFilters),
    ],
    ([url, accessToken]) =>
      authFetcher(url, accessToken, "POST", {
        metric: metric.toLowerCase(),
        metric_metadata: metadata_metric?.toLowerCase(),
        breakdown_by:
          breakdown_by !== "None" ? breakdown_by.toLowerCase() : null,
        scorer_id: scorer_id,
        filters: {
          ...dataFilters,
          event_name: dataFilters.event_name
            ? [...dataFilters.event_name, tagger_name]
            : [tagger_name],
        },
      }).then((response) => {
        const pivotTable = response?.pivot_table as PivotTableElement[] | null;
        if (!pivotTable) {
          return [];
        }
        // Replace "breakdown_by": null with "breakdown_by": "None"
        pivotTable.forEach((element: PivotTableElement) => {
          if (element.breakdown_by === null) {
            element.breakdown_by = "None";
          }
        });

        return pivotTable;
      }),
    {
      keepPreviousData: false,
      refreshInterval: 0,
      refreshWhenHidden: false,
      revalidateOnReconnect: true,
      revalidateOnFocus: false,
      revalidateOnMount: true,
      refreshWhenOffline: false,
    },
  );

  console.log("pivotdata2", pivotData2);

  return <>kdhfjds</>;
};

export default DatavizTaggerGraph;
