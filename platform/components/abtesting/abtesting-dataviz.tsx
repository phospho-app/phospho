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

  const [versionIDA, setVersionIDA] = useState<string>(
    computeVersionsIds().versionADefault,
  );
  const [versionIDB, setVersionIDB] = useState<string>(
    computeVersionsIds().versionBDefault,
  );

  useEffect(() => {
    if (versionIDs.length >= 2) {
      setVersionIDA(computeVersionsIds().versionADefault);
      setVersionIDB(computeVersionsIds().versionBDefault);
    }
  }, [JSON.stringify(versionIDs)]);

  const { data: graphData } = useSWR(
    project_id && versionIDA && versionIDB
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

  if (!project_id || !versionIDs || versionIDs.length < 2) {
    return <></>;
  }

  if (!graphData) {
    return (
      <div className="flex flex-col items-center">
        <Spinner className="my-40" />
      </div>
    );
  }

  return (
    <>
      <div className="flex justify-center z-0 space-x-2">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline">
              Version A: {versionIDA} <ChevronDown className="h-4 w-4 ml-2" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent
            align="end"
            className="overflow-y-auto max-h-[40rem]"
          >
            {versionIDs.map((versionID) => (
              <DropdownMenuItem
                key={`${versionID}_A`}
                onClick={() => setVersionIDA(versionID)}
              >
                {versionID === versionIDA && (
                  <Check className="h-4 w-4 mr-2 text-green-500" />
                )}
                {versionID}
              </DropdownMenuItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline">
              Version B: {versionIDB} <ChevronDown className="h-4 w-4 ml-2" />
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
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
      <div className="flex flex-col items-center">
        <ResponsiveContainer width={"100%"} height={400}>
          <BarChart data={graphData}>
            <XAxis dataKey="event_name" />
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            <Bar dataKey={versionIDA} fill="#28BB62" />
            <Bar dataKey={versionIDB} fill="#82ca9d" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </>
  );
};

export const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    console.log("payload", payload);
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
