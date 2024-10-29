"use client";

import { ClusteringLoading } from "@/components/clusters/clusters-loading";
import RunClusteringSheet from "@/components/clusters/clusters-sheet";
import { InteractiveDatetime } from "@/components/interactive-datetime";
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
  DropdownMenuLabel,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Sheet, SheetTrigger } from "@/components/ui/sheet";
import { authFetcher } from "@/lib/fetcher";
import { formatUnixTimestampToLiteralDatetime } from "@/lib/time";
import { Clustering } from "@/models/models";
import { navigationStateStore } from "@/store/store";
import { zodResolver } from "@hookform/resolvers/zod";
import { useUser } from "@propelauth/nextjs/client";
import { Boxes, Pencil, Plus, Settings } from "lucide-react";
import { useEffect, useState } from "react";
import * as React from "react";
import { useForm } from "react-hook-form";
import useSWR from "swr";
import * as z from "zod";

import { ClustersCards } from "./clusters-cards";
import { ClusteringDropDown } from "./clusters-drop-down";
import { CustomPlot } from "./clusters-plot";

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
  const [dropdownOpen, setDropdownOpen] = useState(false);

  const { data: clusteringsData } = useSWR(
    project_id
      ? [
          `/api/explore/${project_id}/clusterings`,
          accessToken,
          selectedClustering?.status,
        ]
      : null,
    ([url, accessToken]) =>
      authFetcher(url, accessToken, "POST").then((res) => {
        return res;
      }),
    {
      keepPreviousData: true,
    },
  );

  const FormSchema = z.object({
    clustering_name: z
      .string({
        required_error: "Please enter a clustering name",
      })
      .min(3, "Project name must be at least 3 characters long")
      .max(32, "Project name must be at most 32 characters long"),
  });

  const form = useForm<z.infer<typeof FormSchema>>({
    resolver: zodResolver(FormSchema),
    defaultValues: {
      clustering_name: selectedClustering?.name || "",
    },
  });

  useEffect(() => {
    if (selectedClustering) {
      form.reset({
        clustering_name: selectedClustering.name,
      });
    }
  }, [selectedClustering, form]);

  const onSubmit = async (data: z.infer<typeof FormSchema>) => {
    setDropdownOpen(false);
    console.log("new-name", data);
    if (project_id && selectedClustering) {
      try {
        const response = await fetch(`/api/clustering/${project_id}/rename`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${accessToken}`,
          },
          body: JSON.stringify({
            clustering_id: selectedClustering.id,
            new_name: data.clustering_name, // Changed from 'name' to 'new_name'
          }),
        });

        if (!response.ok) {
          throw new Error("Failed to rename clustering");
        }

        setSelectedClustering({
          ...selectedClustering,
          name: data.clustering_name,
        });

        // Handle successful rename (e.g., update local state or refetch data)
        // You might want to update the selectedClustering or trigger a refetch of clusterings
      } catch (error) {
        console.error("Error renaming clustering:", error);
        // Handle error (e.g., show an error message to the user)
      }
    }
  };

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

  const clusteringsJSON = JSON.stringify(clusterings);

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

  function toggleButton() {
    setDropdownOpen(!dropdownOpen);
  }

  return (
    <>
      <Sheet open={sheetClusterOpen} onOpenChange={setSheetClusterOpen}>
        <div className="flex flex-col gap-y-2">
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
          <div className="flex flex-row gap-x-2 items-center">
            <DropdownMenu open={dropdownOpen} onOpenChange={setDropdownOpen}>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size={"icon"} onClick={toggleButton}>
                  <Settings className="size-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent className="w-full">
                <DropdownMenuLabel className="flex flex-row items-center">
                  <Pencil className="w-4 h-4 mr-1" />
                  Rename clustering
                </DropdownMenuLabel>
                <div className="p-2">
                  <Form {...form}>
                    <form
                      onSubmit={form.handleSubmit(onSubmit)}
                      className="space-y-4"
                    >
                      <FormField
                        control={form.control}
                        name="clustering_name"
                        render={({ field }) => (
                          <FormItem>
                            <FormControl>
                              <Input maxLength={32} {...field} autoFocus />
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />
                      <Button
                        type="submit"
                        onClick={() => {
                          onSubmit(form.getValues());
                        }}
                        className="w-full"
                      >
                        Update
                      </Button>
                    </form>
                  </Form>
                </div>
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
            <div className="space-x-2 my-2">
              <Badge variant="secondary">
                {`Instruction: ${selectedClustering?.instruction}`}
              </Badge>
              <Badge variant="secondary">
                {selectedClustering?.nb_clusters ?? "No"} clusters
              </Badge>
              <Badge variant="secondary">
                <InteractiveDatetime
                  timestamp={selectedClustering.created_at}
                />
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
      </Sheet>
    </>
  );
};

export default Clusters;
