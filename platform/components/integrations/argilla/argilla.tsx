"use client";

import CreateDataset from "@/components/integrations/argilla/create-argilla-dataset";
import PullDataset from "@/components/integrations/argilla/pull-argilla-dataset";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { authFetcher } from "@/lib/fetcher";
import { OrgMetadata } from "@/models/models";
import { navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import { CircleAlert } from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import { useEffect, useState } from "react";
import useSWR from "swr";

const ArgillaIntegrations: React.FC = () => {
  const selectedOrgId = navigationStateStore((state) => state.selectedOrgId);
  const { accessToken } = useUser();
  const { data: selectedOrgMetadata }: { data: OrgMetadata } = useSWR(
    selectedOrgId
      ? [`/api/organizations/${selectedOrgId}/metadata`, accessToken]
      : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "GET"),
    {
      keepPreviousData: true,
    },
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
          <Image
            src="/image/argilla.png"
            alt="Argilla Logo"
            className="w-10 h-5 mr-2"
            width={40}
            height={20}
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
                <PullDataset />
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
