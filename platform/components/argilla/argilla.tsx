"use client";

import CreateDataset from "@/components/argilla/create-argilla-dataset";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
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
          View the documentation{" "}
          <Link
            href={"https://docs.phospho.ai/guides/export-dataset-argilla"}
            className="hover:text-green-500"
          >
            here
          </Link>
          .
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
                  <Button>View your datasets</Button>
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
