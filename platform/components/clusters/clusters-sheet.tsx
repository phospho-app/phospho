import { Blockwall } from "@/components/blockwall";
import { DatePickerWithRange } from "@/components/date-range";
import FilterComponent from "@/components/filters";
import { Spinner } from "@/components/small-spinner";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { AlertDialog, AlertDialogTrigger } from "@/components/ui/alert-dialog";
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
  SelectValue,
} from "@/components/ui/select";
import {
  SheetContent,
  SheetDescription,
  SheetTitle,
} from "@/components/ui/sheet";
import { toast } from "@/components/ui/use-toast";
import { authFetcher } from "@/lib/fetcher";
import useDebounce from "@/lib/useDebounce";
import { Clustering, OrgMetadata } from "@/models/models";
import { navigationStateStore } from "@/store/store";
import { zodResolver } from "@hookform/resolvers/zod";
import { useUser } from "@propelauth/nextjs/client";
import { Separator } from "@radix-ui/react-dropdown-menu";
import { QuestionMarkIcon } from "@radix-ui/react-icons";
import { TestTubeDiagonal } from "lucide-react";
import React from "react";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import useSWR, { useSWRConfig } from "swr";
import * as z from "zod";

interface ProjectStatics {
  total_nb_tasks?: number;
  nb_tasks_in_sessions?: number;
  total_nb_sessions?: number;
  nb_sessions_in_scope?: number;
  nb_elements: number;
  clustering_cost: number;
  nb_users_messages?: number;
  total_nb_users?: number;
  nb_users_in_scope?: number;
}

