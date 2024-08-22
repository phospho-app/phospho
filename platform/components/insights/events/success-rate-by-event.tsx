import { DatePickerWithRange } from "@/components/date-range";
import FilterComponent from "@/components/filters";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { authFetcher } from "@/lib/fetcher";
import { navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import { Filter } from "lucide-react";
import {
  Bar,
  BarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import useSWR from "swr";

interface SuccessRate {
  event_name: string;
  success_rate: number;
}

function SuccessRateByEvent() {
  const { accessToken } = useUser();
  const project_id = navigationStateStore((state) => state.project_id);
  const dataFilters = navigationStateStore((state) => state.dataFilters);

  const {
    data: successRateByEvent,
  }: {
    data: SuccessRate[] | null | undefined;
  } = useSWR(
    project_id
      ? [
          `/api/explore/${project_id}/aggregated/events`,
          accessToken,
          JSON.stringify(dataFilters),
        ]
      : null,
    ([url, accessToken]) =>
      authFetcher(url, accessToken, "POST", {
        metrics: ["success_rate_by_event_name"],
        filters: dataFilters,
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

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-primary shadow-md p-2 rounded-md">
          <p className="text-secondary font-semibold">{`${label}`}</p>
          <p className="text-green-500">
            {`${payload[0].value.toFixed(2)}% success rate`}
          </p>
        </div>
      );
    }

    return null;
  };

  if (successRateByEvent === null) {
    return <></>;
  }

  return (
    <div className="flex flex-col space-y-2">
      <div className="flex flex-row space-x-2 items-center">
        <DatePickerWithRange />
        <FilterComponent variant="tasks" />
      </div>
      <Card className="col-span-full lg:col-span-5">
        <CardHeader>Success Rate (%) by Event</CardHeader>
        <CardContent>
          {successRateByEvent === undefined ? (
            <Skeleton className="h-[250px]" />
          ) : (
            <ResponsiveContainer width="100%" height={150}>
              <BarChart data={successRateByEvent}>
                <XAxis
                  dataKey="tagger_name"
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
                <Tooltip content={CustomTooltip} />
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
