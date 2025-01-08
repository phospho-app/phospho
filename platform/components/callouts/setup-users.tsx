import { Button } from "@/components/ui/button";
import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { authFetcher } from "@/lib/fetcher";
import { navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import { HeartHandshake } from "lucide-react";
import Link from "next/link";
import useSWR from "swr";

function SetupUsersCallout() {
  const { accessToken } = useUser();
  const project_id = navigationStateStore((state) => state.project_id);

  // Fetch graph data
  const { data: usersCount }: { data: number | undefined } = useSWR(
    project_id
      ? [`/api/explore/${project_id}/aggregated/users`, accessToken, "nb_users"]
      : null,
    ([url, accessToken]) =>
      authFetcher(url, accessToken, "POST", {
        metrics: ["nb_users"],
      }).then((data) => {
        if (data === undefined) return undefined;
        return data.nb_users;
      }),
    {
      keepPreviousData: true,
    },
  );

  return (
    <>
      {usersCount === 0 && (
        <Card className="bg-secondary">
          <CardHeader>
            <div className="flex">
              <HeartHandshake className="mr-4 h-16 w-16 hover:text-green-500 transition-colors" />
              <div className="flex flex-grow justify-between items-center">
                <div>
                  <CardTitle className="flex flex-row text-2xl font-bold tracking-tight items-center">
                    Analyze user activity
                  </CardTitle>
                  <CardDescription>
                    Group messages by user by adding a <code>user_id</code> in
                    metadata when logging.
                  </CardDescription>
                </div>
                <Link
                  href="https://phospho-app.github.io/docs/guides/sessions-and-users#users"
                  target="_blank"
                >
                  <Button variant="default">Set up user tracking</Button>
                </Link>
              </div>
            </div>
          </CardHeader>
        </Card>
      )}
    </>
  );
}

export { SetupUsersCallout };
