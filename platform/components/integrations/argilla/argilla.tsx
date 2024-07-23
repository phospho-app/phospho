"use client";

import CreateDataset from "@/components/integrations/argilla/create-argilla-dataset";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { dataStateStore } from "@/store/store";
import { CircleAlert } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

const ArgillaIntegrations: React.FC = () => {
  const selectedOrgMetadata = dataStateStore(
    (state) => state.selectedOrgMetadata,
  );

  // If the selectedOrgMetadata.argilla_worspace_id exists and is not null, then Argilla is set up
  const [isArgillaSetup, setIsArgillaSetup] = useState<boolean>(false);

  useEffect(() => {
    if (selectedOrgMetadata?.argilla_workspace_id) {
      setIsArgillaSetup(true);
    }
  }, [selectedOrgMetadata?.argilla_workspace_id]);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex">
          <img
            src="/image/argilla.png"
            alt="Argilla Logo"
            className="w-10 h-5 mr-2"
          />
          Argilla
        </CardTitle>
        <CardDescription>
          Learn more about the Argilla labelling platform{" "}
          <Link
            href={
              "https://docs.argilla.io/en/latest/practical_guides/practical_guides.html"
            }
            className="underline"
          >
            here
          </Link>
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div>
          {isArgillaSetup ? (
            <div>
              <div className="mt-4 flex space-x-4">
                <Link
                  href={
                    process.env.NEXT_PUBLIC_ARGILLA_URL ||
                    "https://argilla.phospho.ai"
                  }
                  target="_blank"
                >
                  <Button>View datasets</Button>
                </Link>
                <CreateDataset />
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

export default ArgillaIntegrations;
