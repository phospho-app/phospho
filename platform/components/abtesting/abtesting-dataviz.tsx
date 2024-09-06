// This component displays a bar chart showing the number of events detected in each task with the version number
// Each event has 2 bars, one for each version
import { Spinner } from "@/components/small-spinner";
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
import { authFetcher } from "@/lib/fetcher";
import { navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import { Check, ChevronDown } from "lucide-react";
import { useSearchParams } from "next/navigation";
import React, { useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
} from "recharts";
import useSWR from "swr";

import { Skeleton } from "../ui/skeleton";

export const ABTestingDataviz = ({ versionIDs }: { versionIDs: string[] }) => {
  // In the URL, use the search params ?a=version_id&b=version_id to set the default versions in the dropdown

  const { accessToken } = useUser();
  const project_id = navigationStateStore((state) => state.project_id);

  // Get the version IDs from the URL. If not present, use the first two version IDs
  const searchParams = useSearchParams();

  function computeVersionsIds() {
    let versionADefault = searchParams.get("a");
    let versionBDefault = searchParams.get("b");
    if (versionADefault) {
      versionADefault = decodeURIComponent(versionADefault);
    } else {
      versionADefault = versionIDs[0];
    }
    if (versionBDefault) {
      versionBDefault = decodeURIComponent(versionBDefault);
    } else {
      versionBDefault = versionIDs[1];
    }
    return { versionADefault, versionBDefault };
  }

  const [versionIDA, setVersionIDA] = useState<string | null>(
    computeVersionsIds().versionADefault,
  );
  const [versionIDB, setVersionIDB] = useState<string | null>(
    computeVersionsIds().versionBDefault,
  );

  useEffect(() => {
    if (versionIDs.length === 0) {
      setVersionIDA(null);
      setVersionIDB(null);
    } else if (versionIDs.length == 1) {
      setVersionIDA(versionIDs[0]);
      setVersionIDB(versionIDs[0]);
    } else if (versionIDs.length >= 2) {
      setVersionIDA(computeVersionsIds().versionADefault);
      setVersionIDB(computeVersionsIds().versionBDefault);
    }
  }, [JSON.stringify(versionIDs)]);

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

  console.log("graphData", graphData);
  console.log("versionIDA", versionIDA);
  console.log("versionIDB", versionIDB);

  if (!project_id || !versionIDs) {
    return <></>;
  }

  return (
    <>
      <div className="flex justify-center z-0 space-x-2">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline">
              <div className="flex flex-row items-center justify-between min-w-[10rem]">
                Reference version A: {versionIDA}{" "}
                <ChevronDown className="h-4 w-4 ml-2" />
              </div>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent
            align="end"
            className="overflow-y-auto max-h-[40rem] "
          >
            {versionIDs.map((versionID) => (
              <DropdownMenuItem
                className="min-w-[10rem]"
                key={`${versionID}_A`}
                onClick={() => setVersionIDA(versionID)}
              >
                {versionID === versionIDA && (
                  <Check className="h-4 w-4 mr-2 text-green-500" />
                )}
                {versionID}
              </DropdownMenuItem>
            ))}
            {versionIDs.length === 0 && (
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
                Candidate version B: {versionIDB}{" "}
                <ChevronDown className="h-4 w-4 ml-2" />
              </div>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent
            align="end"
            className="overflow-y-auto max-h-[40rem]"
          >
            {versionIDs.map((versionID) => (
              <DropdownMenuItem
                key={`${versionID}_B`}
                onClick={() => setVersionIDB(versionID)}
              >
                {versionID === versionIDB && (
                  <Check className="h-4 w-4 mr-2 text-green-500" />
                )}
                {versionID}
              </DropdownMenuItem>
            ))}
            {versionIDs.length === 0 && (
              <DropdownMenuItem disabled>
                <p>
                  No <code>version_id</code> found
                </p>
              </DropdownMenuItem>
            )}
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
      <div className="flex flex-col items-center my-2">
        {(!graphData ||
          !versionIDA ||
          !versionIDB ||
          graphData.length == 0) && <Skeleton className="w-[100%] h-[400px]" />}
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
    </>
  );
};

export const CustomTooltip = ({ active, payload, label }: any) => {
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
            {payload.map((pld: any) => (
              <div style={{ display: "inline-block", padding: 10 }}>
                <div>{pld.payload[pld.dataKey + "_tooltip"].toFixed(2)}</div>
                <div>{pld.dataKey}</div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    );
  }

  return null;
};
