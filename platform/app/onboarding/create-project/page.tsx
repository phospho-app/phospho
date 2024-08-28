"use client";

import Authenticate from "@/components/authenticate";
import {
  SendDataAlertDialog,
  UploadDataset,
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
import { Input } from "@/components/ui/input";
import { useToast } from "@/components/ui/use-toast";
import { generateSlug } from "@/lib/utils";
import { navigationStateStore } from "@/store/store";
import { zodResolver } from "@hookform/resolvers/zod";
import { useUser } from "@propelauth/nextjs/client";
import { CloudUpload } from "lucide-react";
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

export default function Page() {
  const router = useRouter();
  const { mutate } = useSWRConfig();
  const toast = useToast();
  const { user, loading, accessToken } = useUser();

  const selectedOrgId = navigationStateStore((state) => state.selectedOrgId);
  const setproject_id = navigationStateStore((state) => state.setproject_id);
  const setSelectedOrgId = navigationStateStore(
    (state) => state.setSelectedOrgId,
  );
  const [creatingProject, setCreatingProject] = useState(false);
  const [redirecting, setRedirecting] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [importDataDialogOpen, setImportDataDialogOpen] = useState(false);

  const delay = (ms: number) => new Promise((res) => setTimeout(res, ms));

  // 1. Define your form.
  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      project_name: generateSlug(false),
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
    });
  }

  // const onSubmit = () => {
  //   if (showModal) {
  //     setShowModal(false);
  //     setButtonPressed(true);
  //   }
  //   if (!file) {
  //     toast({
  //       title: "Please select a file",
  //     });
  //     return;
  //   }
  //   console.log("onSubmit", file);
  //   const formData = new FormData();
  //   formData.set("file", file, file.name);
  //   try {
  //     // Call API to upload file
  //     setLoading(true);
  //     fetch(`/api/projects/${project_id}/upload-tasks`, {
  //       method: "POST",
  //       headers: {
  //         Authorization: "Bearer " + accessToken,
  //         // "Content-Type": "multipart/form-data",
  //       },
  //       body: formData,
  //     }).then(async (response) => {
  //       if (response.ok) {
  //         const responseBody = await response.json();
  //         const nbRowsProcessed = responseBody.nb_rows_processed;
  //         const nbRowsDroped = responseBody.nb_rows_dropped;
  //         if (nbRowsDroped === 0 && nbRowsProcessed > 0) {
  //           toast({
  //             title: `Processing ${nbRowsProcessed} rows... ⏳`,
  //             description: (
  //               <div>Data will appear in your dashboard shortly.</div>
  //             ),
  //           });
  //           setOpen(false);
  //           setLoading(false);
  //           return;
  //         }
  //         if (nbRowsDroped > 0 && nbRowsProcessed > 0) {
  //           toast({
  //             title: `Processing ${nbRowsProcessed} rows... ⏳`,
  //             description: (
  //               <div>
  //                 {nbRowsDroped} rows were dropped because the column{" "}
  //                 <code>input</code> was empty.
  //               </div>
  //             ),
  //           });
  //           setOpen(false);
  //           setLoading(false);
  //           return;
  //         }
  //         if (nbRowsProcessed === 0 && nbRowsDroped === 0) {
  //           toast({
  //             title: "No data to process 🤷‍♂️",
  //             description: <div>Please check your file and try again.</div>,
  //           });
  //           setLoading(false);
  //         }
  //         if (nbRowsProcessed === 0 && nbRowsDroped > 0) {
  //           toast({
  //             title: "No data to process 🤷‍♂️",
  //             description: (
  //               <div>
  //                 {nbRowsDroped} rows were dropped because the column{" "}
  //                 <code>input</code> was empty.
  //               </div>
  //             ),
  //           });
  //           setLoading(false);
  //         }
  //       } else {
  //         // Read the error details
  //         const error = await response.text();
  //         toast({
  //           title: "An error occurred",
  //           description: `${error}`,
  //         });
  //         setLoading(false);
  //       }
  //     });
  //   } catch (error) {
  //     setLoading(false);
  //     console.error("An unexpected error happened:", error);
  //     toast({
  //       title: "An error occurred",
  //       description: `${error}`,
  //     });
  //   }
  // };

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
    });
  }

  if (!user) {
    return <></>;
  }

  return (
    <>
      <FetchOrgProject />
      <Card className="flex flex-col md:flex-row p-4 items-center space-y-4">
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
                <FormItem>
                  <FormLabel>Upload a dataset</FormLabel>
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
                  <AlertDialog
                    onOpenChange={setImportDataDialogOpen}
                    open={importDataDialogOpen}
                  >
                    <AlertDialogTrigger className="flex justify-end w-full">
                      <div className="underline text-xs">
                        Other data import options
                      </div>
                    </AlertDialogTrigger>
                    <SendDataAlertDialog setOpen={setImportDataDialogOpen} />
                  </AlertDialog>
                </FormItem>

                <div className="flex justify-end">
                  <Button
                    type="submit"
                    disabled={loading || creatingProject}
                    className="w-full"
                  >
                    {redirecting && <Spinner className="mr-1" />}
                    Continue
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
                Get a feel for phospho by loading a project with sample data.
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
                variant="secondary"
                onClick={() => {
                  defaultProject();
                }}
                disabled={loading || creatingProject || redirecting}
              >
                {redirecting && <Spinner className="mr-1" />}
                Explore project
              </Button>
            </div>
          </CardContent>
        </div>
      </Card>
    </>
  );
}
