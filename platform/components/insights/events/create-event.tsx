import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import {
  AlertDialogCancel,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import {
  DetectionEngine,
  DetectionScope,
  EventDefinition,
} from "@/models/models";
import { dataStateStore, navigationStateStore } from "@/store/store";
import { zodResolver } from "@hookform/resolvers/zod";
import { useUser } from "@propelauth/nextjs/client";
import { AlertDialogAction } from "@radix-ui/react-alert-dialog";
import { useForm } from "react-hook-form";
import { useSWRConfig } from "swr";
import { z } from "zod";

export default function CreateEvent({
  setOpen,
  currentEvents,
  eventNameToEdit,
}: {
  setOpen: (open: boolean) => void;
  currentEvents: Record<string, EventDefinition>;
  eventNameToEdit?: string;
}) {
  // Component to create an event or edit an existing event

  const project_id = navigationStateStore((state) => state.project_id);
  const selectedProject = dataStateStore((state) => state.selectedProject);
  const orgMetadata = dataStateStore((state) => state.selectedOrgMetadata);

  // Max number of events depends on the plan
  const max_nb_events = orgMetadata?.plan === "pro" ? 100 : 10;

  const eventToEdit = eventNameToEdit ? currentEvents[eventNameToEdit] : null;

  if (!selectedProject) {
    return <></>;
  }

  console.log("eventToEdit", eventToEdit);

  const { mutate } = useSWRConfig();
  const { loading, accessToken } = useUser();

  // If we are editing an event, we need to pre-fill the form
  const formSchema = z.object({
    event_name: z
      .string()
      .min(2, {
        message: "Event name must be at least 2 characters.",
      })
      .max(30, {
        message: "Event name must be at most 30 characters.",
      }),
    description: z
      .string()
      .min(10, "Description must be at least 10 characters long."),
    webhook: z.string().optional(),
    webhook_auth_header: z.string().optional(),
    detection_engine: z.enum(["llm_detection"]).default("llm_detection"),
    detection_scope: z
      .enum(["task", "session", "task_input_only", "task_output_only"])
      .default("task"),
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
    },
  });

  async function onSubmit(values: z.infer<typeof formSchema>) {
    let updatedEvents = { ...currentEvents };
    if (eventNameToEdit) {
      // Editing the event means that we remove the previous event and add the new one
      // This is in case the event name has changed
      delete updatedEvents[eventNameToEdit];
    }

    updatedEvents[values.event_name] = {
      event_name: values.event_name,
      description: values.description,
      webhook: values.webhook,
      webhook_headers: values.webhook_auth_header
        ? { Authorization: values.webhook_auth_header }
        : null,
      detection_engine: values.detection_engine as DetectionEngine,
      detection_scope: values.detection_scope as DetectionScope,
    };

    console.log("updatedEvents", updatedEvents);

    // We then send back all the settings to be pushed back into the project
    const updatedSettings = {
      ...selectedProject?.settings,
      events: updatedEvents,
    };

    try {
      const creation_response = await fetch(`/api/projects/${project_id}`, {
        method: "POST",
        headers: {
          Authorization: "Bearer " + accessToken,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          settings: updatedSettings,
        }),
      });

      const responseData = await creation_response.json();
      console.log("response", responseData);

      mutate(
        [`/api/projects/${project_id}`, accessToken],
        async (data: any) => {
          return { project: { ...data.project, settings: updatedSettings } };
        },
      );
    } catch (error) {
      console.error("Error submitting event:", error);
    }
  }

  return (
    <>
      <AlertDialogHeader>
        {(eventNameToEdit === null || eventNameToEdit === undefined) && (
          <AlertDialogTitle>Setup new event</AlertDialogTitle>
        )}
        {eventNameToEdit && (
          <AlertDialogTitle>Edit event "{eventNameToEdit}"</AlertDialogTitle>
        )}
      </AlertDialogHeader>
      <Form {...form}>
        <form
          onSubmit={form.handleSubmit(onSubmit)}
          className="font-normal space-y-4"
          key={`createEventForm${eventToEdit?.event_name}`}
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
            name="description"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Description*</FormLabel>
                <FormControl>
                  <Textarea
                    id="description"
                    placeholder="Describe this event like you'd do to a 5 years old. Refer to speakers as 'the user' and 'the assistant'."
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
              <FormItem className="w-1/2">
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
          <Accordion type="single" collapsible className="mb-2">
            <AccordionItem value="webhook">
              <AccordionTrigger>
                <span className="text-sm flex flex-row items-center text-gray-500 ">
                  Advanced settings (optional)
                </span>
              </AccordionTrigger>
              <AccordionContent className="space-y-4">
                <FormField
                  control={form.control}
                  name="webhook"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Webhook (optional)</FormLabel>
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
                      <FormLabel>Authorization Header</FormLabel>
                      <FormControl>
                        <Input placeholder="Bearer sk-..." {...field} />
                      </FormControl>
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="detection_engine"
                  render={({ field }) => (
                    <FormItem className="w-1/2">
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
                          <SelectItem disabled value="other">
                            More coming soon!
                          </SelectItem>
                        </SelectContent>
                      </Select>
                    </FormItem>
                  )}
                />
              </AccordionContent>
            </AccordionItem>
          </Accordion>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction asChild>
              <Button
                type="submit"
                disabled={
                  loading ||
                  // !form.formState.isValid ||
                  // too many events
                  ((eventNameToEdit === null ||
                    eventNameToEdit === undefined) &&
                    currentEvents &&
                    max_nb_events &&
                    Object.keys(currentEvents).length + 1 >= max_nb_events)
                }
                onClick={() => {
                  if (form.formState.isValid) {
                    setOpen(false);
                  }
                }}
              >
                {(eventNameToEdit === null ||
                  eventNameToEdit === undefined) && <>Add event</>}
                {eventNameToEdit && <>Save</>}
              </Button>
            </AlertDialogAction>
          </AlertDialogFooter>
        </form>
      </Form>
    </>
  );
}