const RunClusteringSheet = ({
  setSheetOpen,
  setSelectedClustering,
}: {
  setSheetOpen: (value: boolean) => void;
  setSelectedClustering: (value: Clustering) => void;
}) => {
  const project_id = navigationStateStore((state) => state.project_id);
  const selectedOrgId = navigationStateStore((state) => state.selectedOrgId);
  const dataFilters = navigationStateStore((state) => state.dataFilters);

  const { accessToken } = useUser();
  const { mutate } = useSWRConfig();

  const [loading, setLoading] = useState(false);

  const { data: orgMetadata }: { data: OrgMetadata } = useSWR(
    selectedOrgId
      ? [`/api/organizations/${selectedOrgId}/metadata`, accessToken]
      : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "GET"),
    {
      keepPreviousData: true,
    },
  );

  const hobby = orgMetadata?.plan === "hobby";

  const FormSchema = z.object({
    scope: z.enum(["messages", "sessions", "users"]),
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
      .max(128, "Number of clusters must be at most 128")
      .optional(),
    limit: z.number().min(0).optional(),
    detect_outliers: z.boolean(),
    output_format: z.enum([
      "title_description",
      "user_persona",
      "question_and_answer",
    ]),
  });

  const form = useForm<z.infer<typeof FormSchema>>({
    resolver: zodResolver(FormSchema),
    defaultValues: {
      scope: "messages",
      instruction: "user intent",
      detect_outliers: false,
      // Note: don't set the nb_clusters default value here, since it's updated dynamically using an API call
      nb_clusters: undefined,
      limit: undefined,
      output_format: "title_description",
    },
  });

  const limit = form.watch("limit");
  const scope = form.getValues("scope");

  const debouncedLimit = useDebounce(limit, 300);
  const {
    data: projectStatistics,
    isLoading: projectStatisticsLoading,
  }: { data: ProjectStatics | undefined; isLoading: boolean } = useSWR(
    project_id
      ? [
          `/api/explore/${project_id}/clustering-cost`,
          accessToken,
          JSON.stringify(dataFilters),
          form.watch("scope"),
          debouncedLimit,
        ]
      : null,
    ([url, accessToken]) =>
      authFetcher(url, accessToken, "POST", {
        scope: form.getValues("scope"),
        filters: dataFilters,
        limit: form.getValues("limit"),
      }),
    {
      keepPreviousData: true,
    },
  );

  const jsonDataFilters = JSON.stringify(dataFilters);
  const jsonProjectStatistics = JSON.stringify(projectStatistics);

  useEffect(() => {
    if (!projectStatistics) {
      return;
    }
    if (scope === "messages") {
      if (limit === undefined || limit === 0) {
        form.setValue("limit", projectStatistics.total_nb_tasks);
      }
    }
    if (scope === "sessions") {
      if (limit === undefined || limit === 0) {
        form.setValue("limit", projectStatistics.total_nb_sessions);
      }
    }
  }, [
    jsonProjectStatistics,
    form,
    limit,
    scope,
    jsonDataFilters,
    projectStatistics,
  ]);

  const canRunClusterAnalysis: boolean =
    (form.watch("scope") === "messages" &&
      !!projectStatistics?.nb_elements &&
      projectStatistics.nb_elements >= 5) ||
    (form.watch("scope") === "sessions" &&
      !!projectStatistics?.nb_sessions_in_scope &&
      projectStatistics.nb_sessions_in_scope >= 5) ||
    (form.watch("scope") === "users" &&
      !!projectStatistics?.nb_users_in_scope &&
      projectStatistics.nb_users_in_scope >= 5);
  // Defautl number of clusters is clamped between 3 and 12
  const defaultNbClusters = Math.min(
    12,
    Math.max(Math.round((projectStatistics?.nb_elements ?? 0) / 100), 3),
  );

  useEffect(() => {
    // Update the form default value for the number of clusters
    form.setValue("nb_clusters", defaultNbClusters);
  }, [defaultNbClusters, form]);

  function handleSkip() {
    setSheetOpen(false);
  }

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
          nb_clusters: formData.detect_outliers ? null : formData.nb_clusters,
          clustering_mode: formData.detect_outliers
            ? "dbscan"
            : "agglomerative",
          limit: formData.limit,
          output_format: formData.output_format,
        }),
      }).then(async (response) => {
        if (response.ok) {
          // The endpoint returns the new clustering
          const newClustering = (await response.json()) as Clustering;
          // Update the clusterings list
          mutate(
            project_id
              ? [`/api/explore/${project_id}/clusterings`, accessToken]
              : null,
            (data: { clusterings: Clustering[] } | undefined) => {
              const clusterings = data?.clusterings || [];
              return {
                clusterings: [newClustering, ...clusterings],
              };
            },
          ).then(() => {
            // Update the selected clustering
            setSelectedClustering(newClustering);
          });
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
    <SheetContent className="md:w-1/2 overflow-auto">
      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6 mt-2">
          <SheetTitle>Configure clusters detection</SheetTitle>
          <SheetDescription>
            Detect recurring topics, trends, and outliers using unsupervized
            machine learning.
          </SheetDescription>
          <Separator className="my-8" />
          <div className="flex flex-col flex-wrap gap-x-2 gap-y-2 items-start">
            <DatePickerWithRange />
            <FilterComponent variant={form.getValues("scope")} />
          </div>
          <div className="flex flex-col space-y-4">
            <FormField
              control={form.control}
              name="instruction"
              render={({ field }) => (
                <div className="flex flex-col space-y-2 bg-secondary p-2 rounded-lg">
                  <FormLabel>
                    <div className="flex space-x-2">
                      <span>Clustering instruction</span>
                      <HoverCard openDelay={0} closeDelay={0}>
                        <HoverCardTrigger>
                          <QuestionMarkIcon className="size-4 rounded-full bg-primary text-secondary p-0.5" />
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
                  <div className="flex items-center justify-start gap-x-1 gap-y-1 flex-wrap">
                    <h2 className="text-muted-foreground text-xs">
                      Templates:
                    </h2>
                    <Button
                      className="text-xs"
                      variant="outline"
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
                      className="text-xs"
                      variant="outline"
                      size="sm"
                      onClick={(mouseEvent) => {
                        mouseEvent.stopPropagation();
                        form.setValue("instruction", "assistant reply");
                        // Prevent the form from submitting
                        mouseEvent.preventDefault();
                      }}
                    >
                      assistant reply
                    </Button>
                    <Button
                      className="text-xs"
                      variant="outline"
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
                      className="text-xs"
                      variant="outline"
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
                      className="text-xs"
                      variant="outline"
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
                  <FormItem>
                    <FormControl>
                      <Input placeholder="user intent" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                  <FormField
                    control={form.control}
                    name="output_format"
                    render={({ field }) => (
                      <>
                        <FormLabel>
                          <div className="flex space-x-2 mt-2">
                            <span>Output format</span>
                          </div>
                        </FormLabel>
                        <Select
                          onValueChange={(value) => {
                            field.onChange(value);
                          }}
                          value={field.value} // Ensure this is controlled
                        >
                          <SelectTrigger className="max-w-[20rem]">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectGroup>
                              <SelectItem value="title_description">
                                Title and description
                              </SelectItem>
                              <SelectItem value="user_persona">
                                User persona
                              </SelectItem>
                              <SelectItem value="question_and_answer">
                                Question and answer
                              </SelectItem>
                            </SelectGroup>
                          </SelectContent>
                        </Select>
                      </>
                    )}
                  />
                </div>
              )}
            />
          </div>
          <Accordion type="single" collapsible className="w-full">
            <AccordionItem value="item-1">
              <AccordionTrigger>
                <div className="flex items-center text-sm">
                  <TestTubeDiagonal className="w-4 h-4 mr-2 text-green-500" />
                  More settings
                </div>
              </AccordionTrigger>
              <AccordionContent className="space-y-2">
                <div className="flex flex-col gap-y-2 bg-secondary p-2 rounded-lg">
                  <div className="flex flex-row gap-x-2 w-full items-end">
                    <FormField
                      control={form.control}
                      name="scope"
                      render={({ field }) => (
                        <FormItem className="w-full">
                          <FormLabel className="flex space-x-2">
                            <span>Granularity</span>
                            <HoverCard openDelay={0} closeDelay={0}>
                              <HoverCardTrigger>
                                <QuestionMarkIcon className="size-4 rounded-full bg-primary text-secondary p-0.5" />
                              </HoverCardTrigger>
                              <HoverCardContent>
                                <div className="w-96 flex flex-col space-y-2 p-2">
                                  <div>
                                    Clustering groups similar entities together.
                                    Pick the granularity of the entities to
                                    cluster.
                                  </div>
                                  <div className="flex flex-col space-y-1">
                                    <span>
                                      - User messages: a single interaction
                                    </span>
                                    <span>
                                      - User sessions: a whole discussion
                                    </span>
                                    <span>
                                      - Active users: multiple discussions from
                                      the same user
                                    </span>
                                  </div>
                                </div>
                              </HoverCardContent>
                            </HoverCard>
                          </FormLabel>
                          <Select
                            onValueChange={(value) => {
                              field.onChange(value);
                            }}
                            value={field.value} // Ensure this is controlled
                          >
                            <SelectTrigger className="max-w-[20rem]">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectGroup>
                                <SelectItem value="messages">
                                  User messages
                                </SelectItem>
                                <SelectItem value="sessions">
                                  User sessions
                                </SelectItem>
                                <SelectItem value="users">
                                  Active users
                                </SelectItem>
                              </SelectGroup>
                            </SelectContent>
                          </Select>
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="detect_outliers"
                      render={({ field }) => (
                        <FormItem className="w-full">
                          <FormLabel className="flex space-x-2">
                            Clustering mode
                          </FormLabel>
                          <Select
                            onValueChange={(value) => {
                              field.onChange(value === "true");
                            }}
                            defaultValue={field.value ? "true" : "false"}
                          >
                            <SelectTrigger className="max-w-[20rem]">
                              {field.value
                                ? "Detect outliers (beta)"
                                : "Uniform groups (default)"}
                            </SelectTrigger>
                            <SelectContent>
                              <SelectGroup>
                                <SelectItem value="false">
                                  Uniform groups (default)
                                </SelectItem>
                                <SelectItem value="true">
                                  Detect outliers (beta)
                                </SelectItem>
                              </SelectGroup>
                            </SelectContent>
                          </Select>
                        </FormItem>
                      )}
                    />
                  </div>

                  {!form.getValues("detect_outliers") && (
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
                                max={projectStatistics?.nb_elements ?? 0}
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
                  )}
                </div>
                <FormField
                  control={form.control}
                  name="limit"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>
                        Limit number of {form.getValues("scope")}
                      </FormLabel>
                      <FormControl>
                        <Input
                          className="w-32"
                          min={1}
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
              </AccordionContent>
            </AccordionItem>
          </Accordion>
          <div className="flex space-x-2 items-center pt-4">
            {projectStatisticsLoading && <Spinner />}
            {!canRunClusterAnalysis && (
              <span>
                You need at least 5 {form.getValues("scope")} to run a cluster
                analysis. There are currently{" "}
                {scope === "messages" && (projectStatistics?.nb_elements ?? 0)}
                {scope === "sessions" &&
                  (projectStatistics?.nb_sessions_in_scope ?? 0)}
                {scope === "users" &&
                  (projectStatistics?.nb_users_in_scope ?? 0)}{" "}
                {form.getValues("scope")}.
              </span>
            )}
            {canRunClusterAnalysis && (
              <span>
                We will cluster{" "}
                {<>{projectStatistics?.nb_elements ?? 0} user messages</>}
                {(form.getValues("scope") === "sessions" && (
                  <>
                    {" "}
                    ({projectStatistics?.nb_sessions_in_scope ??
                      0} sessions){" "}
                  </>
                )) ||
                  (form.getValues("scope") === "users" && (
                    <> ({projectStatistics?.nb_users_in_scope ?? 0} users) </>
                  ))}{" "}
                for a total of {projectStatistics?.clustering_cost} credits.{" "}
              </span>
            )}
          </div>
          {hobby && (
            <AlertDialog>
              <AlertDialogTrigger asChild>
                <Button> Run cluster analysis </Button>
              </AlertDialogTrigger>
              <Blockwall handleSkip={handleSkip} />
            </AlertDialog>
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
  );
};

export default RunClusteringSheet;
