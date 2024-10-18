import { Blockwall } from "@/components/blockwall";
import { DefaultProjects } from "@/components/callouts/default-projects";
import { PasswordInput } from "@/components/password-input";
import { Spinner } from "@/components/small-spinner";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import {
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { AlertDialog } from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import {
  Card,
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
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { useToast } from "@/components/ui/use-toast";
import { authFetcher } from "@/lib/fetcher";
import { OrgMetadata } from "@/models/models";
import { navigationStateStore } from "@/store/store";
import { zodResolver } from "@hookform/resolvers/zod";
import { useUser } from "@propelauth/nextjs/client";
import {
  BarChartBig,
  CloudUpload,
  Lock,
  Mail,
  MonitorPlay,
  NotebookText,
  Telescope,
  Unplug,
  Upload,
  X,
} from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import React, { useEffect, useState } from "react";
import { CopyBlock, dracula } from "react-code-blocks";
import { FileUploader } from "react-drag-drop-files";
import { useForm } from "react-hook-form";
import useSWR from "swr";
import { z } from "zod";

import { CopyButton } from "../copy-button";

const fileTypes = ["csv", "xlsx", "jsonl", "parquet"];

const PythonIcon = () => {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 448 512"
      fill="currentColor"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className="mr-2 w-6 h-6 text-primary"
    >
      <path d="M439.8 200.5c-7.7-30.9-22.3-54.2-53.4-54.2h-40.1v47.4c0 36.8-31.2 67.8-66.8 67.8H172.7c-29.2 0-53.4 25-53.4 54.3v101.8c0 29 25.2 46 53.4 54.3 33.8 9.9 66.3 11.7 106.8 0 26.9-7.8 53.4-23.5 53.4-54.3v-40.7H226.2v-13.6h160.2c31.1 0 42.6-21.7 53.4-54.2 11.2-33.5 10.7-65.7 0-108.6zM286.2 404c11.1 0 20.1 9.1 20.1 20.3 0 11.3-9 20.4-20.1 20.4-11 0-20.1-9.2-20.1-20.4 .1-11.3 9.1-20.3 20.1-20.3zM167.8 248.1h106.8c29.7 0 53.4-24.5 53.4-54.3V91.9c0-29-24.4-50.7-53.4-55.6-35.8-5.9-74.7-5.6-106.8 .1-45.2 8-53.4 24.7-53.4 55.6v40.7h106.9v13.6h-147c-31.1 0-58.3 18.7-66.8 54.2-9.8 40.7-10.2 66.1 0 108.6 7.6 31.6 25.7 54.2 56.8 54.2H101v-48.8c0-35.3 30.5-66.4 66.8-66.4zm-6.7-142.6c-11.1 0-20.1-9.1-20.1-20.3 .1-11.3 9-20.4 20.1-20.4 11 0 20.1 9.2 20.1 20.4s-9 20.3-20.1 20.3z" />
    </svg>
  );
};

const JavaScriptIcon = () => {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 448 512"
      fill="currentColor"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className="mr-2 w-6 h-6 text-primary"
    >
      <path d="M0 32v448h448V32H0zm243.8 349.4c0 43.6-25.6 63.5-62.9 63.5-33.7 0-53.2-17.4-63.2-38.5l34.3-20.7c6.6 11.7 12.6 21.6 27.1 21.6 13.8 0 22.6-5.4 22.6-26.5V237.7h42.1v143.7zm99.6 63.5c-39.1 0-64.4-18.6-76.7-43l34.3-19.8c9 14.7 20.8 25.6 41.5 25.6 17.4 0 28.6-8.7 28.6-20.8 0-14.4-11.4-19.5-30.7-28l-10.5-4.5c-30.4-12.9-50.5-29.2-50.5-63.5 0-31.6 24.1-55.6 61.6-55.6 26.8 0 46 9.3 59.8 33.7L368 290c-7.2-12.9-15-18-27.1-18-12.3 0-20.1 7.8-20.1 18 0 12.6 7.8 17.7 25.9 25.6l10.5 4.5c35.8 15.3 55.9 31 55.9 66.2 0 37.8-29.8 58.6-69.7 58.6z" />
    </svg>
  );
};

