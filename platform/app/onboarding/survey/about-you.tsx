"use client";

import { Spinner } from "@/components/small-spinner";
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
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { zodResolver } from "@hookform/resolvers/zod";
import { useUser } from "@propelauth/nextjs/client";
import { useRouter } from "next/navigation";
import { useState } from "react";
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

export type AboutYouFormValues = z.infer<typeof formSchema>;

export default function AboutYou({
  setAboutYouValues,
}: {
  setAboutYouValues: React.Dispatch<
    React.SetStateAction<AboutYouFormValues | null>
  >;
}) {
  const router = useRouter();
  const { accessToken } = useUser();
  const [redirect, setRedirect] = useState(false);

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
  });

  async function onSubmit(values: z.infer<typeof formSchema>) {
    setRedirect(true);
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
    }).then(() => {
      setAboutYouValues(values);
      router.push("/onboarding/setup-project");
    });
  }

  return (
    <>
      <Card className="lg:w-1/3 md:w-1/2">
        <CardHeader className="pb-0">
          <CardTitle>Welcome to phospho!</CardTitle>
          <CardDescription>
            Help us setup your account by telling us a bit more about you.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col items-left justify-center p-6 text-xl font-semibold space-y-4">
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
                      <FormLabel>What&apos;s your job title ?</FormLabel>
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
                      <FormLabel>
                        Who <i>are</i> you then?
                      </FormLabel>
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
                        Give us more details about how you found us
                      </FormLabel>
                      <Input
                        placeholder="Github, google search, research papers..."
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
