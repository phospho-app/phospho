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
import { authFetcher } from "@/lib/fetcher";
import {
  DetectionEngine,
  DetectionScope,
  OrgMetadata,
  Project,
} from "@/models/models";
import { navigationStateStore } from "@/store/store";
import { zodResolver } from "@hookform/resolvers/zod";
import { useUser } from "@propelauth/nextjs/client";
import { Wand2 } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import useSWR, { useSWRConfig } from "swr";
import { z } from "zod";

import {
  HoverCard,
  HoverCardContent,
  HoverCardTrigger,
} from "../ui/hover-card";

interface SuggestEventProps {
  sessionId: string;
}

const SuggestEvent: React.FC<SuggestEventProps> = ({ sessionId }) => {
  const [popoverOpen, setPopoverOpen] = useState(false);

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
  const selectedOrgId = navigationStateStore((state) => state.selectedOrgId);
  const { mutate } = useSWRConfig();
  const { loading, accessToken } = useUser();
  const { toast } = useToast();

  const { data: selectedProject }: { data: Project } = useSWR(
    project_id ? [`/api/projects/${project_id}`, accessToken] : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "GET"),
    {
      keepPreviousData: true,
    },
  );
  const { data: orgMetadata }: { data: OrgMetadata } = useSWR(
    selectedOrgId
      ? [`/api/organizations/${selectedOrgId}/metadata`, accessToken]
      : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "GET"),
    {
      keepPreviousData: true,
    },
  );

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
      event_name: "",
      description: "",
      webhook: "",
      webhook_auth_header: "",
      detection_engine: "llm_detection",
      detection_scope: "session",
      keywords: "",
      regex_pattern: "",
    },
  });

  async function onSubmit(values: z.infer<typeof formSchema>) {
    setPopoverOpen(false);
    if (!selectedProject) {
      return;
    }
    if (!selectedProject.settings) {
      return;
    }

    if (!selectedProject.settings.events) {
      selectedProject.settings.events = {};
    }

    selectedProject.settings.events[values.event_name] = {
      project_id: selectedProject.id,
      org_id: selectedProject.org_id,
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

    try {
      await fetch(`/api/projects/${project_id}`, {
        method: "POST",
        headers: {
          Authorization: "Bearer " + accessToken,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(selectedProject),
      }).then(() => {
        mutate([`/api/projects/${project_id}`, accessToken], async () => {
          return { project: selectedProject };
        });
        toast({
          title: "Event created",
          description: `Event "${values.event_name}" has been created`,
        });
      });
    } catch (error) {
      toast({
        title: "Error when creating event",
        description: `${error}`,
      });
    }
  }

  return (
    <Popover open={popoverOpen} onOpenChange={setPopoverOpen}>
      <HoverCard openDelay={0} closeDelay={0}>
        <HoverCardTrigger asChild>
          <PopoverTrigger asChild>
            <div
              className="hover:border-green-500 rounded-full p-1.5 border-2 cursor-pointer"
              onClick={() => generateEventSuggestion()}
            >
              <Wand2 className="size-4" />
            </div>
          </PopoverTrigger>
        </HoverCardTrigger>
        <HoverCardContent>
          <div className="text-sm text-muted-foreground">
            Suggest a tag based on the session&apos;s content
          </div>
        </HoverCardContent>
      </HoverCard>
      <PopoverContent className="min-w-[30rem] max-w-3/4">
        <CardHeader>
          <h2 className="font-semibold">Tag suggestion for this session</h2>
          <Form {...form}>
            <form
              onSubmit={form.handleSubmit(onSubmit)}
              className="font-normal space-y-2"
            >
              <FormField
                control={form.control}
                name="event_name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Event name*</FormLabel>
                    <FormControl>
                      <Input spellCheck placeholder="Thinking..." {...field} />
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
  );
};

export default SuggestEvent;
