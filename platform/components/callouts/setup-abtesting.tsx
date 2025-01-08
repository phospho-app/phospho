import { Button } from "@/components/ui/button";
import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { authFetcher } from "@/lib/fetcher";
import { ABTest } from "@/models/models";
import { navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import Link from "next/link";
import useSWR from "swr";

function SetupABTestingCallout() {
  const { accessToken } = useUser();
  const project_id = navigationStateStore((state) => state.project_id);

  // Fetch ABTests
  const { data: abTests }: { data: ABTest[] | null | undefined } = useSWR(
    project_id ? [`/api/explore/${project_id}/ab-tests`, accessToken] : null,
    ([url, accessToken]) =>
      authFetcher(url, accessToken).then((res) => {
        if (res === undefined) return undefined;
        if (!res.abtests) return null;
        return res.abtests;
      }),
    {
      keepPreviousData: true,
    },
  );

  return (
    <>
      {abTests && (abTests?.length ?? 0) <= 1 && (
        <Card className="bg-secondary">
          <CardHeader>
            <div className="flex justify-between items-center">
              <div>
                <CardTitle className="flex flex-row text-2xl font-bold tracking-tight items-center">
                  Compare versions with AB Testing
                </CardTitle>
                <CardDescription>
                  <div className="text-muted-foreground">
                    When logging, add a <code>version_id</code> in{" "}
                    <code>metadata</code> to compare their analytics
                    distribution.
                  </div>
                </CardDescription>
              </div>
              <Link
                href="https://phospho-app.github.io/docs/guides/ab-test"
                target="_blank"
              >
                <Button>Setup AB Testing</Button>
              </Link>
            </div>
          </CardHeader>
        </Card>
      )}
    </>
  );
}

export { SetupABTestingCallout };
