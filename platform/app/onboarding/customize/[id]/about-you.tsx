"use client";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
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
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { EventDefinition, Project } from "@/models/models";
import { navigationStateStore } from "@/store/store";
import { zodResolver } from "@hookform/resolvers/zod";
import { useUser } from "@propelauth/nextjs/client";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

// `myString` is a string that can be either optional (undefined or missing),
// empty, or min 4
const myString = z
  .string()
  .min(10, {
    message: "Description must be at least 10 characters.",
  })
  .max(200, { message: "Description must be at most 200 characters." })
  .optional();

const formSchema = z
  .object({
    build: z.union([
      z.literal("knowledge-assistant"),
      z.literal("virtual-companion"),
      z.literal("narrator"),
      z.literal("ask-ai"),
      z.literal("customer-support"),
      z.literal("other"),
    ]),
    purpose: z.union([
      z.literal("entertainment"),
      z.literal("aquisition"),
      z.literal("retention"),
      z.literal("marketing"),
      z.literal("productivity"),
      z.literal("resolve-tikets"),
      z.literal("other"),
    ]),
    // if build is "other", then customBuild is required
    customBuild: myString,
    customPurpose: myString,
  })
  //   .partial()
  .refine(
    (data) => {
      if (data.build === "other" && !data.customBuild) {
        return false;
      }
      if (data.purpose === "other" && !data.customPurpose) {
        return false;
      }
      if (data.build !== "other") {
        return true;
      }
      if (data.purpose !== "other") {
        return true;
      }

      return true;
    },
    {
      message: "Custom build and custom purpose are required.",
      path: ["customBuild", "customPurpose"],
    },
  );

const CARD_STYLE =
  "flex flex-col items-left justify-center p-6 text-xl font-semibold space-y-4";

