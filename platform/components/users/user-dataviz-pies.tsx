import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
} from "@/components/ui/card";
import { ChartContainer, ChartTooltip } from "@/components/ui/chart";
import { Skeleton } from "@/components/ui/skeleton";
import { ChevronRight } from "lucide-react";
import Link from "next/link";
import { Pie, PieChart } from "recharts";
import { Label, TooltipProps } from "recharts";
import {
  NameType,
  ValueType,
} from "recharts/types/component/DefaultTooltipContent";

interface DataPoint {
  category: string;
  count: number;
  fill?: string;
}

interface PieChartSectionProps {
  selectedMetric: "jobTitles" | "industry";
  setSelectedMetric: (metric: "jobTitles" | "industry") => void;
  data: DataPoint[] | null | undefined;
  totalCount: number;
}

const CustomTooltip: React.FC<TooltipProps<ValueType, NameType>> = ({
  active,
  payload,
}) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-primary shadow-md p-2 rounded-md">
        <p className="text-secondary font-semibold">{payload[0].name}</p>
        <p className="text-secondary">{payload[0].value} messages</p>
      </div>
    );
  }
  return null;
};

export const PieChartSection: React.FC<PieChartSectionProps> = ({
  selectedMetric,
  setSelectedMetric,
  data,
  totalCount,
}) => {
  console.log("Data: ", data);
  const renderPieChartContent = () => {
    // Loading state
    if (data === undefined) {
      return <Skeleton className="w-[100%] h-[10rem]" />;
    }

    // Empty/null state
    if (data === null) {
      return (
        <div className="flex flex-col text-center items-center h-[10rem] justify-center">
          <p className="text-muted-foreground mb-2 text-sm">
            Add a classifier named{" "}
            <code>
              {selectedMetric === "jobTitles"
                ? "User job title"
                : "User industry"}
            </code>
            <br /> to get started
          </p>
          <Link href="/org/insights/events">
            <Button variant="outline" size="sm">
              Setup analytics
              <ChevronRight className="ml-2 h-4 w-4" />
            </Button>
          </Link>
        </div>
      );
    }

    // Data state
    return (
      <ChartContainer config={{}} className="w-full h-[10rem]">
        <PieChart className="w-full h-[10rem]">
          <ChartTooltip content={CustomTooltip} />
          <Pie
            data={data}
            dataKey="count"
            nameKey="category"
            labelLine={false}
            innerRadius={60}
            outerRadius={70}
          >
            <Label
              content={({ viewBox }) => {
                if (viewBox && "cx" in viewBox && "cy" in viewBox) {
                  return (
                    <text
                      x={viewBox.cx}
                      y={viewBox.cy}
                      textAnchor="middle"
                      dominantBaseline="middle"
                    >
                      <tspan
                        x={viewBox.cx}
                        y={(viewBox.cy || 0) + 5}
                        className="fill-foreground text-3xl font-bold"
                      >
                        {totalCount.toLocaleString()}
                      </tspan>
                      <tspan
                        x={viewBox.cx}
                        y={(viewBox.cy || 0) + 25}
                        className="fill-muted-foreground"
                      >
                        {selectedMetric === "jobTitles"
                          ? "job titles"
                          : "industries"}
                      </tspan>
                    </text>
                  );
                }
              }}
            />
          </Pie>
        </PieChart>
      </ChartContainer>
    );
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex justify-between items-center">
          <CardDescription>
            {selectedMetric === "jobTitles"
              ? "Job Title Distribution"
              : "Industry Distribution"}
          </CardDescription>
          <div className="flex gap-2">
            <Button
              variant={selectedMetric === "jobTitles" ? "default" : "outline"}
              size="sm"
              onClick={() => setSelectedMetric("jobTitles")}
            >
              Job Titles
            </Button>
            <Button
              variant={selectedMetric === "industry" ? "default" : "outline"}
              size="sm"
              onClick={() => setSelectedMetric("industry")}
            >
              Industry
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>{renderPieChartContent()}</CardContent>
    </Card>
  );
};
