"use client";

import { Spinner } from "@/components/SmallSpinner";
import { Button } from "@/components/ui/Button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/Card";
import {
  Form,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/Form";
import { Input } from "@/components/ui/Input";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/ToggleGroup";
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
  .min(3, {
    message: "Description must be at least 3 characters.",
  })
  .max(200, { message: "Description must be at most 200 characters." })
  .optional();

const formSchema = z.object({
  code: z.union([z.literal("yes"), z.literal("no")]).optional(),
  customer: z
    .union([
      z.literal("software"),
      z.literal("data"),
      z.literal("manager"),
      z.literal("founder"),
      z.literal("other"),
    ])
    .optional(),
  contact: z
    .union([
      z.literal("friends"),
      z.literal("socials"),
      z.literal("blog"),
      z.literal("conference"),
      z.literal("other"),
    ])
    .optional(),
  // if build is "other", then customBuild is required
  customCustomer: myString.optional(),
  customContact: myString.optional(),
});

const CARD_STYLE =
  "flex flex-col items-left justify-center p-6 text-xl font-semibold space-y-4";

export default function AboutYou({
  setAboutYouValues,
}: {
  setAboutYouValues: (values: any) => void;
  setCustomEvents: (values: EventDefinition[]) => void;
  setPhosphoTaskId: (taskId: string) => void;
}) {
  const router = useRouter();
  const [project, setProject] = useState<Project | null>(null);
  const { loading, accessToken } = useUser();
  const selectedOrgId = navigationStateStore((state) => state.selectedOrgId);
  const [redirect, setRedirect] = useState(false);

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
  }, [loading, selectedOrgId, accessToken, project]);

  // 1. Define your form.
  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    // defaultValues: {
    //   project_name: "Default project",
    // },
  });

  // 2. Define a submit handler.
  async function onSubmit(values: z.infer<typeof formSchema>) {
    setRedirect(true);
    router.push("/onboarding/create-project");
    fetch(`/api/onboarding/log-onboarding-survey`, {
      method: "POST",
      headers: {
        Authorization: "Bearer " + accessToken,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        code: values.code,
        customer: values.customer,
        custom_customer: values.customCustomer,
        contact: values.contact,
        custom_contact: values.customContact,
      }),
    });

    setAboutYouValues(values);
  }

  return (
    <>
      <Card className="lg:w-1/3 md:w-1/2">
        <CardHeader className="pb-0">
          <CardTitle>
            Let's setup your project{" "}
            {project && <span>{project.project_name}</span>}
          </CardTitle>
          <CardDescription>
            We just want to know a bit more about you.
          </CardDescription>
          <CardDescription>
            This will help us setup event detection.
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
                    <FormLabel>Do you write code ?</FormLabel>
                    <ToggleGroup
                      type="single"
                      className="flex-wrap"
                      value={field.value}
                      onValueChange={field.onChange}
                    >
                      <ToggleGroupItem value="yes">Yes</ToggleGroupItem>
                      <ToggleGroupItem value="no">No</ToggleGroupItem>
                    </ToggleGroup>
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
                      <FormLabel>What's your job title ?</FormLabel>
                      <ToggleGroup
                        type="single"
                        className="flex-wrap"
                        value={field.value}
                        onValueChange={field.onChange}
                      >
                        <ToggleGroupItem value="software">
                          Software engineer
                        </ToggleGroupItem>
                        <ToggleGroupItem value="data">
                          Data analyst
                        </ToggleGroupItem>
                        <ToggleGroupItem value="manager">
                          Product manager
                        </ToggleGroupItem>
                        <ToggleGroupItem value="founder">
                          Founder
                        </ToggleGroupItem>
                        <ToggleGroupItem value="other">Other</ToggleGroupItem>
                      </ToggleGroup>
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
                      <Input
                        placeholder="Researcher, student, ..."
                        {...field}
                      />
                      <FormMessage />
                    </FormItem>
                  )}
                ></FormField>
              )}
              {form.watch("customer") !== undefined && (
                <FormField
                  control={form.control}
                  name="contact"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>How did you hear about phospho ?</FormLabel>
                      <ToggleGroup
                        type="single"
                        className="flex-wrap"
                        value={field.value}
                        onValueChange={field.onChange}
                      >
                        <ToggleGroupItem value="friends">
                          Friends
                        </ToggleGroupItem>
                        <ToggleGroupItem value="socials">
                          Social media
                        </ToggleGroupItem>
                        <ToggleGroupItem value="blog">
                          Blog post
                        </ToggleGroupItem>
                        <ToggleGroupItem value="conference">
                          Conference
                        </ToggleGroupItem>
                        <ToggleGroupItem value="other">Other</ToggleGroupItem>
                      </ToggleGroup>
                      <FormMessage />
                    </FormItem>
                  )}
                ></FormField>
              )}
              {form.watch("contact") === "other" && (
                <FormField
                  control={form.control}
                  name="customContact"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>
                        Tell us more about how you heard about phospho:
                      </FormLabel>
                      <Input
                        placeholder="Employees, customers, ..."
                        {...field}
                      />
                      <FormMessage />
                    </FormItem>
                  )}
                ></FormField>
              )}

              <div className="flex justify-end">
                {/* Button is only accessible when the form is complete */}
                <Button type="submit" disabled={redirect}>
                  {redirect && <Spinner className=" mr-1" />}
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
