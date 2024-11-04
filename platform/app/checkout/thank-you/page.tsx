"use client";

import { CenteredSpinner } from "@/components/small-spinner";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
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
import { toast } from "@/components/ui/use-toast";
import { authFetcher } from "@/lib/fetcher";
import { Project } from "@/models/models";
import { navigationStateStore } from "@/store/store";
import { zodResolver } from "@hookform/resolvers/zod";
import { useUser } from "@propelauth/nextjs/client";
import { QuestionMarkIcon } from "@radix-ui/react-icons";
import { PlayIcon } from "lucide-react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import React, { useState } from "react";
import { useForm } from "react-hook-form";
import useSWR from "swr";
import { z } from "zod";

const FormSchema = z.object({
  recipe_type_list: z.array(z.string()),
});

function RunAnalyticsForm({
  selectedProject,
  totalNbTasks,
}: {
  selectedProject: Project;
  totalNbTasks: number | null | undefined;
}) {
  const router = useRouter();
  const { accessToken } = useUser();
  const [checkedEvent, setCheckedEvent] = useState(true);
  const [checkedLangSent, setCheckedLangSent] = useState(true);
  const [totalAnalytics, setTotalAnalytics] = useState(0);

  // Create a list from the keys of the selectedProject.settings.event mapping {event_name: event}
  // The list should be comma separated
  const eventList: string[] = Object.keys(
    selectedProject?.settings?.events || {},
  );
  const formatedEventList = eventList.join(", ");
  const nbrEvents = eventList.length;

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
      label: "Event detection",
      description:
        "Detect if the setup events are present: " +
        formatedEventList +
        ". " +
        nbrEvents +
        " credits per user message, one per event.",
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
    // call the API endpoint
    const response = await fetch(`/api/recipes/${selectedProject.id}/run`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${accessToken}`,
      },
      body: JSON.stringify({
        recipe_type_list: data.recipe_type_list,
      }),
    });

    // Redirect to the home page
    router.push("/");

    if (!response.ok) {
      toast({
        title: "Something went wrong",
        description: `Details ${await response.text()}`,
      });
      return;
    }

    toast({
      title: "Your analytics are running 🚀",
      description:
        "This may take a few minutes. Feel free to reach out - we&apos;re here to help.",
    });
  }

  return (
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
              {form_choices.map((item) => (
                <FormField
                  key={item.id}
                  control={form.control}
                  name="recipe_type_list"
                  render={({ field }) => {
                    return (
                      <FormItem
                        key={item.id}
                        className="flex flex-row items-center space-x-3 space-y-0 py-1"
                      >
                        <FormControl>
                          <Checkbox
                            checked={field.value?.includes(item.id)}
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
                            <HoverCardTrigger>
                              <div className="flex flex-row space-x-2">
                                <span>{item.label}</span>
                                <QuestionMarkIcon className="rounded-full bg-primary text-secondary p-0.5" />
                              </div>
                            </HoverCardTrigger>
                            <HoverCardContent side="right" className="w-96">
                              <div className="p-1 flex flex-col space-y-1">
                                <div className="font-bold">{item.label}</div>
                                <div>{item.description}</div>
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
            We will run {totalAnalytics} analytics, on {totalNbTasks} tasks, for
            a total of {totalAnalytics} credits.
          </div>
        )}
        <div className="flex justify-between">
          <HoverCard openDelay={0} closeDelay={0}>
            <HoverCardTrigger asChild>
              <Link href="/">
                <Button variant="link" className="px-0">
                  Later
                </Button>
              </Link>
            </HoverCardTrigger>
            <HoverCardContent side="bottom">
              <div className="text-xs">You can run this later</div>
            </HoverCardContent>
          </HoverCard>
          <Button type="submit" disabled={form.formState.isSubmitted}>
            <PlayIcon className="size-4 mr-2 text-green-500" />
            Run now
          </Button>
        </div>
      </form>
    </Form>
  );
}

export default function Page() {
  // This is a Thank you page displayed after a successful checkout

  const router = useRouter();
  const searchParams = useSearchParams();

  // Get the project_id from the URL, or from the navigation state
  const project_id_in_url = searchParams.get("project_id");
  const decoded_project_id_in_url = project_id_in_url
    ? decodeURIComponent(project_id_in_url)
    : null;
  const project_id =
    navigationStateStore((state) => state.project_id) ??
    decoded_project_id_in_url;

  const { accessToken } = useUser();

  const { data: selectedProject } = useSWR(
    [`/api/projects/${project_id}`, accessToken],
    ([url, accessToken]) =>
      authFetcher(url, accessToken, "GET").then((data) => {
        // if data?.detail is not null, it means the project was not found
        if (data?.detail) {
          return null;
        }
        return data;
      }),
    {
      keepPreviousData: true,
    },
  );

  const { data: hasTasksData } = useSWR(
    project_id ? [`/api/explore/${project_id}/has-tasks`, accessToken] : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "POST"),
    { keepPreviousData: true },
  );
  const hasTasks: boolean = hasTasksData?.has_tasks;

  const { data: totalNbTasksData } = useSWR(
    project_id
      ? [
          `/api/explore/${project_id}/aggregated/tasks`,
          accessToken,
          "total_nb_tasks",
        ]
      : null,
    ([url, accessToken]) =>
      authFetcher(url, accessToken, "POST", {
        metrics: ["total_nb_tasks"],
      }),
    {
      keepPreviousData: true,
    },
  );
  const totalNbTasks: number | null | undefined =
    totalNbTasksData?.total_nb_tasks;

  function onBoogieClick() {
    toast({
      title: "We are activating your account 🚀",
      description:
        "You should see changes in a few minutes max. If not, please refresh the page. Contact us if anything - we're here to help.",
    });
    router.push("/");
  }

  return (
    <>
      {selectedProject === undefined && <CenteredSpinner />}
      {(hasTasks === false || selectedProject === null) && (
        <Card className={"container w-96"}>
          <CardHeader>
            <CardTitle className="font-bold">Welcome to phospho.</CardTitle>
            <CardDescription className="text-xl">
              Thank you for joining the community.
            </CardDescription>
          </CardHeader>
          <CardContent className="flex justify-center">
            <p>We can&apos;t wait to see what you&apos;ll build.</p>
          </CardContent>
          <CardFooter className="flex justify-center">
            <Button className="bg-green-500" onClick={onBoogieClick}>
              Let&apos;s boogie.
            </Button>
          </CardFooter>
        </Card>
      )}
      {hasTasks && (
        <Card className={"container w-96"}>
          <CardHeader>
            <CardTitle className="py-2">
              <div className="font-bold">Welcome to phospho.</div>
            </CardTitle>
            <CardDescription className="text-sm flex flex-col space-y-2">
              <RunAnalyticsForm
                selectedProject={selectedProject}
                totalNbTasks={totalNbTasks}
              />
            </CardDescription>
          </CardHeader>
        </Card>
      )}
    </>
  );
}
