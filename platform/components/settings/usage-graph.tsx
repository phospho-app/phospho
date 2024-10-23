import { Button } from "@/components/ui/button";
import {
  ChartConfig,
  ChartContainer,
  ChartTooltip,
} from "@/components/ui/chart";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Skeleton } from "@/components/ui/skeleton";
import { authFetcher } from "@/lib/fetcher";
import { navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import { ChevronDown } from "lucide-react";
import { useState } from "react";
import { Bar, BarChart, TooltipProps, XAxis, YAxis } from "recharts";
import {
  NameType,
  ValueType,
} from "recharts/types/component/DefaultTooltipContent";
import useSWR from "swr";

const chartConfig: ChartConfig = {};

function UsageGraph() {
  const [usageType, setUsageType] = useState("event_detection");
  const validUsageTypes = [
    "event_detection",
    "clustering",
    "sentiment",
    "language",
  ];
  const selectedOrgId = navigationStateStore((state) => state.selectedOrgId);
  const { accessToken } = useUser();

  const { data } = useSWR(
    selectedOrgId
      ? [
          `/api/organizations/${selectedOrgId}/billing-stats`,
          accessToken,
          usageType,
        ]
      : null,
    ([url, accessToken]) =>
      authFetcher(url, accessToken, "POST", {
        usage_type: usageType,
      }),
    {
      refreshInterval: 0,
    },
  );

  const CustomTooltipUsage: React.FC<TooltipProps<ValueType, NameType>> = ({
    active,
    payload,
    label,
  }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-primary shadow-md p-2 rounded-md">
          <p className="text-secondary font-semibold">{label}</p>
          <p className="text-secondary">{`Usage: ${payload[0].value} credits`}</p>
        </div>
      );
    }
    return null;
  };

  return (
    <>
      <div className="flex flex-row gap-x-2 items-center mb-2">
        <h2 className="font-bold">Display usage for: </h2>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" className="min-w-[10rem]">
              <span>{usageType}</span> <ChevronDown className="size-4 ml-2" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            {validUsageTypes.map((type) => (
              <DropdownMenuItem
                key={type}
                onClick={() => {
                  setUsageType(type);
                }}
              >
                {type}
              </DropdownMenuItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
      {data && data.length > 0 && (
        <ChartContainer
          className="w-full h-[14rem] max-w-[40rem]"
          config={chartConfig}
        >
          <BarChart data={data} barGap={0} barCategoryGap={0}>
            <XAxis dataKey="date" />
            <YAxis />
            <ChartTooltip content={CustomTooltipUsage} />
            <Bar
              dataKey="usage"
              fill="#22c55e"
              radius={[4, 4, 0, 0]}
              barSize={20}
            />
          </BarChart>
        </ChartContainer>
      )}
      {(data === null || (data && data.length == 0)) && (
        <div className="w-full h-[14rem] max-w-[40rem] flex items-center justify-center">
          No data available
        </div>
      )}
      {data === undefined && (
        <ChartContainer
          config={chartConfig}
          className="w-full h-[14rem] max-w-[40rem]"
        >
          <Skeleton className="w-full h-[14rem] max-w-[40rem]" />
        </ChartContainer>
      )}
    </>
  );
}

export { UsageGraph };
