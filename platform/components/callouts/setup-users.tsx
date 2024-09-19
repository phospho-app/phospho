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

  const { data: userCountData } = useSWR(
    [`/api/metadata/${project_id}/count/tasks/user_id`, accessToken],
    ([url, accessToken]) => authFetcher(url, accessToken, "GET"),
    {
      keepPreviousData: true,
    },
  );
  const userCount = userCountData?.value;

  return (
    <>
      {userCount === 0 && (
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
                  href="https://docs.phospho.ai/guides/sessions-and-users#users"
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
