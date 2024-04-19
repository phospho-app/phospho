"use client";

import { Button } from "@/components/ui/button";
import { CardHeader } from "@/components/ui/card";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Textarea } from "@/components/ui/textarea";
import { useToast } from "@/components/ui/use-toast";
import { DetectionEngine, DetectionScope } from "@/models/models";
import { EventDefinition } from "@/models/models";
import { dataStateStore, navigationStateStore } from "@/store/store";
import { zodResolver } from "@hookform/resolvers/zod";
import { useUser } from "@propelauth/nextjs/client";
import { Wand2 } from "lucide-react";
import { useForm } from "react-hook-form";
import { useSWRConfig } from "swr";
import { z } from "zod";

interface SuggestEventProps {
  sessionId: string;
  event: EventDefinition;
}

const SuggestEvent: React.FC<SuggestEventProps> = ({ sessionId, event }) => {
  const generateEventSuggestion = () => {
    // Let's fill eventToEdit?.description with our event prediction
    try {
      const fetchEventDescription = async () => {
        const suggestion_response = await fetch(
          `/api/sessions/${sessionId}/suggestion`,
          {
            method: "GET",
            headers: {
              Authorization: "Bearer " + accessToken,
              "Content-Type": "application/json",
            },
          },
        );

        if (suggestion_response.ok) {
          const [eventName, eventDescription] =
            await suggestion_response.json();
          form.setValue("event_name", eventName);
          form.setValue("description", eventDescription);
          console.log("Fetched event name:", eventName);
          console.log("Fetched event description:", eventDescription);
        } else {
          console.error(
            "Failed to fetch event description:",
            suggestion_response.status,
          );
        }
      };

      fetchEventDescription();
    } catch (error) {
      console.error("Failed to fetch event description:", error);
    }
  };

  const project_id = navigationStateStore((state) => state.project_id);
  const orgMetadata = dataStateStore((state) => state.selectedOrgMetadata);
  const { mutate } = useSWRConfig();
  const { loading, accessToken } = useUser();
  const { toast } = useToast();

  const selectedProject = dataStateStore((state) => state.selectedProject);
  const currentEvents = selectedProject?.settings?.events || {};
  const max_nb_events = orgMetadata?.plan === "pro" ? 100 : 10;
  const current_nb_events = Object.keys(currentEvents).length;

  const formSchema = z.object({
    event_name: z
      .string()
      .min(2, {
        message: "Event name must be at least 2 characters.",
      })
      .max(32, {
        message: "Event name must be at most 32 characters.",
      }),
    description: z
      .string()
      .min(10, "Description must be at least 10 characters long.")
      .max(1000, "Description must be at most 1000 characters long."),
    webhook: z.string().optional(),
    webhook_auth_header: z.string().optional(),
    detection_engine: z
      .enum(["llm_detection", "regex_detection", "keyword_detection"])
      .default("llm_detection"),
    detection_scope: z
      .enum(["task", "session", "task_input_only", "task_output_only"])
      .default("session"),
    keywords: z.string().optional(),
    regex_pattern: z.string().optional(),
  });

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      event_name: event?.event_name ?? "",
      description: event?.description ?? "",
      webhook: "",
      webhook_auth_header: "",
      detection_engine: "llm_detection",
      detection_scope: "session",
      keywords: "",
      regex_pattern: "",
    },
  });

  async function onSubmit(values: z.infer<typeof formSchema>) {
    console.log("Submitting event:", values);
    if (!selectedProject) {
      console.log("Submit: No selected project");
      return;
    }
    if (!selectedProject.settings) {
      console.log("Submit: No selected project settings");
      return;
    }
    if (event.event_name !== values.event_name) {
      delete selectedProject.settings.events[event.event_name];
    }

    selectedProject.settings.events[values.event_name] = {
      event_name: values.event_name,
      description: values.description,
      webhook: values.webhook,
      webhook_headers: values.webhook_auth_header
        ? { Authorization: values.webhook_auth_header }
        : null,
      detection_engine: values.detection_engine as DetectionEngine,
      detection_scope: values.detection_scope as DetectionScope,
      keywords: values.keywords,
      regex_pattern: values.regex_pattern,
    };
    console.log("Updated selected project:", selectedProject);

    try {
      const creation_response = await fetch(`/api/projects/${project_id}`, {
        method: "POST",
        headers: {
          Authorization: "Bearer " + accessToken,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(selectedProject),
      }).then((response) => {
        mutate(
          [`/api/projects/${project_id}`, accessToken],
          async (data: any) => {
            return { project: selectedProject };
          },
        );
      });
    } catch (error) {
      toast({
        title: "Error when creating event",
        description: `${error}`,
      });
    }
  }

  return (
    <div>
      <Popover>
        <PopoverTrigger>
          <button
            className={`mr-1 hover:border-green-500 rounded-full p-1 border-2 `}
            onClick={() => generateEventSuggestion()}
          >
            <Wand2 className="h-4 w-4" />
          </button>
        </PopoverTrigger>
        <PopoverContent className="w-400">
          <CardHeader>
            <h2 className="text-lg font-semibold">Event suggestion</h2>
            <p className="text-sm text-gray-500">
              Based on the session's content, we recommend creating this new
              event
            </p>
            <Form {...form}>
              <form
                onSubmit={form.handleSubmit(onSubmit)}
                className="font-normal space-y-4"
                key={`createEventForm${event.event_name}`}
              >
                <FormField
                  control={form.control}
                  name="event_name"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Event name*</FormLabel>
                      <FormControl>
                        <Input
                          spellCheck
                          placeholder="Thinking..."
                          {...field}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="description"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Description*</FormLabel>
                      <FormControl>
                        <Textarea
                          id="description"
                          placeholder="Thinking..."
                          {...field}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </form>
            </Form>
            <Button
              type="submit"
              className="hover:bg-green-600"
              disabled={
                loading ||
                current_nb_events >= max_nb_events ||
                !form.formState.isValid
              }
              onClick={() => form.handleSubmit(onSubmit)()}
            >
              Save
            </Button>
          </CardHeader>
        </PopoverContent>
      </Popover>
    </div>
  );
};

export default SuggestEvent;