const SidebarSendData = () => {
  return (
    <>
      <div className="flex flex-col col-span-1 justify-end">
        {/* <Button variant="link" className="flex" onClick={() => setOpen(false)}>
          Skip and continue later <ArrowRight className="h-4 w-4 ml-1" />
        </Button> */}
      </div>
    </>
  );
};

const APIKeyAndProjectId = () => {
  const selectedOrgId = navigationStateStore((state) => state.selectedOrgId);
  const project_id = navigationStateStore((state) => state.project_id);

  if (!project_id) {
    return <></>;
  }

  return (
    <div className="flex items-center space-x-4">
      <Link
        href={`${process.env.NEXT_PUBLIC_AUTH_URL}/org/api_keys/${selectedOrgId}`}
        target="_blank"
      >
        <Button className="w-96">Create phospho API key</Button>
      </Link>

      <div className="flex items-center">
        <span className="w-32">Project id:</span>
        <Input value={project_id}></Input>
        <CopyButton text={project_id} className="ml-2" />
      </div>
    </div>
  );
};

export function UploadDragAndDrop({
  setFile,
}: {
  setFile: (file: File) => void;
}) {
  const [fileName, setFileName] = React.useState<string | null>(null);

  const handleChange = (file: File) => {
    setFile(file);
    setFileName(file.name);
  };

  return (
    <div className="w-full h-full relative">
      <div className="absolute top-0 w-full h-40 border-2 border-dashed rounded-3xl z-0 text-center flex justify-center items-center">
        <div className="flex flex-col items-center">
          <div>
            <CloudUpload className="w-10 h-10" />
          </div>
          <div className="text-xl font-bold">
            {fileName ?? "Click box or drag here to select file"}
          </div>
          <div className="text-sm text-muted-foreground">
            Supported formats: .csv, .xlsx, .jsonl, .parquet
          </div>
        </div>
      </div>
      <FileUploader
        handleChange={handleChange}
        name="file"
        types={fileTypes}
        hoverTitle=""
      >
        <div className="h-40 flex flex-col items-center cursor-pointer z-20"></div>
      </FileUploader>
    </div>
  );
}

export function UploadDatasetInstructions() {
  return (
    <div className="text-wrap">
      <div className="text-sm mb-1">
        The file should contain text data with the following columns:{" "}
        <code>input</code>, <code>output</code>.
      </div>
      <div className="text-sm mb-1">
        <span>Other columns are optional (look at the example below). </span>
        <a
          href="/files/example_csv_phospho.csv"
          download="example_csv_phospho"
          className="underline"
        >
          Download example CSV
        </a>
      </div>
      <CopyBlock
        text={`input;output;task_id;session_id;user_id;created_at
"What's the capital of France?";"The capital of France is Paris";task_1;session_1;user_bob;"2021-09-01 12:00:00"`}
        language={"text"}
        showLineNumbers={true}
        theme={dracula}
        wrapLongLines={true}
      />
    </div>
  );
}

export function UploadDataset({
  setOpen,
  showModal,
  setShowModal,
  setButtonPressed,
}: {
  setOpen: (open: boolean) => void;
  showModal: boolean;
  setShowModal: (modal: boolean) => void;
  setButtonPressed: (buttonPressed: boolean) => void;
}) {
  const { toast } = useToast();
  const { accessToken } = useUser();
  const project_id = navigationStateStore((state) => state.project_id);
  const setDateRangePreset = navigationStateStore(
    (state) => state.setDateRangePreset,
  );

  const [loading, setLoading] = useState(false);
  const [file, setFile] = useState<File | null>(null);

  const onSubmit = () => {
    setDateRangePreset("all-time");
    if (showModal) {
      setShowModal(false);
      setButtonPressed(true);
    }
    if (!file) {
      toast({
        title: "Please select a file",
      });
      return;
    }
    const formData = new FormData();
    formData.set("file", file, file.name);
    try {
      // Call API to upload file
      setLoading(true);
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
            setOpen(false);
            setLoading(false);
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
            setOpen(false);
            setLoading(false);
            return;
          }
          if (nbRowsProcessed === 0 && nbRowsDroped === 0) {
            toast({
              title: "No data to process 🤷‍♂️",
              description: <div>Please check your file and try again.</div>,
            });
            setLoading(false);
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
            setLoading(false);
          }
        } else {
          // Read the error details
          const error = await response.text();
          toast({
            title: "An error occurred",
            description: `${error}`,
          });
          setLoading(false);
        }
      });
    } catch (error) {
      setLoading(false);
      console.error("An unexpected error happened:", error);
      toast({
        title: "An error occurred",
        description: `${error}`,
      });
    }
  };

  return (
    <div className="flex flex-col gap-y-2">
      <UploadDatasetInstructions />
      <UploadDragAndDrop setFile={setFile} />
      {file !== null && !loading && (
        <Button onClick={onSubmit}>
          Send file
          <Upload className="ml-1 w-4 h-4" />
        </Button>
      )}

      {loading && (
        <Button disabled>
          Uploading...
          <Spinner className="ml-1" />
        </Button>
      )}
    </div>
  );
}

