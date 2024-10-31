import { Button } from "@/components/ui/button";
import {
  HoverCard,
  HoverCardContent,
  HoverCardTrigger,
} from "@/components/ui/hover-card";
import { ABTest } from "@/models/models";
import { QuestionMarkIcon } from "@radix-ui/react-icons";
import { ColumnDef } from "@tanstack/react-table";
import { ChevronRight } from "lucide-react";
import Link from "next/link";

import { InteractiveDatetime } from "../interactive-datetime";

export function getColumns() {
  // Create the columns for the data table
  const columns: ColumnDef<ABTest>[] = [
    {
      header: "Start date",
      accessorKey: "first_task_ts",
      cell: ({ row }) => {
        return <InteractiveDatetime timestamp={row.original.first_task_ts} />;
      },
    },
    {
      header: "Last update",
      accessorKey: "last_task_ts",
      cell: ({ row }) => {
        return <InteractiveDatetime timestamp={row.original.last_task_ts} />;
      },
    },
    // version_id
    {
      header: "Version ID",
      accessorKey: "version_id",
      cell: ({ row }) => {
        return <div>{row.original.version_id}</div>;
      },
    },
    // size
    {
      header: "Sample size",
      accessorKey: "nb_tasks",
      cell: ({ row }) => {
        return <div>{row.original.nb_tasks}</div>;
      },
    },
    // name
    {
      header: () => {
        return (
          <div className="md:flex items-center align-items space-x-2">
            <div>Average Human rating</div>
            <HoverCard openDelay={0} closeDelay={0}>
              <HoverCardTrigger>
                <QuestionMarkIcon className="size-4 rounded-full bg-primary text-secondary p-0.5" />
              </HoverCardTrigger>
              <HoverCardContent>
                <div className="w-96">
                  The average human rating (nb of system responses marked as
                  thumbs up)/(total nb of system responses)
                </div>
                <div>Higher is better.</div>
              </HoverCardContent>
            </HoverCard>
          </div>
        );
      },
      accessorKey: "score",
      cell: ({ row }) => {
        const roundedScore = Number((row.original.score * 100).toFixed(2));
        return <div>{roundedScore}%</div>;
      },
    },
    {
      header: () => {
        return (
          <div className="md:flex items-center align-items space-x-2">
            <div>95% Confidence interval</div>
            <HoverCard openDelay={0} closeDelay={0}>
              <HoverCardTrigger>
                <QuestionMarkIcon className="size-4 rounded-full bg-primary text-secondary p-0.5" />
              </HoverCardTrigger>
              <HoverCardContent>
                <div className="w-96">
                  The 95% confidence interval indicates the likely range of the
                  true rating. The smaller the interval, the more confident the
                  estimate.
                </div>
              </HoverCardContent>
            </HoverCard>
          </div>
        );
      },
      accessorKey: "confidence_interval",
      cell: ({ row }) => {
        if (!row.original.confidence_interval) {
          return <div>-</div>;
        }
        const left =
          Math.round(row.original.confidence_interval[0] * 10000) / 100;
        const right =
          Math.round(row.original.confidence_interval[1] * 10000) / 100;
        return (
          <div>
            [{left}%, {right}%]
          </div>
        );
      },
    },
    // description
    {
      header: () => {
        return (
          <div className="md:flex items-center align-items space-x-2">
            <div>Succes Rate Std</div>
            <HoverCard openDelay={0} closeDelay={0}>
              <HoverCardTrigger>
                <QuestionMarkIcon className="size-4 rounded-full bg-primary text-secondary p-0.5" />
              </HoverCardTrigger>
              <HoverCardContent>
                <div className="w-96">
                  The estimated standard deviation of the success rate. Lower is
                  better.
                </div>
              </HoverCardContent>
            </HoverCard>
          </div>
        );
      },
      accessorKey: "score_std",
      cell: ({ row }) => {
        if (!row.original.score_std) {
          return <div>-</div>;
        }
        const roundedStd = Number((row.original.score_std * 100).toFixed(4));
        return <div>{roundedStd}%</div>;
      },
    },
    {
      header: "",
      accessorKey: "view",
      cell: ({ row }) => {
        const abtest_id = row.original.version_id;
        // Match the task object with this key
        // Handle undefined edge case
        if (!abtest_id) return <></>;
        return (
          <Link href={`/org/ab-testing/${encodeURIComponent(abtest_id)}`}>
            <Button variant="ghost" size="icon">
              <ChevronRight />
            </Button>
          </Link>
        );
      },
      size: 10,
      minSize: 10,
      maxSize: 10,
    },
  ];

  return columns;
}
