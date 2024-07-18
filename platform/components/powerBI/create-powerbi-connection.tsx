import { Spinner } from "@/components/small-spinner";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { toast } from "@/components/ui/use-toast";
import { PowerBIConnection } from "@/models/models";
import { dataStateStore } from "@/store/store";
import { navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import { Separator } from "@radix-ui/react-dropdown-menu";
import { ChevronRight } from "lucide-react";
import Link from "next/link";
import React from "react";
import { CopyBlock, monoBlue } from "react-code-blocks";

const CreatePowerBI = ({
  credentials,
  project_id,
}: {
  credentials: PowerBIConnection;
  project_id: string;
}) => {
  const { accessToken } = useUser();
  const org_id = navigationStateStore((state) => state.selectedOrgId);
  const orgMetadata = dataStateStore((state) => state.selectedOrgMetadata);

  const handleExport = () => {
    console.log(
      "State: ",
      project_id,
      credentials,
      credentials.projects_started.includes(project_id),
      credentials.projects_finished.includes(project_id),
    );
    if (
      !(
        credentials.projects_started.includes(project_id) ||
        credentials.projects_finished.includes(project_id)
      )
    ) {
      toast({
        title: "Exporting data to a dedicated postgres instance",
        description:
          "We are exporting your data to postgres, this may take a few minutes",
      });
      fetch(`/api/powerbi/${project_id}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${accessToken}`,
        },
      }).then((response) => {
        if (response.ok) {
          toast({
            title: "Export successful",
            description:
              "Your data has been exported to a dedicated postgres instance",
          });
        } else {
          toast({
            title: "Error exporting data",
            description:
              "There was an error exporting your data, please reach out through intercom",
          });
        }
      });
    }
  };

  if (!org_id || !orgMetadata?.power_bi || !project_id || !credentials) {
    return <></>;
  }

  return (
    <Sheet>
      <SheetTrigger>
        <Button className="default" onClick={handleExport}>
          Export data to Power BI
          <ChevronRight className="w-4 h-4 ml-2" />
        </Button>
      </SheetTrigger>
      <SheetContent className="md:w-1/2 overflow-auto">
        <SheetTitle>Export data to Power BI</SheetTitle>
        <SheetDescription>
          Export data from your project for use in your Power BI reports.
        </SheetDescription>
        <Separator className="my-8" />
        <div className="block text-m font-medium">
          Below are the credentials to a dedicated postgres DB that you can use
          to connect your Power BI instance to your project data.
        </div>
        <Separator className="my-2" />
        <div className="block text-m font-medium">
          View the documentation on how to connect Power BI to a PostgreSQL DB{" "}
          <Link href="https://docs.phospho.ai" className="hover:text-green-500">
            here
          </Link>
          .
        </div>
        <Separator className="my-8" />
        <div className="flex flex-col space-y-2">
          <div className="text-xl font-medium">Server</div>
          <CopyBlock
            text={credentials?.server}
            language="text"
            theme={monoBlue}
          />
          <div className="text-xl font-medium">Database</div>
          <CopyBlock
            text={credentials?.database}
            language="text"
            theme={monoBlue}
          />
          <div className="text-xl font-medium">Username</div>
          <CopyBlock
            text={credentials?.username}
            language="text"
            theme={monoBlue}
          />
          <div className="text-xl font-medium">Password</div>
          <CopyBlock
            text={credentials?.password}
            language="text"
            theme={monoBlue}
          />
        </div>

        <Separator className="my-8" />

        <div className="text-m font-medium0">
          Status:{" "}
          {!credentials.projects_finished.includes(project_id) && (
            <div className="flex">
              <Spinner className="w-6 h-6 mr-1" />
              <div>Synchronising data</div>
            </div>
          )}
          {credentials.projects_finished.includes(project_id) && (
            <span className="text-green-500">
              Export complete, we will synchronise your project regularly.
            </span>
          )}
        </div>
      </SheetContent>
    </Sheet>
  );
};

export default CreatePowerBI;
