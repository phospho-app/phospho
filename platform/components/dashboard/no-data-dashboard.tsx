import { Button } from "@/components/ui/button";
import { navigationStateStore } from "@/store/store";
import { ArrowRight, CopyIcon, HelpCircleIcon, TestTube2 } from "lucide-react";
import Link from "next/link";
import { CopyBlock, dracula } from "react-code-blocks";

import {
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "../ui/alert-dialog";
import { Input } from "../ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../ui/tabs";

const SidebarSendData = ({ setOpen }: { setOpen: (open: boolean) => void }) => {
  return (
    <>
      <div className="relative flex flex-col col-span-1">
        <div className="flex-grow"></div>

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

  if (!project_id) {
    return <></>;
  }

  return (
    <AlertDialogContent>
      <AlertDialogHeader>
        <AlertDialogTitle className="text-3xl font-bold tracking-tight mb-1">
          How to send data to phospho?
        </AlertDialogTitle>
        <AlertDialogDescription>
          You log tasks to phospho. We evaluate their success and detect the
          events you set up.
        </AlertDialogDescription>
      </AlertDialogHeader>
      <div className="grid grid-cols-5 gap-2 w-full h-full">
        <SidebarSendData setOpen={setOpen} />
        <div className="col-span-4 overflow-y-auto space-y-4 ">
          <Tabs defaultValue="python">
            <TabsList className="mb-2">
              <TabsTrigger value="python">Python</TabsTrigger>
              <TabsTrigger value="javascript">JavaScript</TabsTrigger>
              <TabsTrigger value="api">API</TabsTrigger>
              <TabsTrigger value="other">Other</TabsTrigger>
            </TabsList>
            <TabsContent value="python" className="flex-col space-y-4">
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
            </TabsContent>
            <TabsContent value="javascript" className="flex-col space-y-4">
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
            </TabsContent>
            <TabsContent value="api" className="flex-col space-y-4">
              <CopyBlock
                text={`curl -X POST https://api.phospho.ai/v2/log/${project_id} \\
-H "Authorization: Bearer $PHOSPHO_API_KEY" \\
-H "Content-Type: application/json" \\
-d '{
    "batched_log_events": [
        {
            "input": "your_input",
            "output": "your_output"
        }
    ]
}'`}
                language={"bash"}
                showLineNumbers={false}
                theme={dracula}
                wrapLongLines={true}
              />
              <APIKeyAndProjectId />
            </TabsContent>
            <TabsContent value="other" className="flex-col space-y-4">
              <p>Discover the full list of integrations.</p>
              <div className="flex space-x-2">
                <Link
                  href="https://docs.phospho.ai/getting-started#how-to-setup-logging"
                  target="_blank"
                >
                  <Button className="w-96">All integrations</Button>
                </Link>
                <Link href="mailto:contact@phospho.app" target="_blank">
                  <Button variant="secondary">Contact us</Button>
                </Link>
              </div>
            </TabsContent>
          </Tabs>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={() => setOpen(false)}>
              Done
            </AlertDialogCancel>
          </AlertDialogFooter>
        </div>
      </div>
    </AlertDialogContent>
  );
};
