import { Button } from "@/components/ui/button";
import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { dataStateStore } from "@/store/store";
import { Boxes } from "lucide-react";
import Link from "next/link";
import React from "react";

export function RunClusteringCallout() {
  const hasTasks = dataStateStore((state) => state.hasTasks);
  const selectedOrgMetadata = dataStateStore(
    (state) => state.selectedOrgMetadata,
  );

  return (
    <>
      {hasTasks === true &&
        (selectedOrgMetadata?.plan === "pro" ||
          selectedOrgMetadata?.plan === "usage_based") && (
          <Card className="bg-secondary">
            <CardHeader>
              <div className="flex">
                <Boxes className="mr-4 h-16 w-16 hover:text-green-500 transition-colors" />

                <div className="flex flex-grow justify-between items-center">
                  <div>
                    <CardTitle className="text-2xl font-bold tracking-tight mb-0">
                      <div className="flex flex-row place-items-center">
                        Discover patterns in your data with clustering
                      </div>
                    </CardTitle>
                    <CardDescription className="flex justify-between">
                      <div className="flex-col text-muted-foreground space-y-0.5">
                        <p>
                          The clustering tool groups your data based on similar
                          features.
                        </p>
                      </div>
                    </CardDescription>
                  </div>
                  <Link href="/org/insights/clusters">
                    <Button variant="default">Cluster data</Button>
                  </Link>
                </div>
              </div>
            </CardHeader>
          </Card>
        )}
    </>
  );
}
