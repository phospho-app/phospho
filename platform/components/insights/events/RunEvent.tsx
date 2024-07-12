"use client";

import { DatePickerWithRange } from "@/components/DateRange";
import { Button } from "@/components/ui/Button";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/Form";
import {
  HoverCard,
  HoverCardContent,
  HoverCardTrigger,
} from "@/components/ui/HoverCard";
import { Input } from "@/components/ui/Input";
import { Separator } from "@/components/ui/Separator";
import {
  SheetDescription,
  SheetFooter,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/Sheet";
import { useToast } from "@/components/ui/UseToast";
import { authFetcher } from "@/lib/fetcher";
import { EventDefinition, Project } from "@/models/models";
import { dataStateStore, navigationStateStore } from "@/store/store";
import { zodResolver } from "@hookform/resolvers/zod";
import { useUser } from "@propelauth/nextjs/client";
import { QuestionMarkIcon } from "@radix-ui/react-icons";
import Link from "next/link";
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
  const dateRange = navigationStateStore((state) => state.dateRange);

  const { data: selectedProject }: { data: Project } = useSWR(
    project_id ? [`/api/projects/${project_id}`, accessToken] : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "GET"),
    {
      keepPreviousData: true,
    },
  );

  const { data: hasTasksData } = useSWR(
    project_id ? [`/api/explore/${project_id}/has-tasks`, accessToken] : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "POST"),
    { keepPreviousData: true },
  );
  const hasTasks: boolean = hasTasksData?.has_tasks ?? false;
  const { data: totalNbTasksData } = useSWR(
    [
      `/api/explore/${project_id}/aggregated/tasks`,
      accessToken,
      JSON.stringify(dateRange),
      "total_nb_tasks",
    ],
    ([url, accessToken]) =>
      authFetcher(url, accessToken, "POST", {
        metrics: ["total_nb_tasks"],
        filters: {
          created_at_start: dateRange?.created_at_start,
          created_at_end: dateRange?.created_at_end,
        },
      }),
    {
      keepPreviousData: true,
    },
  );
  const totalNbTasks: number | null | undefined =
    totalNbTasksData?.total_nb_tasks;

  const formSchema = z.object({
    sample_rate: z.coerce.number().min(0).max(1),
  });

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      sample_rate: 1,
    },
  });

  async function onSubmit(values: z.infer<typeof formSchema>) {
    console.log("Submitting event:", values);
    let sampleSize = Math.floor(totalNbTasks ?? 0 * values.sample_rate);
    if (!selectedProject) {
      console.log("Submit: No selected project");
      return;
    }
    try {
      const creation_response = await fetch(`/api/events/${project_id}/run`, {
        method: "POST",
        headers: {
          Authorization: "Bearer " + accessToken,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          event_id: eventToRun.id,
          sample_rate: values.sample_rate,
          created_at_start: dateRange?.created_at_start,
          created_at_end: dateRange?.created_at_end,
        }),
      });
      if (creation_response.ok) {
        toast({
          title: `Event detection for "${eventToRun.event_name}" started.`,
          description: `Running on ${sampleSize} tasks`,
        });
        setOpen(false);
      } else {
        toast({
          title: "Error starting event detection",
          description: await creation_response.text(),
        });
      }
    } catch (error) {
      toast({
        title: "Error starting event detection",
        description: `${error}`,
      });
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
              Detect event "{eventToRun.event_name}" on past data
            </SheetTitle>
            <SheetDescription>
              Detect if this event happened on a sample of previously logged
              data.
            </SheetDescription>
          </SheetHeader>
          <Separator />
          <div className="flex-col space-y-4">
            <FormItem>
              <FormLabel>Date range</FormLabel>
              <DatePickerWithRange />
            </FormItem>
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
                      defaultValue={1}
                      min={0}
                      max={1}
                      step={0.01}
                      type="number"
                      {...field}
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
                  No tasks found in this project. Log some data to run event.
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
            {totalNbTasks !== undefined &&
              totalNbTasks !== null &&
              totalNbTasks > 0 && (
                <div className="flex flex-row space-x-1 items-center">
                  This will run event detection on:{" "}
                  <span className="font-semibold ml-1">
                    {Math.floor(totalNbTasks * form.getValues("sample_rate"))}{" "}
                    tasks
                  </span>
                  <HoverCard openDelay={0} closeDelay={0}>
                    <HoverCardTrigger>
                      <QuestionMarkIcon className="h-4 w-4 rounded-full bg-primary text-secondary p-0.5" />
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
              <div>No task found in this date range.</div>
            )}
          </div>
          <SheetFooter>
            <Button
              type="submit"
              disabled={
                loading || totalNbTasks === undefined || totalNbTasks === 0
              }
            >
              Run detection
            </Button>
          </SheetFooter>
        </form>
      </Form>
    </>
  );
}
