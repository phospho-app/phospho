"use client";

import CreateEvent from "@/components/events/create-event";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  HoverCard,
  HoverCardContent,
  HoverCardTrigger,
} from "@/components/ui/hover-card";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { authFetcher } from "@/lib/fetcher";
import {
  Cluster,
  Clustering,
  EventDefinition,
  OrgMetadata,
} from "@/models/models";
import { Project } from "@/models/models";
import { navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import { ChevronRight, Pickaxe, PlusIcon } from "lucide-react";
import { useRouter } from "next/navigation";
import React, { useState } from "react";
import useSWR from "swr";

import "./style.css";

function ClusterCard({
  cluster,
  setSheetClusterOpen,
}: {
  cluster: Cluster;
  setSheetClusterOpen: (value: boolean) => void;
}) {
  /* This is a single cluster card */
  const project_id = navigationStateStore((state) => state.project_id);
  const { accessToken } = useUser();
  const router = useRouter();
  const dataFilters = navigationStateStore((state) => state.dataFilters);
  const selectedOrgId = navigationStateStore((state) => state.selectedOrgId);
  const setDataFilters = navigationStateStore((state) => state.setDataFilters);
  const setDateRangePreset = navigationStateStore(
    (state) => state.setDateRangePreset,
  );

  const [sheetEventOpen, setSheetEventOpen] = useState(false);

  const { data: selectedProject }: { data: Project } = useSWR(
    project_id ? [`/api/projects/${project_id}`, accessToken] : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "GET"),
    {
      keepPreviousData: true,
    },
  );
  const { data: orgMetadata }: { data: OrgMetadata } = useSWR(
    selectedOrgId
      ? [`/api/organizations/${selectedOrgId}/metadata`, accessToken]
      : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "GET"),
    {
      keepPreviousData: true,
    },
  );

  const events = selectedProject?.settings?.events || {};

  // Max number of events depends on the plan
  const max_nb_events = orgMetadata?.plan === "pro" ? 100 : 10;
  const current_nb_events = Object.keys(events).length;
  const isDisabled = max_nb_events && current_nb_events >= max_nb_events;

  const eventToEdit = {
    project_id: project_id,
    org_id: selectedOrgId,
    event_name: cluster.name,
    description: cluster.description,
    score_range_settings: {
      min: 0,
      max: 1,
      score_type: "confidence",
    },
  } as EventDefinition;

  return (
    <Card
      key={cluster.id}
      className="rounded-lg shadow-md p-4 flex flex-col justify-between"
    >
      <HoverCard openDelay={0} closeDelay={0}>
        <div className="flex justify-between items-start space-x-2 mb-2">
          <h3 className="text-lg font-semibold text-center">{cluster.name}</h3>
          <HoverCardTrigger asChild>
            <div className="text-xl bg-primary text-secondary rounded-tr-lg px-3">
              {cluster.size}
            </div>
          </HoverCardTrigger>
        </div>
        <HoverCardContent className="text-secondary bg-primary text-xs">
          <p>Cluster size</p>
        </HoverCardContent>
      </HoverCard>
      <p className="text-sm text-muted-foreground mb-4">
        {cluster.description}
      </p>
      <div className="mt-auto pt-2 flex justify-end space-x-2">
        <Sheet
          open={sheetEventOpen}
          onOpenChange={setSheetEventOpen}
          key={cluster.id}
        >
          <SheetTrigger asChild>
            <Button disabled={isDisabled} size="sm" variant="outline">
              <PlusIcon className="size-4 mr-1" />
              Add tagger
            </Button>
          </SheetTrigger>
          <SheetContent className="md:w-1/2 overflow-auto">
            <CreateEvent
              setOpen={setSheetEventOpen}
              eventToEdit={eventToEdit}
            />
          </SheetContent>
        </Sheet>
        {cluster.size > 5 && (
          <Button
            className="pickaxe-button"
            variant="outline"
            size="sm"
            onClick={(mouseEvent) => {
              mouseEvent.stopPropagation();
              setSheetClusterOpen(true);
              setDataFilters({
                ...dataFilters,
                clustering_id: cluster.clustering_id,
                clusters_ids: [cluster.id],
              });
            }}
          >
            Break down
            <Pickaxe className="w-6 h-6 ml-1 pickaxe-animation" />
          </Button>
        )}
        <Button
          variant="secondary"
          size="sm"
          onClick={(mouseEvent) => {
            mouseEvent.stopPropagation();
            setDateRangePreset("all-time");
            router.push(
              `/org/insights/clusters/${encodeURIComponent(cluster.id)}`,
            );
          }}
        >
          Explore
          <ChevronRight className="w-4 h-4 ml-1" />
        </Button>
      </div>
    </Card>
  );
}

export function ClustersCards({
  setSheetClusterOpen: setSheetClusterOpen,
  selectedClustering: selectedClustering,
}: {
  setSheetClusterOpen: (value: boolean) => void;
  selectedClustering: Clustering | undefined;
}) {
  /* This is the group of all cluster cards */

  const { accessToken } = useUser();
  const project_id = navigationStateStore((state) => state.project_id);

  const {
    data: clustersData,
  }: {
    data: Cluster[] | null | undefined;
  } = useSWR(
    project_id
      ? [
          `/api/explore/${project_id}/clusters`,
          accessToken,
          project_id,
          // Refetch the data when the selected clustering changes
          // Ex: different selection, status update
          JSON.stringify(selectedClustering),
        ]
      : null,
    ([url, accessToken]) =>
      authFetcher(url, accessToken, "POST", {
        clustering_id: selectedClustering?.id,
        limit: 100,
      }).then((res) => {
        if (res === undefined) return undefined;
        return res?.clusters.sort((a: Cluster, b: Cluster) => b.size - a.size);
      }),
    {
      keepPreviousData: true,
    },
  );

  if (!project_id) {
    return <></>;
  }

  return (
    // We set this as custom-plot to align the width of plotly to the width of the cards
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 custom-plot min-w-full">
      {clustersData?.map((cluster) => {
        return (
          <ClusterCard
            key={cluster.id}
            cluster={cluster}
            setSheetClusterOpen={setSheetClusterOpen}
          />
        );
      })}
    </div>
  );
}
