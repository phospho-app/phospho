import { DatePickerWithRange } from "@/components/date-range";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
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
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { authFetcher } from "@/lib/fetcher";
import { OrgMetadata, Project } from "@/models/models";
import { navigationStateStore } from "@/store/store";
import { zodResolver } from "@hookform/resolvers/zod";
import { useUser } from "@propelauth/nextjs/client";
import { Separator } from "@radix-ui/react-dropdown-menu";
import { QuestionMarkIcon } from "@radix-ui/react-icons";
import { ChevronRight, PlayIcon, Sparkles } from "lucide-react";
import { useRouter } from "next/navigation";
import React from "react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import useSWR from "swr";
import { z } from "zod";

import FilterComponent from "./filters";
import { Spinner } from "./small-spinner";
import { toast } from "./ui/use-toast";
import UpgradeButton from "./upgrade-button";

const FormSchema = z.object({
  recipe_type_list: z.array(z.string()),
});

const RunAnalysisInPast = () => {
  const router = useRouter();
  const { accessToken } = useUser();
  const selectedOrgId = navigationStateStore((state) => state.selectedOrgId);
  const [checkedEvent, setCheckedEvent] = useState(true);
  const [checkedLangSent, setCheckedLangSent] = useState(true);
  const [totalAnalytics, setTotalAnalytics] = useState(0);

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

  const [loading, setLoading] = React.useState(false);
  const dataFilters = navigationStateStore((state) => state.dataFilters);

  const project_id = navigationStateStore((state) => state.project_id);
  const { data: selectedProject }: { data: Project } = useSWR(
    project_id ? [`/api/projects/${project_id}`, accessToken] : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "GET"),
    {
      keepPreviousData: true,
    },
  );
  const eventList: string[] = Object.keys(
    selectedProject?.settings?.events || {},
  );
  const formatedEventList = eventList.join(", ");
  const nbrEvents = eventList.length;

  const { data: totalNbTasks }: { data: number | null } = useSWR(
    [
      `/api/explore/${project_id}/aggregated/tasks`,
      accessToken,
      JSON.stringify(dataFilters),
      "total_nb_tasks",
    ],
    ([url, accessToken]) =>
      authFetcher(url, accessToken, "POST", {
        metrics: ["total_nb_tasks"],
        filters: dataFilters,
      }).then((res) => {
        if (res === undefined) return undefined;
        if (!res?.total_nb_tasks) return null;
        return res?.total_nb_tasks;
      }),
    {
      keepPreviousData: true,
    },
  );

  React.useEffect(() => {
    if (totalNbTasks) {
      setTotalAnalytics(
        ((checkedEvent ? nbrEvents : 0) + (checkedLangSent ? 2 : 0)) *
          totalNbTasks,
      );
    } else {
      setTotalAnalytics(0);
    }
  }, [checkedEvent, checkedLangSent, nbrEvents, totalNbTasks]);

  const form_choices = [
    {
      id: "event_detection",
      label: "Analytics",
      description:
        "Detect if the setup analytics are present: " +
        formatedEventList +
        ". " +
        nbrEvents +
        " credits per user message, one per analytic.",
    },
    {
      id: "sentiment_language",
      label: "Sentiment & language",
      description:
        "Recognize the sentiment (positive, negative) and the language of the user message. 2 credits per user message.",
    },
  ] as const;

  const form = useForm<z.infer<typeof FormSchema>>({
    resolver: zodResolver(FormSchema),
    defaultValues: {
      recipe_type_list: ["event_detection", "sentiment_language"],
    },
  });

  async function onSubmit(data: z.infer<typeof FormSchema>) {
    setLoading(true);
    // call the API endpoint
    const response = await fetch(`/api/recipes/${project_id}/run`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${accessToken}`,
      },
      body: JSON.stringify({
        recipe_type_list: data.recipe_type_list,
        filters: dataFilters,
      }),
    });

    // Redirect to the home page
    router.push("/");

    if (!response.ok) {
      toast({
        title: "Something went wrong",
        description: `Details: ${await response.text()}`,
      });
      return;
    }

    toast({
      title: "Your analytics are running 🚀",
      description:
        "This may take a few minutes. Feel free to reach out - we're here to help.",
    });
  }

  return (
    <Sheet>
      <SheetTrigger asChild>
        <Button variant={"outline"}>
          <Sparkles className="text-green-500 size-4 mr-2" />
          Detect
          <ChevronRight className="size-4 ml-2" />
        </Button>
      </SheetTrigger>
      <SheetContent className="md:w-1/2 overflow-auto">
        <SheetTitle>Run analysis on past data</SheetTitle>
        <SheetDescription>
          Run analytics, language, and sentiment labels.
        </SheetDescription>
        <Separator className="my-8" />
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-8">
            <FormField
              control={form.control}
              name="recipe_type_list"
              render={() => (
                <FormItem>
                  <div className="mb-8">
                    <FormLabel className="text-base">
                      Select analytics to run on the data of the project &apos;
                      {selectedProject?.project_name}&apos;
                    </FormLabel>
                  </div>
                  <div className="flex flex-wrap space-x-2">
                    <DatePickerWithRange />
                    <FilterComponent variant="tasks" />
                  </div>
                  {form_choices.map((item) => (
                    <FormField
                      key={item.id}
                      control={form.control}
                      name="recipe_type_list"
                      render={({ field }) => {
                        return (
                          <FormItem
                            key={item.id}
                            className="flex flex-row items-center space-x-3 space-y-4 py-1"
                          >
                            <FormControl>
                              <Checkbox
                                checked={field.value?.includes(item.id)}
                                className="mt-4"
                                onCheckedChange={(checked) => {
                                  if (checked) {
                                    field.onChange([...field.value, item.id]);
                                    if (item.id === "event_detection") {
                                      setCheckedEvent(true);
                                    }
                                    if (item.id === "sentiment_language") {
                                      setCheckedLangSent(true);
                                    }
                                  } else {
                                    field.onChange(
                                      field.value?.filter(
                                        (value) => value !== item.id,
                                      ),
                                    );
                                    if (item.id === "event_detection") {
                                      setCheckedEvent(false);
                                    }
                                    if (item.id === "sentiment_language") {
                                      setCheckedLangSent(false);
                                    }
                                  }
                                }}
                              />
                            </FormControl>
                            <FormLabel className="font-normal">
                              <HoverCard openDelay={0} closeDelay={0}>
                                <div className="flex flex-row space-x-2">
                                  <span>{item.label}</span>
                                  <HoverCardTrigger>
                                    <QuestionMarkIcon className="rounded-full bg-primary text-secondary p-0.5" />
                                  </HoverCardTrigger>
                                </div>
                                <HoverCardContent side="right" className="w-96">
                                  <div className="p-1 flex flex-col space-y-1 ">
                                    <div className="font-bold">
                                      {item.label}
                                    </div>
                                    <div className="text-muted-foreground text-xs">
                                      {item.description}
                                    </div>
                                  </div>
                                </HoverCardContent>
                              </HoverCard>
                            </FormLabel>
                          </FormItem>
                        );
                      }}
                    />
                  ))}
                  <FormMessage />
                </FormItem>
              )}
            />
            {totalNbTasks && (
              <div>
                We will run {totalAnalytics} analytics, on {totalNbTasks}{" "}
                messages, for a total of {totalAnalytics} credits.
              </div>
            )}
            {hobby && (
              <div className="flex justify-end">
                <UpgradeButton tagline="Run now" green={false} />
              </div>
            )}
            {!hobby && totalNbTasks && totalNbTasks > 0 && (
              <div className="flex justify-end">
                <Button
                  type="submit"
                  disabled={
                    form.formState.isSubmitted || form.formState.isSubmitting
                  }
                >
                  {loading && <Spinner className="mr-2" />}
                  {!loading && (
                    <PlayIcon className="size-4 mr-2 text-green-500" />
                  )}
                  Run now
                </Button>
              </div>
            )}
            {!totalNbTasks && (
              <div>
                <div>No messages selected</div>
              </div>
            )}
          </form>
        </Form>
      </SheetContent>
    </Sheet>
  );
};

export default RunAnalysisInPast;
