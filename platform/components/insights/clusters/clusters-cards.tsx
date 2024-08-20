"use client";

import { TableNavigation } from "@/components/table-navigation";
import { Card } from "@/components/ui/card";
import {
    Select,
    SelectContent,
    SelectGroup,
    SelectItem,
    SelectTrigger,
} from "@/components/ui/select";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import { authFetcher } from "@/lib/fetcher";
import { formatUnixTimestampToLiteralDatetime } from "@/lib/time";
import { Cluster, Clustering } from "@/models/models";
import { navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import {
    ColumnFiltersState,
    SortingState,
    flexRender,
    getCoreRowModel,
    getFilteredRowModel,
    getPaginationRowModel,
    getSortedRowModel,
    useReactTable,
} from "@tanstack/react-table";
import { useRouter } from "next/navigation";
import React from "react";
import useSWR from "swr";

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

    if (!project_id) {
        return <></>;
    }

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {clustersData?.map((cluster) => (
                <Card
                    key={cluster.id}
                    className="rounded-lg shadow-md p-4 flex flex-col justify-between h-full"
                >
                    <h3 className="text-lg font-bold mb-4">{cluster.name}</h3>
                    <p className="text-sm text-muted-foreground">
                        {cluster.description}
                    </p>
                    <div className="flex justify-between items-center mt-4">
                        <div>
                            <span className="text-muted-foreground">Size:  </span>
                            <span className="text-lg">
                                {cluster.size}
                            </span>
                        </div>
                        <button
                            className="text-muted-foreground"
                            onClick={() => {
                                router.push(
                                    `/org/insights/clusters/${cluster.id}`
                                );
                            }}
                        >
                            View
                        </button>
                    </div>
                </Card>
            ))}
        </div>
    );
}
