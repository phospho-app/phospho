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
import { ChevronDown } from "lucide-react";
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

export const ABTestingDataviz = ({
  versionIDs,
}: {
  versionIDs: string[] | undefined;
}) => {
  const { accessToken } = useUser();
  const project_id = navigationStateStore((state) => state.project_id);
  const [versionIDA, setVersionIDA] = useState<string>("");
  const [versionIDB, setVersionIDB] = useState<string>("");

  useEffect(() => {
    if (versionIDs && versionIDs.length > 1) {
      setVersionIDA(versionIDs[0]);
      setVersionIDB(versionIDs[1]);
    }
  }, [project_id]); // We want to select the first 2 versions when the project_id changes

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

  if (!versionIDA || !versionIDB) {
    setVersionIDA(versionIDs[0]);
    setVersionIDB(versionIDs[1]);
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
                {versionID}
              </DropdownMenuItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
      <div className="flex flex-col items-center">
        <ResponsiveContainer width={1000} height={400}>
          <BarChart data={graphData}>
            <XAxis dataKey="event_name" />
            <Tooltip
              content={<CustomTooltip active={""} payload={""} label={""} />}
            />
            <Legend />
            <Bar dataKey={versionIDA} fill="#28BB62" />
            <Bar dataKey={versionIDB} fill="#82ca9d" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </>
  );
};

export const CustomTooltip = ({
  active,
  payload,
  label,
}: {
  active: any;
  payload: any;
  label: any;
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
            {payload.map((pld: any) => (
              <div style={{ display: "inline-block", padding: 10 }}>
                <div>{pld.value.toFixed(2)}</div>
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