const ToggleButton = ({ children }: { children: React.ReactNode }) => {
  return <div className="text-xl flex flex-row space-x-2">{children}</div>;
};

export const SendDataAlertDialog = ({
  setOpen,
  exampleProjects = true,
}: {
  setOpen: (open: boolean) => void;
  exampleProjects?: boolean;
}) => {
  const { accessToken } = useUser();
  const toast = useToast();
  const router = useRouter();

  const project_id = navigationStateStore((state) => state.project_id);
  const selectedOrgId = navigationStateStore((state) => state.selectedOrgId);

  const { data: selectedOrgMetadata }: { data: OrgMetadata } = useSWR(
    selectedOrgId
      ? [`/api/organizations/${selectedOrgId}/metadata`, accessToken]
      : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "GET"),
    {
      keepPreviousData: true,
    },
  );

  const [showModal, setShowModal] = useState(true);
  const [disableLF, setDisableLF] = useState(false);
  const [disableLS, setDisableLS] = useState(false);
  const [buttonPressed, setButtonPressed] = useState(false);
  const [selectedTab, setSelectedTab] = useState<string | undefined>(undefined);

  useEffect(() => {
    setShowModal(selectedOrgMetadata?.plan === "hobby");
  }, [selectedOrgMetadata?.plan]);

  const formSchemaLS = z.object({
    langsmith_api_key: z
      .string()
      .min(50, {
        message: "Your API key should be longer than 50 characters.",
      })
      .max(60, {
        message: "Your API key should be shorter than 60 characters.",
      }),
    langsmith_project_name: z
      .string()
      .min(2, {
        message: "Project name should be at least 2 characters.",
      })
      .max(32, {
        message: "Project name should be at most 30 characters.",
      }),
  });

  const formLS = useForm<z.infer<typeof formSchemaLS>>({
    resolver: zodResolver(formSchemaLS),
  });

  const formSchemaLF = z.object({
    langfuse_secret_key: z
      .string()
      .min(35, {
        message: "Your secret key should be longer than 35 characters.",
      })
      .max(50, {
        message: "Your secret key should be shorter than 50 characters.",
      }),
    langfuse_public_key: z
      .string()
      .min(35, {
        message: "Your public key should be at least 35 characters.",
      })
      .max(50, {
        message: "Your public key should be at most 50 characters.",
      }),
  });

  const formLF = useForm<z.infer<typeof formSchemaLF>>({
    resolver: zodResolver(formSchemaLF),
  });

  async function onLangSmithSubmit(values: z.infer<typeof formSchemaLS>) {
    setDisableLS(true);
    fetch(`/api/projects/${project_id}/connect-langsmith`, {
      method: "POST",
      headers: {
        Authorization: "Bearer " + accessToken,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        langsmith_project_name: values.langsmith_project_name,
        langsmith_api_key: values.langsmith_api_key,
      }),
    }).then(async (response) => {
      await response.json();
      if (response.ok) {
        setDisableLS(false);
        if (showModal) {
          setButtonPressed(true);
          setShowModal(false);
        }
        toast.toast({
          title: "🦜🔗 LangSmith import successful",
          description: "Your data is being imported to phospho.",
        });
        setOpen(false);
      } else {
        setDisableLS(false);
        toast.toast({
          title: "🦜🔗 LangSmith import failed",
          description:
            "Please double-check your LangSmith API key and project name",
        });
      }
    });
  }

  async function onLangFuseSubmit(values: z.infer<typeof formSchemaLF>) {
    setDisableLF(true);
    fetch(`/api/projects/${project_id}/connect-langfuse`, {
      method: "POST",
      headers: {
        Authorization: "Bearer " + accessToken,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        langfuse_public_key: values.langfuse_public_key,
        langfuse_secret_key: values.langfuse_secret_key,
      }),
    }).then(async (response) => {
      await response.json();
      if (response.ok) {
        setDisableLF(false);
        if (showModal) {
          setButtonPressed(true);
          setShowModal(false);
        }
        toast.toast({
          title: "🪢 LangFuse import successful",
          description: "Your data is being imported to phospho.",
        });
        setOpen(false);
      } else {
        setDisableLF(false);
        toast.toast({
          title: "🪢 LangFuse import failed",
          description:
            "Please double-check your LangFuse public and secret keys",
        });
      }
    });
  }

  function handleClose() {
    if (showModal) {
      setShowModal(false);
      setButtonPressed(true);
    } else {
      setOpen(false);
    }
  }

  function handleSkip() {
    setOpen(false);
    setButtonPressed(false);
    setShowModal(false);
  }

  if (!project_id) {
    return <></>;
  }

  return (
    <>
      {!buttonPressed && (
        <AlertDialogContent className="md:h-3/4 md:max-w-3/4">
          <AlertDialogHeader>
            <div className="flex justify-between">
              <div>
                <AlertDialogTitle className="text-2xl font-bold tracking-tight mb-1">
                  Send data to phospho
                </AlertDialogTitle>
                <AlertDialogDescription>
                  <p>phospho needs text data to generate insights.</p>
                </AlertDialogDescription>
              </div>
              <X onClick={handleClose} className="cursor-pointer h-8 w-8" />
            </div>
          </AlertDialogHeader>
          <div className="overflow-y-auto">
            <SidebarSendData />
            <div className="space-y-2 flex flex-col">
              <Card>
                <CardHeader>
                  <CardTitle className="text-xl">
                    I already store messages.
                  </CardTitle>
                  <CardDescription>
                    Push your historical data to phospho
                  </CardDescription>
                  <ToggleGroup
                    type="single"
                    value={selectedTab}
                    onValueChange={(value) => setSelectedTab(value)}
                    className="justify-start"
                  >
                    <ToggleGroupItem value="upload">
                      <ToggleButton>
                        <Upload className="mr-2 w-6 h-6" /> Upload dataset
                      </ToggleButton>
                    </ToggleGroupItem>
                    <ToggleGroupItem value="lang_smith">
                      <ToggleButton>🦜🔗 LangSmith</ToggleButton>
                    </ToggleGroupItem>
                    <ToggleGroupItem value="lang_fuse">
                      <ToggleButton>🪢 LangFuse</ToggleButton>
                    </ToggleGroupItem>
                    <ToggleGroupItem value="other_bottom">
                      <ToggleButton>Other</ToggleButton>
                    </ToggleGroupItem>
                  </ToggleGroup>

                  {selectedTab == "upload" && (
                    <div className="flex-col space-y-4">
                      <UploadDataset
                        setOpen={setOpen}
                        showModal={showModal}
                        setShowModal={setShowModal}
                        setButtonPressed={setButtonPressed}
                      />
                    </div>
                  )}

                  {selectedTab == "lang_smith" && (
                    <div className="flex-col space-y-4">
                      <div className="text-sm">
                        Synchronise your data from LangSmith to phospho. We will
                        fetch the data periodically.
                      </div>
                      <Form {...formLS}>
                        <form
                          onSubmit={formLS.handleSubmit(onLangSmithSubmit)}
                          className="space-y-8"
                        >
                          <FormField
                            control={formLS.control}
                            name="langsmith_api_key"
                            render={({ field }) => (
                              <FormItem>
                                <FormLabel>
                                  Your LangSmith API key,{" "}
                                  <Link
                                    className="underline hover:text-green-500"
                                    href="https://docs.smith.langchain.com/how_to_guides/setup/create_account_api_key#api-keys"
                                  >
                                    learn more here
                                  </Link>
                                </FormLabel>
                                <div className="flex justify-center">
                                  <HoverCard openDelay={80} closeDelay={30}>
                                    <HoverCardTrigger>
                                      <Lock className="mr-2 mt-2" />
                                    </HoverCardTrigger>
                                    <HoverCardContent
                                      side="top"
                                      className="text-sm text-center"
                                    >
                                      <div>
                                        This key is encrypted and stored
                                        securely.
                                      </div>
                                      <div>
                                        We only use it to fetch your data from
                                        LangSmith.
                                      </div>
                                    </HoverCardContent>
                                  </HoverCard>

                                  <FormControl>
                                    <PasswordInput
                                      placeholder="lsv2_..."
                                      {...field}
                                      className="font-normal flex"
                                    />
                                  </FormControl>
                                </div>
                                <FormMessage />
                              </FormItem>
                            )}
                          />
                          <FormField
                            control={formLS.control}
                            name="langsmith_project_name"
                            render={({ field }) => (
                              <FormItem>
                                <FormLabel>LangSmith project name</FormLabel>
                                <FormControl>
                                  <Input
                                    placeholder="My LangSmith project"
                                    {...field}
                                    className="font-normal"
                                  />
                                </FormControl>
                                <FormMessage />
                              </FormItem>
                            )}
                          />
                          <div className="flex justify-end">
                            <Button
                              type="submit"
                              disabled={!formLS.formState.isValid || disableLS}
                            >
                              {disableLS && <Spinner className="mr-1" />}
                              Transfer data from LangSmith
                            </Button>
                          </div>
                        </form>
                      </Form>
                    </div>
                  )}

                  {selectedTab == "lang_fuse" && (
                    <div className="flex-col space-y-4">
                      <div className="text-sm">
                        Synchronise your data from LangFuse to phospho. We will
                        fetch the data periodically.
                      </div>
                      <Form {...formLF}>
                        <form
                          onSubmit={formLF.handleSubmit(onLangFuseSubmit)}
                          className="space-y-8"
                        >
                          <FormField
                            control={formLF.control}
                            name="langfuse_secret_key"
                            render={({ field }) => (
                              <FormItem>
                                <FormLabel>
                                  Your LangFuse secret key,{" "}
                                  <Link
                                    className="underline hover:text-green-500"
                                    href="https://cloud.langfuse.com/"
                                  >
                                    go to LangFuse -&gt; Settings -&gt; Create
                                    new API keys
                                  </Link>
                                </FormLabel>
                                <div className="flex justify-center">
                                  <HoverCard openDelay={80} closeDelay={30}>
                                    <HoverCardTrigger>
                                      <Lock className="mr-2 mt-2" />
                                    </HoverCardTrigger>
                                    <HoverCardContent
                                      side="top"
                                      className="text-sm text-center"
                                    >
                                      <div>
                                        This key is encrypted and stored
                                        securely.
                                      </div>
                                      <div>
                                        We only use it to fetch your data from
                                        LangFuse.
                                      </div>
                                    </HoverCardContent>
                                  </HoverCard>

                                  <FormControl>
                                    <PasswordInput
                                      placeholder="sk-lf-..."
                                      {...field}
                                      className="font-normal flex"
                                    />
                                  </FormControl>
                                </div>
                                <FormMessage />
                              </FormItem>
                            )}
                          />
                          <FormField
                            control={formLF.control}
                            name="langfuse_public_key"
                            render={({ field }) => (
                              <FormItem>
                                <FormLabel>Your LangFuse public key</FormLabel>
                                <FormControl>
                                  <Input
                                    placeholder="pk-lf-..."
                                    {...field}
                                    className="font-normal"
                                  />
                                </FormControl>
                                <FormMessage />
                              </FormItem>
                            )}
                          />
                          <div className="flex justify-end">
                            <Button
                              type="submit"
                              disabled={!formLF.formState.isValid || disableLF}
                            >
                              {disableLF && <Spinner className="mr-1" />}
                              Transfer data from LangFuse
                            </Button>
                          </div>
                        </form>
                      </Form>
                    </div>
                  )}

                  {selectedTab == "other_bottom" && (
                    <div className="flex-col space-y-4">
                      <div className="flex space-x-2">
                        <Link
                          href="https://docs.phospho.ai/getting-started#how-to-setup-logging"
                          target="_blank"
                        >
                          <Button className="w-96">
                            Discover all integrations
                          </Button>
                        </Link>
                        <Link href="mailto:contact@phospho.ai" target="_blank">
                          <Button variant="secondary">Contact us</Button>
                        </Link>
                      </div>
                    </div>
                  )}
                </CardHeader>
              </Card>
              <Card>
                <CardHeader>
                  <CardTitle className="text-xl">
                    I need to log messages.
                  </CardTitle>
                  <CardDescription>
                    What&apos;s your app&apos;s backend language?
                  </CardDescription>
                  <ToggleGroup
                    type="single"
                    value={selectedTab}
                    onValueChange={(value) => setSelectedTab(value)}
                    className="justify-start"
                  >
                    <ToggleGroupItem value="python">
                      <ToggleButton>
                        <PythonIcon />
                        Python
                      </ToggleButton>
                    </ToggleGroupItem>
                    <ToggleGroupItem value="javascript">
                      <ToggleButton>
                        <JavaScriptIcon />
                        JavaScript
                      </ToggleButton>
                    </ToggleGroupItem>
                    <ToggleGroupItem value="api">
                      <ToggleButton>API</ToggleButton>
                    </ToggleGroupItem>
                    <ToggleGroupItem value="other">
                      <ToggleButton>Other</ToggleButton>
                    </ToggleGroupItem>
                  </ToggleGroup>

                  {selectedTab == "python" && (
                    <div className="flex-col space-y-4">
                      <div className="text-sm">
                        Use the following code snippets to log your app messages
                        to phospho.
                      </div>
                      <CopyBlock
                        text={`pip install --upgrade phospho`}
                        language={"shell"}
                        showLineNumbers={false}
                        theme={dracula}
                      />
                      <CopyBlock
                        text={`import phospho
              
phospho.init(api_key="YOUR_API_KEY", project_id="${project_id}")

input_str = "Hello! This is what the user asked to the system"
output_str = "This is the response showed to the user by the app."
phospho.log(input=input_str, output=output_str)`}
                        language={"python"}
                        showLineNumbers={false}
                        theme={dracula}
                        wrapLongLines={true}
                      />
                      <APIKeyAndProjectId />
                    </div>
                  )}
                  {selectedTab == "javascript" && (
                    <div className="flex-col space-y-4">
                      <div className="text-sm">
                        Use the following code snippets to log your app messages
                        to phospho.
                      </div>
                      <CopyBlock
                        text={`npm i phospho`}
                        language={"shell"}
                        showLineNumbers={false}
                        theme={dracula}
                      />
                      <CopyBlock
                        text={`import { phospho } from "phospho";

phospho.init({apiKey: "YOUR_API_KEY", projectId: "${project_id}"});

const input = "Hello! This is what the user asked to the system";
const output = "This is the response showed to the user by the app.";
phospho.log({input, output});`}
                        language={"javascript"}
                        showLineNumbers={false}
                        theme={dracula}
                        wrapLongLines={true}
                      />
                      <APIKeyAndProjectId />
                    </div>
                  )}
                  {selectedTab == "api" && (
                    <div className="flex-col space-y-4">
                      <div className="text-sm">
                        Use the following code snippets to log your app messages
                        to phospho.
                      </div>
                      <CopyBlock
                        text={`curl -X POST https://api.phospho.ai/v2/log/${project_id} \\
-H "Authorization: Bearer $PHOSPHO_API_KEY" \\
-H "Content-Type: application/json" \\
-d '{"batched_log_events": [
      {"input": "your_input", "output": "your_output"}
]}'`}
                        language={"bash"}
                        showLineNumbers={false}
                        theme={dracula}
                        wrapLongLines={true}
                      />
                      <APIKeyAndProjectId />
                    </div>
                  )}
                  {selectedTab == "other" && (
                    <div className="flex-col space-y-4">
                      <div className="flex space-x-2">
                        <Link
                          href="https://docs.phospho.ai/getting-started#how-to-setup-logging"
                          target="_blank"
                        >
                          <Button className="w-96">
                            Discover all integrations
                          </Button>
                        </Link>
                        <Link href="mailto:contact@phospho.ai" target="_blank">
                          <Button variant="secondary">Contact us</Button>
                        </Link>
                      </div>
                    </div>
                  )}
                </CardHeader>
              </Card>
              <Alert>
                <AlertTitle className="text-sm">
                  I don&apos;t have an LLM app
                </AlertTitle>
                <AlertDescription className="flex flex-row items-center">
                  <Link href="https://www.youtube.com/watch?v=4QeNPa4xOc8">
                    <Button variant="ghost" className="text-xs">
                      <MonitorPlay className="h-4 w-4 mr-2" />
                      Watch demo
                    </Button>
                  </Link>
                  <Link
                    href="https://colab.research.google.com/drive/1Wv9KHffpfHlQCxK1VGvP_ofnMiOGK83Q"
                    target="_blank"
                  >
                    <Button variant="ghost" className="text-xs">
                      <NotebookText className="h-4 w-4 mr-2" />
                      Example Colab notebook
                    </Button>
                  </Link>
                  {exampleProjects && (
                    <AlertDialog>
                      <AlertDialogTrigger asChild>
                        <Button variant="ghost" className="text-xs">
                          <Telescope className="h-4 w-4 mr-2" /> Explore sample
                          data
                        </Button>
                      </AlertDialogTrigger>
                      <DefaultProjects
                        handleClose={handleClose}
                        setOpen={setOpen}
                      />
                    </AlertDialog>
                  )}
                  <Button
                    variant="ghost"
                    className="text-xs"
                    onClick={() => router.push("mailto:paul-louis@phospho.ai")}
                  >
                    <Mail className="h-4 w-4 mr-2" />
                    Contact us to create your LLM app
                  </Button>
                </AlertDescription>
              </Alert>
            </div>
          </div>
        </AlertDialogContent>
      )}
      {buttonPressed && Blockwall({ handleSkip })}
    </>
  );
};

