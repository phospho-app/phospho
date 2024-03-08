import { Skeleton } from "@/components/ui/skeleton";
import { authFetcher } from "@/lib/fetcher";
import { useUser } from "@propelauth/nextjs/client";
import {
  Bar,
  BarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import useSWR from "swr";

import { Card, CardContent, CardHeader } from "../../ui/card";

interface SuccessRate {
  event_name: string;
  success_rate: number;
}

function SuccessRateByEvent({ project_id }: { project_id: string }) {
  const { accessToken } = useUser();

  const {
    data: successRateByEvent,
  }: {
    data: SuccessRate[] | null | undefined;
  } = useSWR(
    [`/api/explore/${project_id}/aggregated/events`, accessToken],
    ([url, accessToken]) =>
      authFetcher(url, accessToken, "POST", {
        metrics: ["success_rate_by_event_name"],
      }).then((response) => {
        return response?.success_rate_by_event_name?.map((event: any) => {
          // Round the success rate to 2 decimal places
          return {
            event_name: event.event_name,
            success_rate: Math.round(event.success_rate * 10000) / 100,
          };
        });
      }),
    {
      keepPreviousData: true,
    },
  );

  return (
    <div>
      <Card className="col-span-full lg:col-span-5">
        <CardHeader>Success Rate (%) by Event</CardHeader>
        <CardContent>
          {successRateByEvent === null || successRateByEvent === undefined ? (
            <Skeleton className="h-[250px]" />
          ) : (
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={successRateByEvent}>
                <XAxis
                  dataKey="event_name"
                  stroke="#888888"
                  fontSize={12}
                  tickLine={false}
                  axisLine={true}
                />
                <YAxis
                  unit="%"
                  stroke="#888888"
                  fontSize={12}
                  tickLine={false}
                  axisLine={false}
                  tickFormatter={(value) => `${value}`}
                />
                <Tooltip />
                <Bar
                  dataKey="success_rate"
                  fill="#22c55e"
                  radius={[4, 4, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default SuccessRateByEvent;
