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
import { ToggleGroup, ToggleGroupItem } from "../ui/toggle-group";

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

const ToggleButton = ({ children }: { children: React.ReactNode }) => {
  return <div className="text-xl flex flex-row space-x-2">{children}</div>;
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
    <AlertDialogContent className="h-3/4 max-w-3/4">
      <AlertDialogHeader>
        <div className="flex justify-between">
          <div>
            <AlertDialogTitle className="text-2xl font-bold tracking-tight mb-1">
              Start sending data to phospho
            </AlertDialogTitle>
            <AlertDialogDescription>
              <p>phospho detects events in the text data of your LLM app.</p>
            </AlertDialogDescription>
          </div>
          <X
            onClick={() => setOpen(false)}
            className="cursor-pointer h-8 w-8"
          />
        </div>
      </AlertDialogHeader>
      <div className="grid grid-cols-5 gap-2 overflow-y-auto">
        <SidebarSendData setOpen={setOpen} />
        <div className="col-span-4 overflow-y-auto space-y-2 flex flex-col justify-between">
          <Card>
            <CardHeader>
              <CardTitle className="text-xl">I need to store logs.</CardTitle>
              <CardDescription>
                What's the programming language of your app?
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
              <CardTitle className="text-xl">I already store logs.</CardTitle>
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
              <CardTitle className="text-xl">
                I don't have an LLM app.
              </CardTitle>
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
