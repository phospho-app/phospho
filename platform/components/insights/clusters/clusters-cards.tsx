"use client";

import { Card } from "@/components/ui/card";
import { authFetcher } from "@/lib/fetcher";
import { Cluster, Clustering } from "@/models/models";
import { navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import {
    ColumnFiltersState,
    SortingState,
} from "@tanstack/react-table";
import { useRouter } from "next/navigation";
import React from "react";
import useSWR from "swr";
import { ChevronRight, Pickaxe } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
    HoverCard,
    HoverCardContent,
    HoverCardTrigger,
} from "@/components/ui/hover-card";
import Link from "next/link";
import "./style.css"

export function ClustersCards({
    clusterings = [],
    setSheetOpen,
}: { clusterings?: Clustering[]; setSheetOpen: (value: boolean) => void; }) {
    const project_id = navigationStateStore((state) => state.project_id);
    const { accessToken } = useUser();

    const [sorting, setSorting] = React.useState<SortingState>([]);
    const [filters, setFilters] = React.useState<ColumnFiltersState>([]);
    const router = useRouter();

    let latestClustering = undefined;
    if (clusterings.length > 0) {
        console.log("clusterings", clusterings);
        latestClustering = clusterings[0];
    }

    const [selectedClustering, setSelectedClustering] = React.useState<
        Clustering | undefined
    >(latestClustering);

    const {
        data: clustersData,
    }: {
        data: Cluster[] | null | undefined;
    } = useSWR(
        project_id
            ? [
                `/api/explore/${project_id}/clusters`,
                accessToken,
                selectedClustering?.id,
            ]
            : null,
        ([url, accessToken]) =>
            authFetcher(url, accessToken, "POST", {
                clustering_id: selectedClustering?.id,
                limit: 100,
            }).then((res) =>
                res?.clusters.sort((a: Cluster, b: Cluster) => b.size - a.size),
            ),
        {
            keepPreviousData: true,
        },
    );

    const dataFilters = navigationStateStore((state) => state.dataFilters);
    const setDataFilters = navigationStateStore(
        (state) => state.setDataFilters,
    );

    if (!project_id) {
        return <></>;
    }

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {clustersData?.map((cluster) => (

                <Card key={cluster.id} className="rounded-lg shadow-md p-4 flex flex-col justify-between h-full">
                    <HoverCard openDelay={0} closeDelay={0}>
                        <div className="flex justify-between items-start space-x-2 mb-2">
                            <h3 className="text-lg font-semibold">{cluster.name}</h3>
                            <HoverCardTrigger asChild>
                                <div className="text-xl bg-primary text-secondary rounded-tr-lg px-3">{cluster.size}</div>
                            </HoverCardTrigger>
                        </div>
                        <HoverCardContent className="text-secondary bg-primary text-xs">
                            <p>Cluster size</p>
                        </HoverCardContent>
                    </HoverCard>
                    <p className="text-sm text-muted-foreground mb-4">{cluster.description}</p>
                    <div className="mt-auto pt-2 flex justify-end space-x-2">
                        {cluster.size > 5 && (
                            <Button
                                className="pickaxe-button"
                                variant="outline"
                                size="sm"
                                onClick={(mouseEvent) => {
                                    mouseEvent.stopPropagation();
                                    setSheetOpen(true);
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
                        <Link href={`/org/insights/clusters/${encodeURIComponent(cluster.id)}`}>
                            <Button
                                variant="secondary"
                                size="sm"
                            >
                                Explore
                                <ChevronRight className="w-4 h-4 ml-1" />
                            </Button>
                        </Link>
                    </div>
                </Card>
            ))
            }
        </div >
    );
}
