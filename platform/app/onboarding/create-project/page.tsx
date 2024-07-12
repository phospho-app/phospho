"use client";

import Authenticate from "@/components/authenticate";
import FetchOrgProject from "@/components/fetch-data/fetch-org-project";
import { Icons, Spinner } from "@/components/small-spinner";
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
import { useToast } from "@/components/ui/use-toast";
import { navigationStateStore } from "@/store/store";
import { zodResolver } from "@hookform/resolvers/zod";
import { useUser } from "@propelauth/nextjs/client";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { useSWRConfig } from "swr";
import { z } from "zod";

const formSchema = z.object({
  project_name: z
    .string()
    .min(2, {
      message: "Project name must be at least 2 characters.",
    })
    .max(32, {
      message: "Project name must be at most 30 characters.",
    }),
});

const CARD_STYLE =
  "flex flex-col items-left justify-center p-6 text-xl font-semibold space-y-4";

export default function Page() {
  const router = useRouter();
  const { mutate } = useSWRConfig();
  const { user, loading, accessToken } = useUser();
  const selectedOrgId = navigationStateStore((state) => state.selectedOrgId);
  const setproject_id = navigationStateStore((state) => state.setproject_id);
  const setSelectedOrgId = navigationStateStore(
    (state) => state.setSelectedOrgId,
  );
  const [creatingProject, setCreatingProject] = useState(false);
  const toast = useToast();

  const [redirecting, setRedirecting] = useState(false);

  const delay = (ms: number) => new Promise((res) => setTimeout(res, ms));

  // 1. Define your form.
  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    // defaultValues: {
    //   project_name: "Default project",
    // },
  });

  async function defaultProject() {
    setRedirecting(true);
    if (creatingProject) {
      return;
    }
    if (!selectedOrgId) {
      // fetch the org id from the user
      const orgId = user?.getOrgs()[0].orgId;
      if (orgId) {
        setSelectedOrgId(orgId);
      } else {
        // if the user has no orgs, redirect to the auth
        router.push("/");
      }
    }
    //Create default project for orgID
    fetch(`/api/organizations/${selectedOrgId}/create-default-project`, {
      method: "POST",
      headers: {
        Authorization: "Bearer " + accessToken,
        "Content-Type": "application/json",
      },
    }).then(async (response) => {
      const responseBody = await response.json();
      if (responseBody.id !== undefined) {
        toast.toast({
          title: "We are creating your project.",
          description: "You will be redirected in a couple seconds.",
        });
        await delay(1000);
        mutate([`/api/organizations/${selectedOrgId}/projects`, accessToken]);
        await delay(1000);
        setproject_id(responseBody.id);
        router.push(`/org`);
      } else {
        toast.toast({
          title: "Error when creating project",
          description: responseBody.error,
        });
      }
      // setCreatingProject(false);
    });
  }

  // 2. Define a submit handler.
  async function onSubmit(values: z.infer<typeof formSchema>) {
    if (creatingProject) {
      return;
    }
    if (!selectedOrgId) {
      // fetch the org id from the user
      const orgId = user?.getOrgs()[0].orgId;
      if (orgId) {
        setSelectedOrgId(orgId);
      } else {
        // if the user has no orgs, redirect to the auth
        router.push("/");
      }
    }
    setCreatingProject(true);
    setRedirecting(true);

    // Do something with the form values.
    // ✅ This will be type-safe and validated.
    fetch(`/api/organizations/${selectedOrgId}/projects`, {
      method: "POST",
      headers: {
        Authorization: "Bearer " + accessToken,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        project_name: values.project_name,
      }),
    }).then(async (response) => {
      const responseBody = await response.json();
      if (responseBody.id !== undefined) {
        router.push(`/onboarding/customize/${responseBody.id}`);
      } else {
        toast.toast({
          title: "Error when creating project",
          description: responseBody.error,
        });
      }
      // setCreatingProject(false);
    });
  }

  if (!user) {
    return <Authenticate />;
  }

  return (
    <>
      <FetchOrgProject />
      <Card className="lg:w-1/3 md:w-1/2">
        <CardHeader className="pb-0">
          <CardTitle>Create your phospho project.</CardTitle>
          <CardDescription>
            You can create multiple projects to keep your app ordered.
          </CardDescription>
        </CardHeader>
        <CardContent className={CARD_STYLE}>
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-8">
              <FormField
                control={form.control}
                name="project_name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Project name</FormLabel>
                    <FormControl>
                      <Input
                        placeholder="My chatbot"
                        {...field}
                        className="font-normal"
                        autoFocus
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <div className="flex justify-end">
                <Button
                  type="submit"
                  disabled={
                    loading || creatingProject || !form.formState.isValid
                  }
                >
                  {redirecting && <Spinner className="mr-1" />}
                  Create project
                </Button>
              </div>
            </form>
          </Form>
        </CardContent>
        <div className="relative flex items-center">
          <div className="flex-grow border-t text-muted-foreground"></div>
          <span className="flex-shrink mx-4 text-muted-foreground">Or</span>
          <div className="flex-grow border-t text-muted-foreground"></div>
        </div>
        <div>
          <CardHeader className="pb-4">
            <CardTitle>Explore sample data</CardTitle>
            <CardDescription>
              Get a feel for Phospho by exploring a sample project.
            </CardDescription>
          </CardHeader>
        </div>
        <CardContent className="space-y-8">
          <div className="flex justify-center flex-col">
            <img
              src="/image/onboarding.svg"
              alt="Onboarding Image"
              className="mx-4"
            />
          </div>
          <div className="flex justify-end mr-4">
            <Button
              onClick={() => {
                defaultProject();
              }}
              disabled={loading || creatingProject || redirecting}
            >
              {redirecting && <Spinner className="mr-1" />}
              Explore sample data
            </Button>
          </div>
        </CardContent>
      </Card>
    </>
  );
}
