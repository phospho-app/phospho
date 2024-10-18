"use client";

import { DatePickerWithRange } from "@/components/date-range";
import FilterComponent from "@/components/filters";
import { Spinner } from "@/components/small-spinner";
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
import { Separator } from "@/components/ui/separator";
import {
  SheetDescription,
  SheetFooter,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { useToast } from "@/components/ui/use-toast";
import { authFetcher } from "@/lib/fetcher";
import { EventDefinition, Project } from "@/models/models";
import { navigationStateStore } from "@/store/store";
import { zodResolver } from "@hookform/resolvers/zod";
import { useUser } from "@propelauth/nextjs/client";
import { QuestionMarkIcon } from "@radix-ui/react-icons";
import Link from "next/link";
import { useState } from "react";
import { useForm } from "react-hook-form";
import useSWR from "swr";
import { z } from "zod";

export default function RunEvent({
  setOpen,
  eventToRun,
}: {
  setOpen: (open: boolean) => void;
  eventToRun: EventDefinition;
}) {
  // This is a form that lets you run an event detection on previous data
  // Component to create an event or edit an existing event

  const project_id = navigationStateStore((state) => state.project_id);
  const { loading, accessToken } = useUser();
  const { toast } = useToast();
  const dataFilters = navigationStateStore((state) => state.dataFilters);
  const [startrunLoading, setStartrunLoading] = useState(false);

  const { data: hasTasksData } = useSWR(
    project_id ? [`/api/explore/${project_id}/has-tasks`, accessToken] : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "POST"),
    { keepPreviousData: true },
  );
  const hasTasks: boolean = hasTasksData?.has_tasks ?? false;
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
        if (!res) return 0;
        return res?.total_nb_tasks;
      }),
    {
      keepPreviousData: true,
    },
  );

  const formSchema = z.object({
    sample_rate: z.coerce.number().min(0).max(1),
  });

  const { data: selectedProject }: { data: Project } = useSWR(
    project_id ? [`/api/projects/${project_id}`, accessToken] : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "GET"),
    {
      keepPreviousData: true,
    },
  );
  const eventDetectionEnabled =
    selectedProject.settings?.run_event_detection ?? false;

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      sample_rate: 1,
    },
  });

  const sampleSize = Math.floor(
    (totalNbTasks ?? 0) * form.watch("sample_rate"),
  );

  async function onSubmit(values: z.infer<typeof formSchema>) {
    console.log("Running event detection on", sampleSize, "tasks");
    setStartrunLoading(true);
    try {
      fetch(`/api/events/${project_id}/run`, {
        method: "POST",
        headers: {
          Authorization: "Bearer " + accessToken,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          event_id: eventToRun.id,
          sample_rate: values.sample_rate,
          filters: dataFilters,
        }),
      }).then(async (res) => {
        setStartrunLoading(false);
        if (res.ok) {
          toast({
            title: `Event detection for "${eventToRun.event_name}" started.`,
            description: `Running on ${sampleSize} tasks`,
          });
          setOpen(false);
        } else {
          toast({
            title: "Error starting event detection",
            description: await res.text(),
          });
        }
      });
    } catch (error) {
      toast({
        title: "Error starting event detection",
        description: `${error}`,
      });
      setStartrunLoading(false);
    }
  }

  return (
    <>
      <Form {...form}>
        <form
          onSubmit={form.handleSubmit(onSubmit)}
          className="font-normal space-y-4"
          key={`createEventForm_${eventToRun.id}`}
        >
          <SheetHeader>
            <SheetTitle className="text-xl">
              Detect event &quot;{eventToRun.event_name}&quot; on past data
            </SheetTitle>
            <SheetDescription>
              Detect if this event happened on a sample of previously logged
              data.
            </SheetDescription>
          </SheetHeader>
          <Separator />
          <div className="flex-col space-y-4">
            <div className="flex space-x-2">
              <DatePickerWithRange />
              <FilterComponent variant="tasks" />
            </div>
            <FormField
              control={form.control}
              name="sample_rate"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Sample rate</FormLabel>
                  <FormControl>
                    <Input
                      className="w-32"
                      placeholder="0.0 - 1.0"
                      min={0}
                      max={1}
                      step={0.01}
                      type="number"
                      {...field}
                      onChange={(e) => {
                        field.onChange(parseFloat(e.target.value));
                      }}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            {hasTasks && totalNbTasks === undefined && <>Loading...</>}
            {!hasTasks && (
              <div className="flex flex-row space-x-1 items-center">
                <span>
                  No messages found in this project. Log some data to run event.
                </span>
                <Link
                  href="https://docs.phospho.ai/getting-started"
                  target="_blank"
                  className="underline"
                >
                  Learn more.
                </Link>
              </div>
            )}
            {!eventDetectionEnabled && (
              <div>Event detection is disabled for this project. </div>
            )}
            {eventDetectionEnabled &&
              totalNbTasks !== undefined &&
              totalNbTasks !== null &&
              totalNbTasks > 0 && (
                <div className="flex flex-row space-x-1 items-center">
                  This will run event detection on:{" "}
                  <span className="font-semibold ml-1">
                    {sampleSize} user messages.
                  </span>
                  <HoverCard openDelay={0} closeDelay={0}>
                    <HoverCardTrigger>
                      <QuestionMarkIcon className="size-4 rounded-full bg-primary text-secondary p-0.5" />
                    </HoverCardTrigger>
                    <HoverCardContent className="w-72">
                      You are billed based on the number of detections.{" "}
                      <Link
                        href="https://docs.phospho.ai/guides/events"
                        target="_blank"
                        className="underline"
                      >
                        Learn more
                      </Link>
                    </HoverCardContent>
                  </HoverCard>
                </div>
              )}
            {(totalNbTasks === 0 || totalNbTasks === null) && (
              <div>No messages found in this date range.</div>
            )}
          </div>
          <SheetFooter>
            <Button
              type="submit"
              disabled={
                !eventDetectionEnabled ||
                loading ||
                totalNbTasks === undefined ||
                totalNbTasks === 0 ||
                startrunLoading
              }
            >
              {startrunLoading && <Spinner className="mr-1" />}
              Run detection
            </Button>
          </SheetFooter>
        </form>
      </Form>
    </>
  );
}