export const SendDataCallout = () => {
  const { accessToken } = useUser();
  const project_id = navigationStateStore((state) => state.project_id);
  const [open, setOpen] = React.useState(false);

  const { data: hasTasksData } = useSWR(
    project_id ? [`/api/explore/${project_id}/has-tasks`, accessToken] : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "POST"),
    { keepPreviousData: true },
  );
  const hasTasks: boolean = hasTasksData?.has_tasks ?? false;

  return (
    <>
      {hasTasks === false && (
        <Card className="bg-secondary">
          <CardHeader>
            <div className="flex">
              <Unplug className="mr-4 h-16 w-16 hover:text-green-500 transition-colors" />
              <div className="flex flex-grow justify-between items-center">
                <div>
                  <CardTitle className="text-2xl font-bold tracking-tight mb-0">
                    Send data to phospho
                  </CardTitle>
                  <CardDescription className="flex justify-between">
                    We&apos;ll show you how to get started
                  </CardDescription>
                </div>
                <AlertDialog open={open}>
                  <Button
                    variant="default"
                    onClick={() => {
                      setOpen(true);
                    }}
                  >
                    Start sending data
                  </Button>
                  <SendDataAlertDialog setOpen={setOpen} />
                </AlertDialog>
              </div>
            </div>
          </CardHeader>
        </Card>
      )}
    </>
  );
};

