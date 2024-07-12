"use client";

import { Button } from "@/components/ui/Button";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/Form";
import { Input } from "@/components/ui/Input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/Select";
import { Separator } from "@/components/ui/Separator";
import { SheetFooter, SheetHeader, SheetTitle } from "@/components/ui/Sheet";
import { Textarea } from "@/components/ui/Textarea";
import { useToast } from "@/components/ui/UseToast";
import { authFetcher } from "@/lib/fetcher";
import { DetectionEngine, DetectionScope, Project } from "@/models/models";
import { ScoreRangeSettings } from "@/models/models";
import { dataStateStore, navigationStateStore } from "@/store/store";
import { zodResolver } from "@hookform/resolvers/zod";
import { useUser } from "@propelauth/nextjs/client";
import Link from "next/link";
import { useForm } from "react-hook-form";
import useSWR, { useSWRConfig } from "swr";
import { z } from "zod";

export default function CreateEvent({
  setOpen,
  eventNameToEdit,
}: {
  setOpen: (open: boolean) => void;
  eventNameToEdit?: string;
}) {
  // Component to create an event or edit an existing event

  const project_id = navigationStateStore((state) => state.project_id);
  const orgMetadata = dataStateStore((state) => state.selectedOrgMetadata);
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

  const currentEvents = selectedProject?.settings?.events || {};
  const eventToEdit = eventNameToEdit ? currentEvents[eventNameToEdit] : null;

  // Max number of events depends on the plan
  const max_nb_events = orgMetadata?.plan === "pro" ? 100 : 10;
  const current_nb_events = Object.keys(currentEvents).length;

  // If we are editing an event, we need to pre-fill the form
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
      .default("task"),
    keywords: z.string().optional(),
    regex_pattern: z.string().optional(),
    score_range_settings: z
      .object({
        min: z.number().min(0).max(1),
        max: z.number().min(1).max(5),
        score_type: z.enum(["confidence", "range", "category"]),
        categories: z.any().transform((value, ctx) => {
          // If array of string, return it
          if (Array.isArray(value)) {
            return value;
          }
          // If not a string, raise an error
          if (typeof value !== "string") {
            ctx.addIssue({
              code: z.ZodIssueCode.custom,
              message: "Categories must be a string.",
            });
            return z.NEVER;
          }
          // Split the string into an array of categories
          let categories = value.split(",").map((category) => category.trim());
          // Remove empty strings
          categories = categories.filter((category) => category !== "");
          // Raise an error if there are less than 1 category or more than 9
          if (categories.length < 1 || categories.length > 9) {
            ctx.addIssue({
              code: z.ZodIssueCode.custom,
              message: "Categories must be between 1 and 9.",
            });
            return z.NEVER;
          }
          return categories;
        }),
      })
      .optional(),
  });

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      event_name: eventToEdit?.event_name ?? "",
      description: eventToEdit?.description ?? "",
      webhook: eventToEdit?.webhook ?? "",
      webhook_auth_header: eventToEdit?.webhook_headers?.Authorization ?? "",
      detection_engine: eventToEdit?.detection_engine ?? "llm_detection",
      detection_scope: eventToEdit?.detection_scope ?? "task",
      keywords: eventToEdit?.keywords ?? "",
      regex_pattern: eventToEdit?.regex_pattern ?? "",
      score_range_settings: eventToEdit?.score_range_settings,
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
    if (
      eventNameToEdit !== null &&
      eventNameToEdit !== undefined &&
      eventNameToEdit !== values.event_name
    ) {
      // Editing the event means that we remove the previous event and add the new one
      // This is in case the event name has changed
      delete selectedProject.settings.events[eventNameToEdit];
    }

    // On purpose, we do not pass the job_id, so a new job object will be created for this event
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
      score_range_settings: values.score_range_settings as ScoreRangeSettings,
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
        setOpen(false);
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
    <div className="space-y-2">
      <Form {...form}>
        <form
          onSubmit={form.handleSubmit(onSubmit)}
          className="font-normal space-y-4"
          key={`createEventForm${eventToEdit?.event_name}`}
        >
          <SheetHeader>
            <SheetTitle className="text-xl">
              {(eventNameToEdit === null || eventNameToEdit === undefined) && (
                <div>Setup new event</div>
              )}
              {eventNameToEdit && <div>Edit event "{eventNameToEdit}"</div>}
            </SheetTitle>
          </SheetHeader>
          {/* <Separator /> */}
          {/* Event templates */}
          <div>
            <h2 className="text-muted-foreground text-xs mb-1">Templates</h2>
            <div className="flex space-x-4">
              <Button
                onClick={(mouseEvent) => {
                  mouseEvent.stopPropagation();
                  form.setValue("event_name", "Penetration testing");
                  form.setValue(
                    "description",
                    "The user is trying to jailbreak the assistant. Example: asking to ignore any previous instruction, asking malicious questions, etc.",
                  );
                  form.setValue("detection_scope", "task");
                  form.setValue("detection_engine", "llm_detection");
                  // Prevent the form from submitting
                  mouseEvent.preventDefault();
                }}
              >
                Penetration testing
              </Button>
              <Button
                onClick={(mouseEvent) => {
                  mouseEvent.stopPropagation();
                  form.setValue("event_name", "Assistant coherence");
                  form.setValue(
                    "description",
                    "The agent answers coherently and consistently.",
                  );
                  form.setValue("detection_scope", "session");
                  form.setValue("detection_engine", "llm_detection");
                  // Prevent the form from submitting
                  mouseEvent.preventDefault();
                }}
              >
                Coherence
              </Button>
              <Button
                onClick={(mouseEvent) => {
                  mouseEvent.stopPropagation();
                  form.setValue("event_name", "Assistant correctness");
                  form.setValue(
                    "description",
                    "The assistant correctly answered the question.",
                  );
                  form.setValue("detection_scope", "task");
                  form.setValue("detection_engine", "llm_detection");
                  // Prevent the form from submitting
                  mouseEvent.preventDefault();
                }}
              >
                Correctness
              </Button>
              <Button
                onClick={(mouseEvent) => {
                  mouseEvent.stopPropagation();
                  form.setValue("event_name", "Assistant plausibility");
                  form.setValue(
                    "description",
                    "The assistant's answer is plausible and makes sense.",
                  );
                  form.setValue("detection_scope", "task");
                  form.setValue("detection_engine", "llm_detection");
                  // Prevent the form from submitting
                  mouseEvent.preventDefault();
                }}
              >
                Plausibility
              </Button>
            </div>
          </div>
          <Separator />
          <div className="flex-col space-y-2">
            <div className="flex flex-row items-center space-x-2">
              <FormField
                control={form.control}
                name="event_name"
                render={({ field }) => (
                  <FormItem className="flex-grow">
                    <FormLabel>Event name*</FormLabel>
                    <FormControl>
                      <Input
                        spellCheck
                        placeholder="e.g.: rude tone of voice, user frustration, user says 'I want to cancel'..."
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="detection_scope"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Detection scope</FormLabel>
                    <Select
                      onValueChange={field.onChange}
                      defaultValue={field.value ?? "task"}
                    >
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent position="popper">
                        <SelectItem value="task">Task</SelectItem>
                        <SelectItem value="session">Session</SelectItem>
                        <SelectItem value="task_input_only">
                          Task input only
                        </SelectItem>
                        <SelectItem value="task_output_only">
                          Task output only
                        </SelectItem>
                      </SelectContent>
                    </Select>
                  </FormItem>
                )}
              />
            </div>
            <FormField
              control={form.control}
              name="description"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Description*</FormLabel>
                  <FormControl>
                    <Textarea
                      id="description"
                      placeholder="Use simple language. Refer to speakers as 'the user' and 'the assistant'."
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="detection_engine"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Engine</FormLabel>
                  <Select
                    onValueChange={field.onChange}
                    defaultValue={field.value ?? "llm_detection"}
                  >
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue
                          defaultValue={field.value ?? "llm_detection"}
                        />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent position="popper">
                      <SelectItem value="llm_detection">
                        LLM Detection
                      </SelectItem>
                      <SelectItem value="keyword_detection">
                        Keyword Detection
                      </SelectItem>
                      <SelectItem value="regex_detection">
                        Regex Detection
                      </SelectItem>
                      <SelectItem disabled value="other">
                        More coming soon!
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </FormItem>
              )}
            />
            {
              // specify the scoreRangeSettings for the LLM detection engine
              form.watch("detection_engine") === "llm_detection" && (
                // Let user pick the scoreRangeSettings.score_type. Then, prefill the min and max values based on the score_type
                <FormField
                  control={form.control}
                  name="score_range_settings"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Output type</FormLabel>
                      <FormControl>
                        <Select
                          onValueChange={(value) => {
                            if (value === "confidence") {
                              field.onChange({
                                score_type: "confidence",
                                min: 0,
                                max: 1,
                                categories: [],
                              });
                            } else if (value === "range") {
                              field.onChange({
                                score_type: "range",
                                min: 1,
                                max: 5,
                                categories: [],
                              });
                            } else if (value === "category") {
                              field.onChange({
                                score_type: "category",
                                min: 1,
                                max: 1,
                                categories: "",
                              });
                            }
                          }}
                          defaultValue={field.value?.score_type ?? "confidence"}
                        >
                          <FormControl>
                            <SelectTrigger>
                              <SelectValue
                                defaultValue={
                                  field.value?.score_type ?? "confidence"
                                }
                              />
                            </SelectTrigger>
                          </FormControl>
                          <SelectContent position="popper">
                            <SelectItem value="confidence">
                              Yes/No (boolean)
                            </SelectItem>
                            <SelectItem value="range">
                              1-5 score (number)
                            </SelectItem>
                            <SelectItem value="category">
                              Category (enum)
                            </SelectItem>
                          </SelectContent>
                        </Select>
                      </FormControl>
                    </FormItem>
                  )}
                />
              )
            }
            {form.watch("detection_engine") === "llm_detection" &&
              form.watch("score_range_settings")?.score_type === "category" && (
                <FormField
                  control={form.control}
                  name="score_range_settings.categories"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Categories</FormLabel>
                      <FormControl>
                        <Input placeholder="happy,sad,neutral" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              )}
            {form.watch("detection_engine") === "keyword_detection" && (
              <FormField
                control={form.control}
                name="keywords"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>
                      List of words to detect, separated by a comma
                    </FormLabel>
                    <FormControl>
                      <Input
                        placeholder="question, why, how, what"
                        {...field}
                      />
                    </FormControl>
                  </FormItem>
                )}
              />
            )}
            {form.watch("detection_engine") === "regex_detection" && (
              <FormField
                control={form.control}
                name="regex_pattern"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Regex pattern to match - </FormLabel>
                    <Link
                      className="hover:underline hover:text-blue-500"
                      href="https://regexr.com/"
                    >
                      Test your regex pattern here
                    </Link>{" "}
                    <FormMessage>
                      Be careful, "happy" will also match "unhappy" unless you
                      add whitespaces like so: " happy "
                    </FormMessage>
                    <FormControl>
                      <Input
                        placeholder="^[0-9]{5}$ or why | how | what"
                        {...field}
                      />
                    </FormControl>
                  </FormItem>
                )}
              />
            )}
            <h2 className="text-sm font-semibold pt-4">
              Advanced settings (optional)
            </h2>
            <Separator />
            <div className="flex flex-row space-x-2 w-full">
              <FormField
                control={form.control}
                name="webhook"
                render={({ field }) => (
                  <FormItem className="flex-grow">
                    <FormLabel className="text-muted-foreground">
                      Webhook URL
                    </FormLabel>
                    <FormControl>
                      <Input
                        placeholder="https://your-api.com/webhook"
                        {...field}
                      />
                    </FormControl>
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="webhook_auth_header"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel className="text-muted-foreground">
                      Authorization Header
                    </FormLabel>
                    <FormControl>
                      <Input placeholder="Bearer sk-..." {...field} />
                    </FormControl>
                  </FormItem>
                )}
              />
            </div>
          </div>
          <SheetFooter>
            <Button
              type="submit"
              disabled={
                loading ||
                // !form.formState.isValid ||
                // too many events
                ((eventNameToEdit === null || eventNameToEdit === undefined) &&
                  currentEvents &&
                  max_nb_events &&
                  current_nb_events + 1 >= max_nb_events)
              }
            >
              {(eventNameToEdit === null || eventNameToEdit === undefined) && (
                <div>Add event</div>
              )}
              {eventNameToEdit && <div>Save edits</div>}
            </Button>
          </SheetFooter>
        </form>
      </Form>
    </div>
  );
}