export default function AboutYou({
  project_id,
  setAboutYouValues,
  setCustomEvents,
  setPhosphoTaskId,
}: {
  project_id: string;
  setAboutYouValues: (values: any) => void;
  setCustomEvents: (values: EventDefinition[]) => void;
  setPhosphoTaskId: (taskId: string) => void;
}) {
  const router = useRouter();
  const [project, setProject] = useState<Project | null>(null);
  const { user, loading, accessToken } = useUser();
  const selectedOrgId = navigationStateStore((state) => state.selectedOrgId);

  useEffect(() => {
    (async () => {
      if (!project) return;
      if (!selectedOrgId) return;
      const response = await fetch(
        `/api/organizations/${selectedOrgId}/metadata`,
        {
          method: "GET",
          headers: {
            Authorization: "Bearer " + accessToken,
            "Content-Type": "application/json",
          },
        },
      );
      const response_json = await response.json();
      console.log("plan", response_json);
      console.log("events", project.settings?.events);
      if (response_json.plan === "hobby") {
        // Without events, skip
        if (!project.settings?.events) {
          return;
        }
        if (Object.keys(project.settings?.events).length >= 10) {
          // Reached the events limit
          // Redirect to the home page
          console.log("Reached the events limit", project);
          router.push("/");
        }
      }
      console.log("plan", response_json.plan);
    })();
  }, [project_id, loading, selectedOrgId, accessToken, project]);

  // 1. Define your form.
  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    // defaultValues: {
    //   project_name: "Default project",
    // },
  });

  // 2. Define a submit handler.
  async function onSubmit(values: z.infer<typeof formSchema>) {
    // Do something with the form values.
    // ✅ This will be type-safe and validated.
    // Call the API endpoint
    fetch(`/api/projects/${project_id}/suggest-events`, {
      method: "POST",
      headers: {
        Authorization: "Bearer " + accessToken,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        build: values.build,
        custom_build: values.customBuild,
        purpose: values.purpose,
        custom_purpose: values.customPurpose,
      }),
    }).then(async (res) => {
      const response_json = await res.json();
      setCustomEvents(response_json.suggested_events);
      setPhosphoTaskId(response_json.phospho_task_id);
    });

    setAboutYouValues(values);
  }

  useEffect(() => {
    // Fetch the project from the server
    (async () => {
      if (!accessToken) return;
      console.log("Fetching project from server in onboarding:", project_id);
      const response = await fetch(`/api/projects/${project_id}`, {
        headers: {
          Authorization: "Bearer " + accessToken,
        },
      });
      const responseBody = await response.json();
      if (!response.ok) {
        // This project doesn't exist or the user doesn't have access to it.
        // Redirect the user to the home page.
        console.log(
          "Project doesn't exist or the user doesn't have access to it",
        );
        router.push("/");
        return;
      }
      setProject(responseBody);
    })();
  }, [accessToken, loading]);

  return (
    <>
      <Card className="lg:w-1/3 md:w-1/2">
        <CardHeader className="pb-0">
          <CardTitle>
            Let's setup your project{" "}
            {project && <span>{project.project_name}</span>}
          </CardTitle>
          <CardDescription>
            Based on your use case, phospho will suggest relevant events to
            track in your app.
          </CardDescription>
        </CardHeader>
        <CardContent className={CARD_STYLE}>
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-8">
              <FormField
                control={form.control}
                name="build"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>What are you building with a LLM?</FormLabel>
                    {/* <FormDescription className="font-normal">
                      We will customize defaults based on your choice.
                    </FormDescription> */}
                    <FormControl>
                      <ToggleGroup
                        type="single"
                        className="flex-wrap"
                        value={field.value}
                        onValueChange={field.onChange}
                      >
                        <ToggleGroupItem value="knowledge-assistant">
                          Knowledge assistant
                        </ToggleGroupItem>
                        <ToggleGroupItem value="virtual-companion">
                          Virtual companion
                        </ToggleGroupItem>
                        <ToggleGroupItem value="customer-support">
                          Customer support
                        </ToggleGroupItem>
                        <ToggleGroupItem value="narrator">
                          Adventure narrator
                        </ToggleGroupItem>
                        <ToggleGroupItem value="ask-ai">
                          "Ask AI" button
                        </ToggleGroupItem>
                        <ToggleGroupItem value="other">Other</ToggleGroupItem>
                      </ToggleGroup>
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              ></FormField>
              {form.watch("build") === "other" && (
                <FormField
                  control={form.control}
                  name="customBuild"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Give us a brief description</FormLabel>
                      <FormControl>
                        <Input
                          placeholder="A code generator, a chatbot, a game..."
                          {...field}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                ></FormField>
              )}
              {form.watch("build") !== undefined && (
                <FormField
                  control={form.control}
                  name="purpose"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>What's the goal of this project?</FormLabel>
                      <FormDescription className="font-normal">
                        Different goals mean different attention points.
                      </FormDescription>
                      <FormControl>
                        <ToggleGroup
                          type="single"
                          className="flex-wrap"
                          value={field.value}
                          onValueChange={field.onChange}
                        >
                          <ToggleGroupItem value="productivity">
                            Increase productivity
                          </ToggleGroupItem>
                          <ToggleGroupItem value="aquisition">
                            Generate leads
                          </ToggleGroupItem>
                          <ToggleGroupItem value="entertainment">
                            Have fun
                          </ToggleGroupItem>
                          <ToggleGroupItem value="retention">
                            Avoid churn
                          </ToggleGroupItem>
                          <ToggleGroupItem value="resolve-tikets">
                            Resolve tickets
                          </ToggleGroupItem>
                          <ToggleGroupItem value="marketing">
                            Promote a brand
                          </ToggleGroupItem>
                          <ToggleGroupItem value="other">Other</ToggleGroupItem>
                        </ToggleGroup>
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                ></FormField>
              )}
              {form.watch("purpose") === "other" && (
                <FormField
                  control={form.control}
                  name="customPurpose"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>
                        Tell us more about your project purpose
                      </FormLabel>
                      <FormControl>
                        <Input
                          placeholder="Mental health, lifestyle change..."
                          {...field}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                ></FormField>
              )}

              <div className="flex justify-end">
                <Button type="submit" disabled={loading}>
                  Create events
                </Button>
              </div>
            </form>
          </Form>
        </CardContent>
      </Card>
    </>
  );
}
