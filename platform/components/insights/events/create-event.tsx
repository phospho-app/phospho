import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter } from "@/components/ui/card";
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
import { Textarea } from "@/components/ui/textarea";
import { dataStateStore, navigationStateStore } from "@/store/store";
import { zodResolver } from "@hookform/resolvers/zod";
import { useUser } from "@propelauth/nextjs/client";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { useSWRConfig } from "swr";
import { z } from "zod";

const formSchema = z.object({
  event_name: z
    .string()
    .min(2, {
      message: "Event name must be at least 2 characters.",
    })
    .max(30, {
      message: "Event name must be at most 30 characters.",
    }),
  description: z.string(),
  webhook: z.string().optional(),
  webhook_auth_header: z.string().optional(),
});

export default function CreateEvent() {
  const project_id = navigationStateStore((state) => state.project_id);
  const selectedProject = dataStateStore((state) => state.selectedProject);
  const orgMetadata = dataStateStore((state) => state.selectedOrgMetadata);

  // Max number of events depends on the plan
  const max_nb_events = orgMetadata?.plan === "pro" ? 100 : 10;

  if (!selectedProject) {
    return <></>;
  }

  const events = selectedProject.settings?.events || {};

  const { mutate } = useSWRConfig();
  const { loading, accessToken } = useUser();

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
  });

  async function onSubmit(values: z.infer<typeof formSchema>) {
    // Add the new event to the existing events
    const updatedEvents = {
      [values.event_name]: {
        event_name: values.event_name,
        description: values.description,
        webhook: values.webhook,
        webhook_headers:
          values.webhook_auth_header !== null
            ? { Authorization: values.webhook_auth_header }
            : null,
      }, // Use the new event's name as a key
      ...events,
    };
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
      <div>
        <span className="flex flex-row justify-between mt-8">
          <div>
            <h2 className="text-2xl font-bold tracking-tight">
              Add a new event
            </h2>
          </div>
        </span>
      </div>
      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="font-normal">
          <Card>
            <CardContent className="space-y-8">
              <FormField
                control={form.control}
                name="event_name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Event name</FormLabel>
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
                    <FormLabel htmlFor="description">Description</FormLabel>
                    <FormControl>
                      <Textarea
                        id="description"
                        placeholder="Describe how to know this event is happening, like you'd do to a 5 years old. Refer to speakers as 'the user' and 'the assistant'."
                        {...field}
                      />
                    </FormControl>
                  </FormItem>
                )}
              />
              <Accordion type="single" collapsible>
                <AccordionItem value="webhook">
                  <AccordionTrigger>
                    <span className="text-sm flex flex-row items-center text-gray-500">
                      Advanced settings (Optional)
                    </span>
                  </AccordionTrigger>
                  <AccordionContent>
                    <div className="grid gap-2">
                      <FormField
                        control={form.control}
                        name="webhook"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>Webhook</FormLabel>
                            <FormControl>
                              <Input
                                id="webhook"
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
                            <FormLabel htmlFor="description">
                              Authorization Header
                            </FormLabel>
                            <FormControl>
                              <Input
                                id="webhook_headers"
                                placeholder="Bearer sk-..."
                                {...field}
                              />
                            </FormControl>
                          </FormItem>
                        )}
                      />
                    </div>
                  </AccordionContent>
                </AccordionItem>
              </Accordion>
            </CardContent>
            <CardFooter className="justify-between space-x-2">
              <Button
                type="submit"
                disabled={
                  loading ||
                  !form.formState.isValid ||
                  // too many events
                  (events &&
                    max_nb_events &&
                    Object.keys(events).length >= max_nb_events)
                }
              >
                Create event
              </Button>
              {
                // too many events
                events &&
                  max_nb_events &&
                  Object.keys(events).length >= max_nb_events && (
                    <p className="text-red-700">
                      {max_nb_events}/{max_nb_events} events created.{" "}
                      <Link href="/org/settings/billing" className="underline">
                        Upgrade plan to create more.
                      </Link>
                    </p>
                  )
              }
              {
                // current number of events
                events &&
                  max_nb_events &&
                  Object.keys(events).length < max_nb_events && (
                    <p>
                      {Object.keys(events).length}/{max_nb_events} events
                      created
                    </p>
                  )
              }
            </CardFooter>
          </Card>
        </form>
      </Form>
    </>
  );
}
