"use client";

import {
  SendDataAlertDialog,
  UploadDatasetButton,
  UploadDatasetInstructions,
} from "@/components/callouts/import-data";
import FetchOrgProject from "@/components/fetch-data/fetch-org-project";
import { Spinner } from "@/components/small-spinner";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { AlertDialog, AlertDialogTrigger } from "@/components/ui/alert-dialog";
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
import {
  HoverCard,
  HoverCardContent,
  HoverCardTrigger,
} from "@/components/ui/hover-card";
import { Input } from "@/components/ui/input";
import { useToast } from "@/components/ui/use-toast";
import { authFetcher } from "@/lib/fetcher";
import { Project } from "@/models/models";
import { navigationStateStore } from "@/store/store";
import { zodResolver } from "@hookform/resolvers/zod";
import { useUser } from "@propelauth/nextjs/client";
import { QuestionMarkIcon } from "@radix-ui/react-icons";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import useSWR, { useSWRConfig } from "swr";
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

export default function Page() {
  const router = useRouter();
  const { mutate } = useSWRConfig();
  const { toast } = useToast();
  const { user, loading: userLoading, accessToken } = useUser();

  const selectedOrgId = navigationStateStore((state) => state.selectedOrgId);
  const project_id = navigationStateStore((state) => state.project_id);
  const setproject_id = navigationStateStore((state) => state.setproject_id);
  const setSelectedOrgId = navigationStateStore(
    (state) => state.setSelectedOrgId,
  );
  const [creatingProject, setCreatingProject] = useState(false);
  const [redirecting, setRedirecting] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [importDataDialogOpen, setImportDataDialogOpen] = useState(false);

  const delay = (ms: number) => new Promise((res) => setTimeout(res, ms));

  const { data: selectedProject }: { data: Project } = useSWR(
    project_id ? [`/api/projects/${project_id}`, accessToken] : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "GET"),
    {
      keepPreviousData: true,
    },
  );

  useEffect(() => {
    if (form.getValues("project_name") === undefined) {
      form.setValue("project_name", selectedProject?.project_name);
    }
  }, [selectedProject]);

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      project_name: undefined,
    },
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
        toast({
          title: "We are creating your project.",
          description: "You will be redirected in a couple seconds.",
        });
        await delay(1000);
        mutate([`/api/organizations/${selectedOrgId}/projects`, accessToken]);
        await delay(1000);
        setproject_id(responseBody.id);
        router.push(`/org`);
      } else {
        toast({
          title: "Error when creating project",
          description: responseBody.error,
        });
      }
    });
  }

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
    let redirect = true; // By default, follow on to the next step

    // Update the project name
    if (values.project_name !== selectedProject?.project_name) {
      // Update the project name
      selectedProject.project_name = values.project_name;
      await fetch(`/api/projects/${project_id}/`, {
        method: "POST",
        headers: {
          Authorization: "Bearer " + accessToken,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(selectedProject),
      }).then(async (response) => {
        mutate(
          [`/api/projects/${project_id}`, accessToken],
          async (data: any) => {
            return { project: project_id };
          },
        );
        // Also mutate the project list
        mutate(
          [`/api/organizations/${selectedOrgId}/projects`, accessToken],
          async (data: any) => {
            // Find the project to edit
            if (!data?.projects) return;
            const index = data.projects.findIndex(
              (project: Project) => project.id === project_id,
            );
            // Replace the project
            data.projects[index] = project_id;
            return { projects: data.projects };
          },
        );
      });
    }

    // Push the file to the server
    if (file !== null) {
      const formData = new FormData();
      formData.set("file", file, file.name);
      try {
        // Call API to upload file
        fetch(`/api/projects/${project_id}/upload-tasks`, {
          method: "POST",
          headers: {
            Authorization: "Bearer " + accessToken,
          },
          body: formData,
        }).then(async (response) => {
          if (response.ok) {
            const responseBody = await response.json();
            const nbRowsProcessed = responseBody.nb_rows_processed;
            const nbRowsDroped = responseBody.nb_rows_dropped;
            if (nbRowsDroped === 0 && nbRowsProcessed > 0) {
              toast({
                title: `Processing ${nbRowsProcessed} rows... ⏳`,
                description: (
                  <div>Data will appear in your dashboard shortly.</div>
                ),
              });
              setRedirecting(false);
              return;
            }
            if (nbRowsDroped > 0 && nbRowsProcessed > 0) {
              toast({
                title: `Processing ${nbRowsProcessed} rows... ⏳`,
                description: (
                  <div>
                    {nbRowsDroped} rows were dropped because the column{" "}
                    <code>input</code> was empty.
                  </div>
                ),
              });
              setRedirecting(false);
              return;
            }
            if (nbRowsProcessed === 0 && nbRowsDroped === 0) {
              toast({
                title: "No data to process 🤷‍♂️",
                description: <div>Please check your file and try again.</div>,
              });
              setRedirecting(false);
              redirect = false;
            }
            if (nbRowsProcessed === 0 && nbRowsDroped > 0) {
              toast({
                title: "No data to process 🤷‍♂️",
                description: (
                  <div>
                    {nbRowsDroped} rows were dropped because the column{" "}
                    <code>input</code> was empty.
                  </div>
                ),
              });
              setRedirecting(false);
              redirect = false;
            }
          } else {
            // Read the error details
            const error = await response.text();
            toast({
              title: "An error occurred",
              description: `${error}`,
            });
            setRedirecting(false);
            redirect = false;
          }
        });
      } catch (error) {
        setRedirecting(false);
        redirect = false;
        console.error("An unexpected error happened:", error);
        toast({
          title: "An error occurred",
          description: `${error}`,
        });
      }
    }

    // Continue to the next onboarding step
    if (redirect) {
      router.push(`/onboarding/customize/${project_id}`);
    }
  }

  if (!user) {
    return <></>;
  }

  if (!selectedProject) {
    return <></>;
  }

  return (
    <>
      <FetchOrgProject />
      <AlertDialog
        onOpenChange={setImportDataDialogOpen}
        open={importDataDialogOpen}
      >
        <SendDataAlertDialog setOpen={setImportDataDialogOpen} />
        <Card className="flex flex-col md:flex-row p-4 items-center space-x-8 space-y-8">
          <div className="w-full">
            <CardHeader>
              <CardTitle>Setup your first phospho project</CardTitle>
              <CardDescription>Let's get you started.</CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col items-left justify-center">
              <Form {...form}>
                <form
                  onSubmit={form.handleSubmit(onSubmit)}
                  className="space-y-8"
                >
                  <FormField
                    control={form.control}
                    name="project_name"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel className="flex flex-row space-x-2">
                          Project name
                          <HoverCard openDelay={0} closeDelay={0}>
                            <HoverCardTrigger>
                              <QuestionMarkIcon className="rounded-full bg-primary text-secondary p-0.5 ml-1" />
                            </HoverCardTrigger>
                            <HoverCardContent>
                              <div className="p-1 flex flex-col space-y-1 text-xs">
                                <div>You can change this later.</div>
                                <div>project_id: {selectedProject.id}</div>
                              </div>
                            </HoverCardContent>
                          </HoverCard>
                        </FormLabel>
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
                  <FormItem>
                    <FormLabel className="flex flex-row space-x-2">
                      Upload a dataset (You can do that later)
                      <HoverCard openDelay={0} closeDelay={0}>
                        <HoverCardTrigger>
                          <QuestionMarkIcon className="rounded-full bg-primary text-secondary p-0.5 ml-1" />
                        </HoverCardTrigger>
                        <HoverCardContent>
                          <div className="p-1 flex flex-col space-y-1 text-xs">
                            <div>
                              No data yet? Click on Continue to skip this step.
                            </div>
                          </div>
                        </HoverCardContent>
                      </HoverCard>
                    </FormLabel>
                    <UploadDatasetButton setFile={setFile} />
                    <Accordion type="single" collapsible className="w-full">
                      <AccordionItem value="instructions">
                        <AccordionTrigger>
                          How to format the dataset?
                        </AccordionTrigger>
                        <AccordionContent>
                          <UploadDatasetInstructions />
                        </AccordionContent>
                      </AccordionItem>
                    </Accordion>

                    <AlertDialogTrigger className="flex justify-end w-full">
                      <div className="underline text-xs">
                        Other data import options
                      </div>
                    </AlertDialogTrigger>
                  </FormItem>

                  <div className="flex justify-end">
                    <Button
                      type="submit"
                      disabled={userLoading || creatingProject}
                      className="w-full"
                    >
                      {redirecting && <Spinner className="mr-1" />}
                      {file && "Upload and continue"}
                      {!file && "Skip (import data later)"}
                    </Button>
                  </div>
                </form>
              </Form>
            </CardContent>
          </div>
          <div className="border-2 rounded-lg border-dashed border-muted-foreground">
            <div>
              <CardHeader className="pb-4">
                <CardTitle>Just looking? Explore a sample project.</CardTitle>
                <CardDescription>
                  Get a feel for phospho by discovering a project with sample
                  data.
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
              <div className="flex justify-center">
                <Button
                  variant="secondary"
                  onClick={() => {
                    defaultProject();
                  }}
                  disabled={userLoading || creatingProject || redirecting}
                >
                  {redirecting && <Spinner className="mr-1" />}
                  Explore sample project
                </Button>
              </div>
            </CardContent>
          </div>
        </Card>
      </AlertDialog>
    </>
  );
}
