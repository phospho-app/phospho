import { Button } from "@/components/ui/button";
import { navigationStateStore } from "@/store/store";
import { ArrowRight, CopyIcon, MonitorPlay, X } from "lucide-react";
import Link from "next/link";
import React from "react";
import { CopyBlock, dracula } from "react-code-blocks";

import {
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "../ui/alert-dialog";
import {
  Card,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "../ui/card";
import { Input } from "../ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../ui/tabs";
import { ToggleGroup, ToggleGroupItem } from "../ui/toggle-group";

const SidebarSendData = ({ setOpen }: { setOpen: (open: boolean) => void }) => {
  return (
    <>
      <div className="flex flex-col col-span-1 justify-end">
        <Button variant="link" className="flex" onClick={() => setOpen(false)}>
          Skip and continue later <ArrowRight className="h-4 w-4 ml-1" />
        </Button>
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
    <div className="flex flex-grow items-center space-x-4">
      <Link
        href={`${process.env.NEXT_PUBLIC_AUTH_URL}/org/api_keys/${selectedOrgId}`}
        target="_blank"
      >
        <Button className="w-96">Create phospho API key</Button>
      </Link>

      <div className="flex flex-grow items-center">
        <span className="w-32">Project id:</span>
        <Input value={project_id}></Input>
        <Button
          variant="outline"
          className="ml-2 p-3"
          onClick={() => {
            navigator.clipboard.writeText(project_id);
          }}
        >
          <CopyIcon size="14" />
        </Button>
      </div>
    </div>
  );
};

export const SendDataAlertDialog = ({
  setOpen,
}: {
  setOpen: (open: boolean) => void;
}) => {
  const selectedOrgId = navigationStateStore((state) => state.selectedOrgId);
  const project_id = navigationStateStore((state) => state.project_id);

  // NULL OR STR VALUE
  const [selectedTab, setSelectedTab] = React.useState<string | undefined>(
    undefined,
  );

  if (!project_id) {
    return <></>;
  }

  return (
    <AlertDialogContent className="w-3/4 h-3/4">
      <AlertDialogHeader>
        <div className="flex justify-between">
          <div>
            <AlertDialogTitle className="text-2xl font-bold tracking-tight mb-1">
              How to send data to phospho?
            </AlertDialogTitle>
            <AlertDialogDescription>
              <p>
                phospho detects events in the text data of your LLM app. We'll
                show you how to get started depending on where you are.
              </p>
            </AlertDialogDescription>
          </div>
          <X
            onClick={() => setOpen(false)}
            className="cursor-pointer h-8 w-8"
          />
        </div>
      </AlertDialogHeader>
      <div className="grid grid-cols-5 gap-2 w-full h-full overflow-auto">
        <SidebarSendData setOpen={setOpen} />
        <div className="col-span-4 overflow-auto overflow-y-auto space-y-4 flex flex-col justify-between">
          <Card>
            <CardHeader>
              <CardTitle>Option 1: I need to start storing logs.</CardTitle>
              <CardDescription>
                What's the programming language of your app?
              </CardDescription>
              <ToggleGroup
                type="single"
                value={selectedTab}
                onValueChange={(value) => setSelectedTab(value)}
                className="justify-start"
              >
                <ToggleGroupItem value="python">Python</ToggleGroupItem>
                <ToggleGroupItem value="javascript">JavaScript</ToggleGroupItem>
                <ToggleGroupItem value="api">API</ToggleGroupItem>
                <ToggleGroupItem value="other">Other</ToggleGroupItem>
              </ToggleGroup>

              {selectedTab == "python" && (
                <div className="flex-col space-y-4">
                  <div className="text-sm">
                    Use the following code snippets to log your app messages to
                    phospho.
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
                    Use the following code snippets to log your app messages to
                    phospho.
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
                    Use the following code snippets to log your app messages to
                    phospho.
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
                    <Link href="mailto:contact@phospho.app" target="_blank">
                      <Button variant="secondary">Contact us</Button>
                    </Link>
                  </div>
                </div>
              )}
            </CardHeader>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Option 2: I'm already storing logs.</CardTitle>
              <CardDescription>
                Coming soon: connect your database to phospho.
              </CardDescription>
              <Link href="mailto:contact@phospho.app" target="_blank">
                <Button variant="outline">Get early access</Button>
              </Link>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Option 3: I don't have an LLM app.</CardTitle>
              <CardDescription>
                Discover what's possible with phospho.
              </CardDescription>
              <div className="flex space-x-2">
                <Link href="https://www.youtube.com/watch?v=yQrRULUEiYM">
                  <Button variant="outline">
                    <MonitorPlay className="h-4 w-4 mr-2" />
                    Watch demo
                  </Button>
                </Link>
                <Link
                  href="https://colab.research.google.com/drive/1Wv9KHffpfHlQCxK1VGvP_ofnMiOGK83Q"
                  target="_blank"
                >
                  <Button variant="outline">Example Colab notebook</Button>
                </Link>
              </div>
            </CardHeader>
          </Card>
        </div>
        <AlertDialogFooter className="col-span-5 justify-end">
          <AlertDialogAction onClick={() => setOpen(false)}>
            Done
          </AlertDialogAction>
        </AlertDialogFooter>
      </div>
    </AlertDialogContent>
  );
};
