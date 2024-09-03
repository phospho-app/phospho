import { DatePickerWithRange } from "@/components/date-range";
import FilterComponent from "@/components/filters";
import { Spinner } from "@/components/small-spinner";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Button } from "@/components/ui/button";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import {
  HoverCard,
  HoverCardContent,
  HoverCardTrigger,
} from "@/components/ui/hover-card";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
} from "@/components/ui/select";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { toast } from "@/components/ui/use-toast";
import UpgradeButton from "@/components/upgrade-button";
import { authFetcher } from "@/lib/fetcher";
import { Clustering } from "@/models/models";
import { dataStateStore } from "@/store/store";
import { navigationStateStore } from "@/store/store";
import { zodResolver } from "@hookform/resolvers/zod";
import { useUser } from "@propelauth/nextjs/client";
import { Separator } from "@radix-ui/react-dropdown-menu";
import { QuestionMarkIcon } from "@radix-ui/react-icons";
import { ChevronRight, Sparkles, TestTubeDiagonal } from "lucide-react";
import React from "react";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import useSWR, { useSWRConfig } from "swr";
import * as z from "zod";

const RunClusters = ({
  sheetOpen,
  setSheetOpen,
  setSelectedClustering,
}: {
  sheetOpen: boolean;
  setSheetOpen: (value: boolean) => void;
  setSelectedClustering: (value: Clustering) => void;
}) => {
  const orgMetadata = dataStateStore((state) => state.selectedOrgMetadata);
  const project_id = navigationStateStore((state) => state.project_id);
  const dataFilters = navigationStateStore((state) => state.dataFilters);
  const setDataFilters = navigationStateStore((state) => state.setDataFilters);

  const { accessToken } = useUser();
  const { mutate } = useSWRConfig();

  const [clusteringCost, setClusteringCost] = useState(0);
  const [nbElements, setNbElements] = useState(0);
  const [loading, setLoading] = useState(false);
  const [update, setUpdate] = useState(false);

  let defaultNbClusters = 0;

  const { data: totalNbTasksData } = useSWR(
    [
      `/api/explore/${project_id}/aggregated/tasks`,
      accessToken,
      JSON.stringify(dataFilters),
      "total_nb_tasks",
    ],
    ([url, accessToken]) =>
      authFetcher(url, accessToken, "POST", {
        metrics: ["total_nb_tasks"],
        filters: { ...dataFilters },
      }),
    {
      keepPreviousData: true,
    },
  );
  let totalNbTasks: number | null | undefined =
    totalNbTasksData?.total_nb_tasks;

  const { data: totalNbSessionsData } = useSWR(
    [
      `/api/explore/${project_id}/aggregated/sessions`,
      accessToken,
      JSON.stringify(dataFilters),
      "total_nb_sessions",
    ],
    ([url, accessToken]) =>
      authFetcher(url, accessToken, "POST", {
        metrics: ["total_nb_sessions"],
        filters: { ...dataFilters },
      }),
    {
      keepPreviousData: true,
    },
  );
  let totalNbSessions: number | null | undefined =
    totalNbSessionsData?.total_nb_sessions;

  const hobby = orgMetadata?.plan === "hobby";

  function setSheetOpenWrapper(value: boolean) {
    // Reset the dataFilters when the sheet is closed
    if (!value) {
      const currentDataFilters = dataFilters;
      delete currentDataFilters.clustering_id;
      delete currentDataFilters.clusters_ids;
      setDataFilters(dataFilters);
    }
    setSheetOpen(value);
  }

  const FormSchema = z.object({
    scope: z.enum(["messages", "sessions"]),
    instruction: z
      .string({
        required_error: "Please enter an instruction",
      })
      .max(64, "Instruction must be at most 64 characters long"),
    nb_clusters: z
      .number({
        required_error: "Please enter the number of clusters",
      })
      .min(1, "Number of clusters must be at least 1")
      .max(128, "Number of clusters must be at most 128"),
  });

  const form = useForm<z.infer<typeof FormSchema>>({
    resolver: zodResolver(FormSchema),
    defaultValues: {
      scope: "messages",
      instruction: "user intent",
      // Note: don't set the nb_clusters default value here, since it's updated dynamically using an API call
    },
  });

  useEffect(() => {
    // Update the default number of clusters when the total number of tasks changes
    if (totalNbTasks) {
      setClusteringCost(totalNbTasks * 2);
    }
    if (form.getValues("scope") === "messages") {
      if (totalNbTasks === null || totalNbTasks === undefined) {
        totalNbTasks = 0;
      }
      setNbElements(totalNbTasks);
      defaultNbClusters = Math.floor(totalNbTasks / 100);

      if (defaultNbClusters >= 5) {
        form.setValue("nb_clusters", defaultNbClusters);
      } else {
        form.setValue("nb_clusters", 5);
      }
    }
    if (form.getValues("scope") === "sessions") {
      if (totalNbSessions === null || totalNbSessions === undefined) {
        totalNbSessions = 0;
      }
      setNbElements(totalNbSessions);
      defaultNbClusters = Math.floor(totalNbSessions / 100);
      if (defaultNbClusters >= 5) {
        form.setValue("nb_clusters", Math.floor(defaultNbClusters));
      } else {
        form.setValue("nb_clusters", 5);
      }
    }
  }, [totalNbSessions, totalNbTasks, update]);

  const canRunClusterAnalysis: boolean =
    (form.getValues("scope") === "messages" &&
      !!totalNbTasks &&
      totalNbTasks >= 5) ||
    (form.getValues("scope") === "sessions" &&
      !!totalNbSessions &&
      totalNbSessions >= 5);

  async function onSubmit(formData: z.infer<typeof FormSchema>) {
    setLoading(true);
    try {
      await fetch(`/api/explore/${project_id}/detect-clusters`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: "Bearer " + accessToken,
        },
        body: JSON.stringify({
          filters: dataFilters,
          scope: formData.scope,
          instruction: formData.instruction,
          nb_clusters: formData.nb_clusters,
        }),
      }).then(async (response) => {
        if (response.ok) {
          // The endpoint returns the new clustering
          const newClustering = (await response.json()) as Clustering;
          // Update the clusterings list
          mutate(
            project_id
              ? [
                  `/api/explore/${project_id}/clusterings`,
                  accessToken,
                  "cluster-cards",
                ]
              : null,
            (data: any) => {
              const clusterings = data?.clusterings || [];
              return {
                clusterings: [newClustering, ...clusterings],
              };
            },
          );
          // Update the selected clustering
          setSelectedClustering(newClustering);
          toast({
            title: `Cluster detection ${newClustering.name} started ⏳`,
            description: "This may take a few minutes.",
          });
          setSheetOpen(false);
        } else {
          toast({
            title: "Error when starting detection",
            description: response.text(),
          });
        }
        setLoading(false);
      });
    } catch (e) {
      toast({
        title: "Error when starting detection",
        description: JSON.stringify(e),
      });
      setLoading(false);
    }
  }

  if (!project_id) {
    return <></>;
  }

  return (
    <Sheet open={sheetOpen} onOpenChange={setSheetOpenWrapper}>
      <SheetTrigger>
        <Button className="default">
          <Sparkles className="w-4 h-4 mr-2 text-green-500" /> Configure
          clusters detection
          <ChevronRight className="w-4 h-4 ml-2" />
        </Button>
      </SheetTrigger>
      <SheetContent className="md:w-1/2 overflow-auto">
        <Form {...form}>
          <form
            onSubmit={form.handleSubmit(onSubmit)}
            className="space-y-6 mt-2"
          >
            <SheetTitle>Configure clusters detection</SheetTitle>
            <SheetDescription>
              Run a cluster analysis on your user sessions to detect patterns
              and group similar messages together.
            </SheetDescription>
            <Separator className="my-8" />
            <div className="flex flex-wrap space-x-2 space-y-2 items-end">
              <DatePickerWithRange />
              <FormField
                control={form.control}
                name="scope"
                render={({ field }) => (
                  <Select
                    onValueChange={(value) => {
                      field.onChange(value);
                      setUpdate(!update);
                    }}
                    defaultValue={field.value}
                  >
                    <SelectTrigger className="max-w-[20rem]">
                      {field.value === "messages" ? "Messages" : "Sessions"}
                    </SelectTrigger>
                    <SelectContent>
                      <SelectGroup>
                        <SelectItem value="messages">Messages</SelectItem>
                        <SelectItem value="sessions">Sessions</SelectItem>
                      </SelectGroup>
                    </SelectContent>
                  </Select>
                )}
              />

              <FilterComponent variant="tasks" />
            </div>
            <Accordion type="single" collapsible className="w-full">
              <AccordionItem value="item-1">
                <AccordionTrigger>
                  <div className="flex items-center">
                    <TestTubeDiagonal className="w-4 h-4 mr-2 text-green-500" />
                    More settings
                  </div>
                </AccordionTrigger>
                <AccordionContent className="space-y-3 space-x-1">
                  <FormLabel>
                    <div className="flex space-x-2">
                      <span>Clustering instruction</span>
                      <HoverCard openDelay={0} closeDelay={0}>
                        <HoverCardTrigger>
                          <QuestionMarkIcon className="h-4 w-4 rounded-full bg-primary text-secondary p-0.5" />
                        </HoverCardTrigger>
                        <HoverCardContent>
                          <div className="w-96">
                            The clustering instruction refines how{" "}
                            {form.getValues("scope")} are grouped. Enter the
                            topic to focus on.
                          </div>
                        </HoverCardContent>
                      </HoverCard>
                    </div>
                  </FormLabel>
                  <FormField
                    control={form.control}
                    name="instruction"
                    render={({ field }) => (
                      <FormItem className="flex-grow">
                        <FormControl>
                          <Input placeholder="user intent" {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <div>
                    <h2 className="text-muted-foreground text-xs mb-1">
                      Templates
                    </h2>
                    <div className="flex space-x-4">
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={(mouseEvent) => {
                          mouseEvent.stopPropagation();
                          form.setValue("instruction", "user intent");
                          // Prevent the form from submitting
                          mouseEvent.preventDefault();
                        }}
                      >
                        user intent
                      </Button>
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={(mouseEvent) => {
                          mouseEvent.stopPropagation();
                          form.setValue(
                            "instruction",
                            "type of issue (refund, delivery, etc.)",
                          );
                          // Prevent the form from submitting
                          mouseEvent.preventDefault();
                        }}
                      >
                        support
                      </Button>
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={(mouseEvent) => {
                          mouseEvent.stopPropagation();
                          form.setValue("instruction", "type of disease");
                          // Prevent the form from submitting
                          mouseEvent.preventDefault();
                        }}
                      >
                        medical chatbot
                      </Button>
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={(mouseEvent) => {
                          mouseEvent.stopPropagation();
                          form.setValue("instruction", "product mentioned");
                          // Prevent the form from submitting
                          mouseEvent.preventDefault();
                        }}
                      >
                        sales assistant
                      </Button>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <FormLabel>Number of clusters:</FormLabel>
                    <FormField
                      control={form.control}
                      name="nb_clusters"
                      render={({ field }) => (
                        <FormItem className="flex-grow">
                          <FormControl>
                            <Input
                              className="w-32"
                              max={nbElements}
                              min={0}
                              step={1}
                              type="number"
                              {...field}
                              onChange={(e) => {
                                field.onChange(e.target.valueAsNumber);
                              }}
                            />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </div>
                </AccordionContent>
              </AccordionItem>
            </Accordion>
            {!canRunClusterAnalysis && (
              <div className="mt-4">
                You need at least 5 {form.getValues("scope")} to run a cluster
                analysis. There are currently {nbElements}{" "}
                {form.getValues("scope")}.
              </div>
            )}
            {canRunClusterAnalysis && (
              <div className="mt-4">
                We will clusterize {nbElements} {form.getValues("scope")}{" "}
                {form.getValues("scope") === "sessions" && (
                  <>containing {totalNbTasks} messages</>
                )}{" "}
                for a total of {clusteringCost} credits.{" "}
              </div>
            )}
            {hobby && (
              <div className="flex justify-end mt-4">
                <UpgradeButton tagline="Run cluster analysis" green={false} />
              </div>
            )}
            {!hobby && canRunClusterAnalysis && (
              <div className="flex justify-end mt-4">
                <Button type="submit" disabled={loading}>
                  {loading && <Spinner className="mr-2" />}
                  Run cluster analysis
                </Button>
              </div>
            )}
          </form>
        </Form>
      </SheetContent>
    </Sheet>
  );
};

export default RunClusters;
