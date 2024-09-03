"use client";

import RunClusters from "@/components/insights/clusters/clusters-sheet";
import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { authFetcher } from "@/lib/fetcher";
import { formatUnixTimestampToLiteralDatetime } from "@/lib/time";
import { Clustering } from "@/models/models";
import { navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import { useEffect, useState } from "react";
import useSWR from "swr";

import { ClustersCards } from "./clusters-cards";

const Clusters: React.FC = () => {
  const project_id = navigationStateStore((state) => state.project_id);

  const [sheetClusterOpen, setSheetClusterOpen] = useState(false);

  if (!project_id) {
    return <></>;
  }

  return (
    <>
      <Card className="bg-secondary">
        <CardHeader>
          <div className="flex justify-between items-start">
            <div>
              <CardTitle className="flex flex-row text-2xl font-bold tracking-tight items-center">
                Automatic cluster detection
              </CardTitle>
              <CardDescription className="text-muted-foreground">
                Detect recurring topics, trends, and outliers using unsupervized
                machine learning.
              </CardDescription>
            </div>
            <div className="flex flex-col space-y-1 justify-center items-center">
              <RunClusters
                sheetOpen={sheetClusterOpen}
                setSheetOpen={setSheetClusterOpen}
              />
            </div>
          </div>
        </CardHeader>
      </Card>
      <div className="flex-col space-y-2 md:flex pb-10">
        <ClustersCards setSheetClusterOpen={setSheetClusterOpen} />
      </div>
    </>
  );
};

export default Clusters;