export const DatavizCallout = () => {
  const { accessToken } = useUser();
  const project_id = navigationStateStore((state) => state.project_id);

  const { data: hasTasksData } = useSWR(
    project_id ? [`/api/explore/${project_id}/has-tasks`, accessToken] : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "POST"),
    { keepPreviousData: true },
  );
  const hasTasks: boolean = hasTasksData?.has_tasks ?? false;

  const [open, setOpen] = React.useState(false);

  return (
    <>
      {hasTasks === false && (
        <Card className="bg-secondary">
          <CardHeader>
            <div className="flex">
              <BarChartBig className="mr-4 h-16 w-16 hover:text-green-500 transition-colors" />
              <div className="flex flex-grow justify-between items-center">
                <div>
                  <CardTitle className="text-2xl font-bold tracking-tight mb-0">
                    Visualize your augmented data
                  </CardTitle>
                  <CardDescription className="flex justify-between">
                    Quickly make plots and graphs with your data.
                  </CardDescription>
                </div>
                <AlertDialog open={open}>
                  <Button
                    variant="default"
                    onClick={() => {
                      setOpen(true);
                    }}
                  >
                    Start sending data
                  </Button>
                  <SendDataAlertDialog setOpen={setOpen} />
                </AlertDialog>
              </div>
            </div>
          </CardHeader>
        </Card>
      )}
    </>
  );
};
