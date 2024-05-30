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
import { useRouter } from "next/navigation";

export function getColumns() {
  const router = useRouter();

  // Create the columns for the data table
  const columns: ColumnDef<ABTest>[] = [
    // version_id
    {
      header: "Version ID",
      accessorKey: "version_id",
      cell: ({ row }) => {
        return <>{row.original.version_id}</>;
      },
    },
    // size
    {
      header: "Sample size",
      accessorKey: "nb_tasks",
      cell: ({ row }) => {
        return <>{row.original.nb_tasks}</>;
      },
    },
    // name
    {
      header: ({ column }) => {
        return (
          <div className="md:flex items-center align-items space-x-2">
            <div>Average Success Rate</div>
            <HoverCard openDelay={50} closeDelay={50}>
              <HoverCardTrigger>
                <QuestionMarkIcon className="h-4 w-4 rounded-full bg-primary text-secondary p-0.5" />
              </HoverCardTrigger>
              <HoverCardContent>
                <div>
                  The average success rate is (nb of "success" tasks)/(total nb
                  of tasks).{" "}
                </div>
                <div>Higher is better.</div>
              </HoverCardContent>
            </HoverCard>
          </div>
        );
      },
      accessorKey: "score",
      cell: ({ row }) => {
        return <>{row.original.score}</>;
      },
    },

    // description
    {
      header: ({ column }) => {
        return (
          <div className="md:flex items-center align-items space-x-2">
            <div>Succes Rate Std</div>
            <HoverCard openDelay={50} closeDelay={50}>
              <HoverCardTrigger>
                <QuestionMarkIcon className="h-4 w-4 rounded-full bg-primary text-secondary p-0.5" />
              </HoverCardTrigger>
              <HoverCardContent>
                The estimated standard deviation of the success rate. Lower is
                better.
              </HoverCardContent>
            </HoverCard>
          </div>
        );
      },
      accessorKey: "score_std",
      cell: ({ row }) => {
        return <>{row.original.score_std}</>;
      },
    },

    {
      header: "",
      accessorKey: "view",
      cell: ({ row }) => {
        const topic_id = row.original.version_id;
        // Match the task object with this key
        // Handle undefined edge case
        if (!topic_id) return <></>;
        return (
          <Link href={`/org/ab-testing/${encodeURIComponent(topic_id)}`}>
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
