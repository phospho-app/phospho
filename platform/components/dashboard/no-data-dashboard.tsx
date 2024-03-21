import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { navigationStateStore } from "@/store/store";
import { CopyIcon, HelpCircleIcon, TestTube2 } from "lucide-react";
import Link from "next/link";
import { CopyBlock, dracula } from "react-code-blocks";

import { Tabs, TabsContent, TabsList, TabsTrigger } from "../ui/tabs";

export const NoDataDashboard = () => {
  const selectedOrgId = navigationStateStore((state) => state.selectedOrgId);
  const project_id = navigationStateStore((state) => state.project_id);

  const LINK_TO_COLAB =
    "https://colab.research.google.com/drive/1Wv9KHffpfHlQCxK1VGvP_ofnMiOGK83Q";

  if (!project_id) {
    return <></>;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-3xl font-bold tracking-tight">
          You're <span className="italic">this</span> close to unique product
          insights.
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div>
          1. Get your API key{" "}
          <a
            className="underline cursor-pointer"
            href={`${process.env.NEXT_PUBLIC_AUTH_URL}/org/api_keys/${selectedOrgId}`}
            // onClick={() => redirectToOrgPage(selectedOrgId)}
          >
            {" "}
            by clicking here
          </a>{" "}
        </div>
        <div className="mt-2">
          2. Your Project id: {project_id}
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
        <div className="mt-2">3. Add phospho in your app:</div>
        <Tabs defaultValue="python">
          <TabsList className="mt-4">
            <TabsTrigger value="python">Python</TabsTrigger>
            <TabsTrigger value="javascript">JavaScript</TabsTrigger>
            <TabsTrigger value="api">API</TabsTrigger>
            <TabsTrigger value="other">Other</TabsTrigger>
          </TabsList>
          <TabsContent value="python">
            <div className="mt-4 shadow border border-gray-300">
              <CopyBlock
                text={`pip install --upgrade phospho`}
                language={"shell"}
                showLineNumbers={false}
                theme={dracula}
              />
            </div>
            <div className="mt-4 shadow border border-gray-300">
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
            </div>
          </TabsContent>
          <TabsContent value="javascript">
            <div className="mt-4 shadow border border-gray-300">
              <CopyBlock
                text={`npm i phospho`}
                language={"shell"}
                showLineNumbers={false}
                theme={dracula}
              />
            </div>
            <div className="mt-4 shadow border border-gray-300">
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
            </div>
          </TabsContent>
          <TabsContent value="api">
            <div className="mt-4 shadow border border-gray-300">
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
            </div>
          </TabsContent>
          <TabsContent value="other">
            <div className=" space-y-2">
              <p>Discover our full list of integrations.</p>
              <div className="flex space-x-2">
                <Link
                  href="https://docs.phospho.ai/getting-started#how-to-setup-logging"
                  target="_blank"
                >
                  <Button>All integrations</Button>
                </Link>
                <Link href="mailto:contact@phospho.app" target="_blank">
                  <Button variant="secondary">Contact us</Button>
                </Link>
              </div>
            </div>
          </TabsContent>
        </Tabs>

        <div className="flex flex-row space-x-4 mt-4">
          <Alert>
            <HelpCircleIcon className="h-4 w-4" />
            <AlertTitle>Something wrong?</AlertTitle>
            <AlertDescription>
              Book a free 30 min session with our dev team.
              <div className="flex flex-row space-x-2">
                <Link href="https://cal.com/nicolas-oulianov" target="_blank">
                  <Button>Book session</Button>
                </Link>
                <Link href="https://discord.gg/MXqBJ9pBsx" target="_blank">
                  <Button variant="secondary">Chat on Discord</Button>
                </Link>
              </div>
            </AlertDescription>
          </Alert>
          <Alert>
            <TestTube2 className="h-4 w-4" />
            <AlertTitle>No app?</AlertTitle>
            <AlertDescription>
              <a className="underline" href={LINK_TO_COLAB} target="_blank">
                Checkout this Colab notebook
              </a>
            </AlertDescription>
          </Alert>
        </div>
      </CardContent>
    </Card>
  );
};
