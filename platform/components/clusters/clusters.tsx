"use client";

import { ClusteringLoading } from "@/components/clusters/clusters-loading";
import RunClusteringSheet from "@/components/clusters/clusters-sheet";
import { AlertDialog, AlertDialogTrigger } from "@/components/ui/alert-dialog";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
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
import {
  HoverCard,
  HoverCardContent,
  HoverCardTrigger,
} from "@/components/ui/hover-card";
import { Sheet, SheetTrigger } from "@/components/ui/sheet";
import { authFetcher } from "@/lib/fetcher";
import { formatUnixTimestampToLiteralDatetime } from "@/lib/time";
import { Clustering } from "@/models/models";
import { navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import { Boxes, Pencil, Plus, Settings, X } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import * as React from "react";
import useSWR from "swr";

import { ClustersCards } from "./clusters-cards";
import { ClusteringDropDown } from "./clusters-drop-down";
import { CustomPlot } from "./clusters-plot";
import RenameClusteringDialog from "./rename-clustering";

const Clusters: React.FC = () => {
  const project_id = navigationStateStore((state) => state.project_id);
  const { accessToken } = useUser();
  const [sheetClusterOpen, setSheetClusterOpen] = useState(false);
  const selectedClustering = navigationStateStore(
    (state) => state.selectedClustering,
  );
  const setSelectedClustering = navigationStateStore(
    (state) => state.setSelectedClustering,
  );
  const [openRename, setOpenRename] = useState(false);
  const [dropdownOpen, setDropdownOpen] = React.useState(false);

  const { data: clusteringsData } = useSWR(
    project_id ? [`/api/explore/${project_id}/clusterings`, accessToken] : null,
    ([url, accessToken]) =>
      authFetcher(url, accessToken, "POST").then((res) => {
        return res;
      }),
    {
      keepPreviousData: true,
    },
  );
  const clusterings = clusteringsData
    ? (clusteringsData.clusterings.sort(
        (a: Clustering, b: Clustering) =>
          new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
      ) as Clustering[])
    : undefined;

  let selectedClusteringName = selectedClustering?.name;
  if (selectedClustering && !selectedClusteringName) {
    selectedClusteringName = formatUnixTimestampToLiteralDatetime(
      selectedClustering.created_at,
    );
  }

  const clusteringsJSON = useMemo(
    () => JSON.stringify(clusterings),
    [clusterings],
  );

  useEffect(() => {
    if (clusterings === undefined) {
      setSelectedClustering(undefined);
      return;
    }
    if (clusterings.length === 0) {
      setSelectedClustering(undefined);
      return;
    }
    // if the selected clustering is not set, select the latest clustering
    if (selectedClustering === undefined) {
      setSelectedClustering(clusterings[0]);
      return;
    }
    // If project_id of the selectedClustering is different from the
    // one in the navigationStateStore, select the latest clustering
    if (
      selectedClustering.project_id !== project_id &&
      clusterings.length > 0
    ) {
      setSelectedClustering(clusterings[0]);
      return;
    } else if (selectedClustering.project_id !== project_id) {
      // If the clusterings are empty, set the selectedClustering to undefined
      setSelectedClustering(undefined);
      return;
    }
  }, [
    clusterings,
    clusteringsJSON,
    project_id,
    selectedClustering,
    setSelectedClustering,
  ]);

  if (!project_id) {
    return <></>;
  }

  return (
    <>
      <AlertDialog open={openRename}>
        <Sheet open={sheetClusterOpen} onOpenChange={setSheetClusterOpen}>
          <RunClusteringSheet
            setSheetOpen={setSheetClusterOpen}
            setSelectedClustering={setSelectedClustering}
          />
          {clusterings && clusterings.length <= 1 && (
            <Card className="bg-secondary">
              <CardHeader>
                <div className="flex justify-between items-center">
                  <div className="flex">
                    <Boxes className="mr-4 h-16 w-16 hover:text-green-500 transition-colors" />
                    <div>
                      <CardTitle className="flex flex-row text-2xl font-bold tracking-tight items-center">
                        Automatic cluster detection
                      </CardTitle>
                      <CardDescription className="text-muted-foreground">
                        Detect recurring topics, trends, and outliers using
                        unsupervized machine learning.{" "}
                        <a
                          href="https://docs.phospho.ai/analytics/clustering"
                          target="_blank"
                          className="underline"
                        >
                          Learn more.
                        </a>
                      </CardDescription>
                    </div>
                  </div>
                </div>
              </CardHeader>
            </Card>
          )}
          {clusterings && clusterings.length > 1 && (
            <h1 className="text-2xl font-bold">Clusterings</h1>
          )}
          <div>
            <div className="flex flex-row space-x-2">
              <DropdownMenu open={dropdownOpen} onOpenChange={setDropdownOpen}>
                <DropdownMenuTrigger asChild>
                  <div>
                    <HoverCard openDelay={0} closeDelay={0}>
                      <HoverCardTrigger asChild>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="text-muted-foreground hover:text-primary h-8 w-8"
                        >
                          <Settings />
                        </Button>
                      </HoverCardTrigger>
                      <HoverCardContent
                        className="m-0 text-xs text-background bg-foreground"
                        align="center"
                        avoidCollisions={false}
                      >
                        <span>Settings</span>
                      </HoverCardContent>
                    </HoverCard>
                  </div>
                </DropdownMenuTrigger>
                <DropdownMenuContent>
                  <DropdownMenuItem
                    onClick={() => {
                      setOpenRename(true);
                    }}
                  >
                    <Pencil className="h-4 w-4 mr-2" />
                    Rename clustering
                    <RenameClusteringDialog
                      open={openRename}
                      setOpen={setOpenRename}
                      clusteringToEdit={selectedClustering}
                    />
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
              <ClusteringDropDown
                selectedClustering={selectedClustering}
                setSelectedClustering={setSelectedClustering}
                clusterings={clusterings}
                selectedClusteringName={selectedClusteringName}
              />
              <SheetTrigger asChild>
                <Button>
                  <Plus className="w-4 h-4 mr-1" /> New clustering
                </Button>
              </SheetTrigger>
            </div>
            {selectedClustering && (
              <div className="space-x-2 mb-2">
                <Badge variant="secondary">
                  {`Instruction: ${selectedClustering?.instruction}` ??
                    "No instruction"}
                </Badge>
                <Badge variant="secondary">
                  {selectedClustering?.nb_clusters ?? "No"} clusters
                </Badge>
                <Badge variant="secondary">
                  {formatUnixTimestampToLiteralDatetime(
                    selectedClustering.created_at,
                  )}
                </Badge>
                <Badge variant="secondary">
                  scope: {selectedClustering.scope}
                </Badge>
              </div>
            )}
            <div className="flex-col space-y-2 md:flex pb-10">
              {selectedClustering &&
                selectedClustering.status !== "completed" && (
                  <ClusteringLoading
                    selectedClustering={selectedClustering}
                    setSelectedClustering={setSelectedClustering}
                  />
                )}
              {clusterings && clusterings.length === 0 && (
                <CustomPlot
                  dummyData={true}
                  displayCTA={true}
                  setSheetClusterOpen={setSheetClusterOpen}
                />
              )}
              {selectedClustering !== undefined &&
                selectedClustering !== null && (
                  <CustomPlot
                    selected_clustering_id={selectedClustering.id}
                    selectedClustering={selectedClustering}
                  />
                )}
              <ClustersCards
                setSheetClusterOpen={setSheetClusterOpen}
                selectedClustering={selectedClustering}
              />
            </div>
          </div>
          <div className="h-10"></div>
        </Sheet>
      </AlertDialog>
    </>
  );
};

export default Clusters;
