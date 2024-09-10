"use client";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { dataStateStore } from "@/store/store";
import { navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import { CircleAlert } from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import { useEffect, useState } from "react";

import CreatePowerBI from "./create-powerbi-connection";

const PowerBIIntegrations: React.FC = () => {
  const selectedOrgMetadata = dataStateStore(
    (state) => state.selectedOrgMetadata,
  );
  const org_id = navigationStateStore((state) => state.selectedOrgId);
  const project_id = navigationStateStore((state) => state.project_id);

  const { accessToken } = useUser();

  // If the selectedOrgMetadata.argilla_worspace_id exists and is not null, then Argilla is set up
  const [isPowerBISetup, setIsPowerBISetup] = useState<boolean>(false);

  useEffect(() => {
    if (selectedOrgMetadata?.power_bi) {
      setIsPowerBISetup(true);
    }
  }, [selectedOrgMetadata?.power_bi]);

  // Let's add a logo on the left side of the CardTitle
  return (
    <Card className="mt-2">
      <CardHeader>
        <CardTitle className="flex">
          <Image
            src="/image/power-bi.png"
            alt="PowerBI Logo"
            className="w-5 h-5 mr-2"
            width={40}
            height={20}
          />
          Power BI
        </CardTitle>
        <CardDescription>Export your project data to Power BI.</CardDescription>
      </CardHeader>
      <CardContent>
        <div>
          {isPowerBISetup && project_id ? (
            <div>
              <div className="mt-4 flex space-x-4">
                <CreatePowerBI project_id={project_id} />
              </div>
            </div>
          ) : (
            <div>
              <Alert>
                <CircleAlert />
                <AlertTitle>
                  This feature is not enabled for your organization
                </AlertTitle>
                <AlertDescription>
                  Contact us at{" "}
                  <Link href="mailto:contact@phospho.ai" className="underline">
                    contact@phospho.ai
                  </Link>{" "}
                  to get access.
                </AlertDescription>
              </Alert>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

export default PowerBIIntegrations;
