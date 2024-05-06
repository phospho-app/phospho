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
    code: z.union([z.literal("yes"), z.literal("no")]),
    customer: z.union([
      z.literal("student"),
      z.literal("developer"),
      z.literal("founder"),
      z.literal("product-manager"),
      z.literal("c-level"),
      z.literal("consultant"),
      z.literal("researcher"),
      z.literal("rather-not-say"),
      z.literal("other"),
    ]),
    purpose: z.union([
      z.literal("metrics"),
      z.literal("retention"),
      z.literal("tickets"),
      z.literal("benchmark"),
      z.literal("tone-of-voice"),
      z.literal("compare-models"),
      z.literal("just-looking"),
      z.literal("rather-not-say"),
      z.literal("other"),
    ]),
    // if build is "other", then customBuild is required
    customCustomer: myString,
    customPurpose: myString,
  })
  //   .partial()
  .refine(
    (data) => {
      if (data.customer === "other" && !data.customCustomer) {
        return false;
      }
      if (data.purpose === "other" && !data.customPurpose) {
        return false;
      }
      if (data.customer !== "other") {
        return true;
      }
      if (data.purpose !== "other") {
        return true;
      }

      return true;
    },
    {
      message: "Custom customer and custom purpose are required.",
      path: ["customCustomer", "customPurpose"],
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
        code: values.code,
        customer: values.customer,
        custom_customer: values.customCustomer,
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
            <div>We just want to know a bit more about you.</div>
            <div>This will help us setup event detection.</div>
          </CardDescription>
        </CardHeader>
        <CardContent className={CARD_STYLE}>
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-8">
              <FormField
                control={form.control}
                name="code"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Can you code ?</FormLabel>
                    <FormControl>
                      <ToggleGroup
                        type="single"
                        className="flex-wrap"
                        value={field.value}
                        onValueChange={field.onChange}
                      >
                        <ToggleGroupItem value="yes">Yes</ToggleGroupItem>
                        <ToggleGroupItem value="no">No</ToggleGroupItem>
                      </ToggleGroup>
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              ></FormField>
              {form.watch("code") !== undefined && (
                <FormField
                  control={form.control}
                  name="customer"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Who are you ?</FormLabel>
                      <FormControl>
                        <ToggleGroup
                          type="single"
                          className="flex-wrap"
                          value={field.value}
                          onValueChange={field.onChange}
                        >
                          <ToggleGroupItem value="student">
                            Student
                          </ToggleGroupItem>
                          <ToggleGroupItem value="developer">
                            Developer
                          </ToggleGroupItem>
                          <ToggleGroupItem value="founder">
                            Founder
                          </ToggleGroupItem>
                          <ToggleGroupItem value="product-manager">
                            Product Manager
                          </ToggleGroupItem>
                          <ToggleGroupItem value="c-level">
                            C-level
                          </ToggleGroupItem>
                          <ToggleGroupItem value="consultant">
                            Consultant
                          </ToggleGroupItem>
                          <ToggleGroupItem value="researcher">
                            Researcher
                          </ToggleGroupItem>
                          <ToggleGroupItem value="rather-not-say">
                            Rather not say
                          </ToggleGroupItem>
                          <ToggleGroupItem value="other">Other</ToggleGroupItem>
                        </ToggleGroup>
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                ></FormField>
              )}
              {form.watch("customer") === "other" && (
                <FormField
                  control={form.control}
                  name="customCustomer"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Tell us more about who you are</FormLabel>
                      <FormControl>
                        <Input
                          placeholder="Engage users, increase retention, ..."
                          {...field}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                ></FormField>
              )}
              {form.watch("customer") !== undefined && (
                <FormField
                  control={form.control}
                  name="purpose"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>What do you need help with ?</FormLabel>
                      <FormControl>
                        <ToggleGroup
                          type="single"
                          className="flex-wrap"
                          value={field.value}
                          onValueChange={field.onChange}
                        >
                          <ToggleGroupItem value="metrics">
                            Metrics
                          </ToggleGroupItem>
                          <ToggleGroupItem value="retention">
                            Improve user retention
                          </ToggleGroupItem>
                          <ToggleGroupItem value="tickets">
                            Resolve tickets
                          </ToggleGroupItem>
                          <ToggleGroupItem value="benchmark">
                            Benchmark
                          </ToggleGroupItem>
                          <ToggleGroupItem value="tone-of-voice">
                            Tone of voice
                          </ToggleGroupItem>
                          <ToggleGroupItem value="compare-models">
                            Compare models
                          </ToggleGroupItem>
                          <ToggleGroupItem value="just-looking">
                            Just looking around
                          </ToggleGroupItem>
                          <ToggleGroupItem value="rather-not-say">
                            Rather not say
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
                        Tell us more about your expectations
                      </FormLabel>
                      <FormControl>
                        <Input
                          placeholder="A/B testing, user segmentation, ..."
                          {...field}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                ></FormField>
              )}

              <div className="flex justify-end">
                {/* Button is only accessible when the form is complete */}
                <Button type="submit" disabled={loading}>
                  Next
                </Button>
              </div>
            </form>
          </Form>
        </CardContent>
      </Card>
    </>
  );
}
