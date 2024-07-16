"use client";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { dataStateStore } from "@/store/store";
import { CircleAlert } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "../ui/card";
import CreatePowerBI from "./create-powerbi-connection";

const PowerBIIntegrations: React.FC = () => {
  const selectedOrgMetadata = dataStateStore(
    (state) => state.selectedOrgMetadata,
  );

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
          <img
            src="/image/power-bi.png"
            alt="PowerBI Logo"
            className="w-5 h-5 mr-2"
          />
          Power BI
        </CardTitle>
        <CardDescription>
          Coming soon: Export data from your project for use in Power BI
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div>
          {isPowerBISetup ? (
            <div>
              <div className="mt-4 flex space-x-4">
                <CreatePowerBI />
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
