"use client";

import {
  SendDataAlertDialog,
  UploadDatasetButton,
  UploadDatasetInstructions,
} from "@/components/callouts/import-data";
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
import { UploadIcon } from "lucide-react";
import Image from "next/image";
import { useRouter } from "next/navigation";
import React from "react";
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

interface ProjectData {
  projects: Project[];
}

interface ImportDataOnboardingProps {
  redirecting: boolean;
  setRedirecting: (value: boolean) => void;
  creatingProject: boolean;
  setCreatingProject: (value: boolean) => void;
}

interface ExploreSampleProjectOnboardingProps {
  redirecting: boolean;
  setRedirecting: (value: boolean) => void;
  creatingProject: boolean;
}

const ImportDataOnboarding: React.FC<ImportDataOnboardingProps> = ({
  redirecting,
  setRedirecting,
  creatingProject,
  setCreatingProject,
}) => {
  const selectedOrgId = navigationStateStore((state) => state.selectedOrgId);
  const project_id = navigationStateStore((state) => state.project_id);
  const setSelectedOrgId = navigationStateStore(
    (state) => state.setSelectedOrgId,
  );
  const router = useRouter();
  const { mutate } = useSWRConfig();
  const { toast } = useToast();
  const { user, loading: userLoading, accessToken } = useUser();
  const [file, setFile] = useState<File | null>(null);

  const { data: selectedProject }: { data: Project } = useSWR(
    project_id ? [`/api/projects/${project_id}`, accessToken] : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "GET"),
    {
      keepPreviousData: true,
    },
  );

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      project_name: undefined,
    },
  });

  useEffect(() => {
    if (form.getValues("project_name") === undefined) {
      form.setValue("project_name", selectedProject?.project_name);
    }
  }, [selectedProject, form]);

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
      }).then(async () => {
        mutate([`/api/projects/${project_id}`, accessToken], async () => {
          return { project: project_id };
        });
        // Also mutate the project list
        mutate(
          [`/api/organizations/${selectedOrgId}/projects`, accessToken],
          async (data: ProjectData | undefined) => {
            if (!data?.projects) return;
            const index = data.projects.findIndex(
              (project: Project) => project.id === project_id,
            );
            if (index !== -1 && project_id) {
              const updatedProject: Project = {
                ...data.projects[index],
                id: project_id,
              };
              data.projects[index] = updatedProject;
              return { projects: data.projects };
            }
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

  if (!selectedProject) {
    return (
      <div className="m-4 p-4">
        <Spinner />
      </div>
    );
  }

  return (
    <CardContent className="flex flex-col items-left justify-center w-full">
      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-8">
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
              Upload dataset
              <HoverCard openDelay={0} closeDelay={0}>
                <HoverCardTrigger>
                  <QuestionMarkIcon className="rounded-full bg-primary text-secondary p-0.5 ml-1" />
                </HoverCardTrigger>
                <HoverCardContent>
                  <div className="p-1 flex flex-col space-y-1 text-xs">
                    <div>You can do this later.</div>
                  </div>
                </HoverCardContent>
              </HoverCard>
            </FormLabel>
            <UploadDatasetButton setFile={setFile} />
            <Accordion type="single" collapsible className="w-full">
              <AccordionItem value="instructions">
                <AccordionTrigger>How to format the dataset?</AccordionTrigger>
                <AccordionContent>
                  <UploadDatasetInstructions />
                </AccordionContent>
              </AccordionItem>
            </Accordion>
            <AlertDialogTrigger className="flex justify-end w-full">
              <div className="underline text-xs">Other data import options</div>
            </AlertDialogTrigger>
          </FormItem>

          <div className="flex justify-center">
            <Button
              type="submit"
              disabled={userLoading || creatingProject || !file}
              className="w-full"
            >
              {redirecting && <Spinner className="mr-1" />}
              <UploadIcon className="w-4 h-4 mr-1" />
              Upload and continue
            </Button>
          </div>
        </form>
      </Form>
    </CardContent>
  );
};

const ExploreSampleProjectOnboarding: React.FC<
  ExploreSampleProjectOnboardingProps
> = ({ redirecting, setRedirecting, creatingProject }) => {
  const router = useRouter();
  const { mutate } = useSWRConfig();
  const { toast } = useToast();
  const { user, accessToken, loading: userLoading } = useUser();
  const selectedOrgId = navigationStateStore((state) => state.selectedOrgId);
  const setSelectedOrgId = navigationStateStore(
    (state) => state.setSelectedOrgId,
  );
  const setproject_id = navigationStateStore((state) => state.setproject_id);

  async function defaultProject() {
    if (creatingProject) return;
    if (!accessToken) return;

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
    toast({
      title: "Creating default project",
      description: "Data will be available shortly.",
    });

    fetch(`/api/organizations/${selectedOrgId}/create-default-project`, {
      method: "POST",
      headers: {
        Authorization: "Bearer " + accessToken,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        project_id: null, // This creates a new project. Specify the project_id to update an existing project.
      }),
    }).then(async (response) => {
      const responseBody = await response.json();
      if (responseBody.id !== undefined) {
        mutate([`/api/organizations/${selectedOrgId}/projects`, accessToken]);
        setproject_id(responseBody.id);
      } else {
        toast({
          title: "Error when creating project",
          description: response.statusText,
        });
      }
    });

    setRedirecting(true);
    router.push(`/onboarding/clustering`);
  }

  return (
    <div className="px-4  w-full">
      <div className="border-2 rounded-lg border-dashed border-muted-foreground bg-secondary">
        <CardContent className="space-x-2 flex justify-center flex-row items-center">
          <Image
            src="/image/onboarding.svg"
            alt="Onboarding Image"
            width={160}
            height={120}
          />
          <div className="flex flex-col items-center">
            <CardHeader className="pb-2">
              <CardTitle>No data, just looking?</CardTitle>
              <CardDescription>
                Explore one of the example projects.
              </CardDescription>
            </CardHeader>
            <Button
              variant="outline"
              className="hover:bg-green-500 transition-colors"
              onClick={() => {
                defaultProject();
              }}
              disabled={userLoading || creatingProject || redirecting}
            >
              {redirecting && <Spinner className="mr-1" />}
              Explore example project
            </Button>
          </div>
        </CardContent>
      </div>
    </div>
  );
};

export default function Page() {
  const [creatingProject, setCreatingProject] = useState(false);
  const [redirecting, setRedirecting] = useState(false);
  const [importDataDialogOpen, setImportDataDialogOpen] = useState(false);

  // const searchParams = useSearchParams();
  // const canCode = searchParams.get("code") === "yes";

  return (
    <>
      <AlertDialog
        onOpenChange={setImportDataDialogOpen}
        open={importDataDialogOpen}
      >
        <SendDataAlertDialog setOpen={setImportDataDialogOpen} />
        <Card className="flex flex-col items-center space-y-4 max-w-full md:w-1/2 md:max-w-1/2">
          <CardHeader className="w-full">
            <CardTitle>Create your first phospho project</CardTitle>
            <CardDescription>Let&apos;s get you started.</CardDescription>
          </CardHeader>
          <ImportDataOnboarding
            redirecting={redirecting}
            setRedirecting={setRedirecting}
            creatingProject={creatingProject}
            setCreatingProject={setCreatingProject}
          />
          <ExploreSampleProjectOnboarding
            redirecting={redirecting}
            setRedirecting={setRedirecting}
            creatingProject={creatingProject}
          />
          <div className="h-2"></div>
        </Card>
      </AlertDialog>
    </>
  );
}
