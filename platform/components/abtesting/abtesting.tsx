"use client";

// Shadcn ui
import { Button } from "@/components/ui/button";
import {
  HoverCard,
  HoverCardContent,
  HoverCardTrigger,
} from "@/components/ui/hover-card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { authFetcher } from "@/lib/fetcher";
import { ABTest } from "@/models/models";
import { navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import { QuestionMarkIcon } from "@radix-ui/react-icons";
import Link from "next/link";
import React from "react";
import useSWR from "swr";

import { Card, CardDescription, CardHeader, CardTitle } from "../ui/card";

const ABTesting: React.FC = () => {
  const { accessToken } = useUser();
  const project_id = navigationStateStore((state) => state.project_id);

  // Fetch ABTests
  const { data: abTests } = useSWR(
    project_id ? [`/api/explore/${project_id}/ab-tests`, accessToken] : null,
    ([url, accessToken]) =>
      authFetcher(url, accessToken)?.then((res) => {
        const abtests = res.abtests as ABTest[];
        // Round the score and score_std to 2 decimal places
        abtests.forEach((abtest) => {
          abtest.score = Math.round(abtest.score * 10000) / 100;
          abtest.score_std = Math.round(abtest.score_std * 10000) / 100;
        });
        return abtests;
      }),
    {
      keepPreviousData: true,
    },
  );

  return (
    <>
      {(!abTests || (abTests?.length ?? 0) <= 1) && (
        <Card className="bg-secondary">
          <CardHeader>
            <div className="flex justify-between items-center">
              <div>
                <CardTitle className="flex flex-row text-2xl font-bold tracking-tight items-center">
                  Compare versions with AB Testing
                </CardTitle>
                <CardDescription>
                  <div className="text-gray-500">
                    When logging tasks, add a version_id in metadata to compare
                    their success rate.
                  </div>
                </CardDescription>
              </div>
              <Link
                href="https://docs.phospho.ai/guides/ab-test"
                target="_blank"
              >
                <Button>Setup AB Testing</Button>
              </Link>
            </div>
          </CardHeader>
        </Card>
      )}
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Version id</TableHead>
            <TableHead>Sample size</TableHead>
            <TableHead>
              <div className="md:flex items-center align-items ">
                <div className="mr-1">Average Success Rate</div>
                <HoverCard openDelay={50} closeDelay={50}>
                  <HoverCardTrigger>
                    <QuestionMarkIcon className="h-4 w-4 rounded-full bg-primary text-secondary p-0.5" />
                  </HoverCardTrigger>
                  <HoverCardContent>
                    <div>
                      The average success rate is (nb of "success" tasks)/(total
                      nb of tasks).{" "}
                    </div>
                    <div>Higher is better.</div>
                  </HoverCardContent>
                </HoverCard>
              </div>
            </TableHead>
            <TableHead>
              <div className="md:flex items-center align-items ">
                <div className="mr-1">Succes Rate Std</div>
                <HoverCard openDelay={50} closeDelay={50}>
                  <HoverCardTrigger>
                    <QuestionMarkIcon className="h-4 w-4 rounded-full bg-primary text-secondary p-0.5" />
                  </HoverCardTrigger>
                  <HoverCardContent>
                    The estimated standard deviation of the success rate. Lower
                    is better.
                  </HoverCardContent>
                </HoverCard>
              </div>
            </TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {abTests?.map((abttest) => (
            <TableRow key={abttest.version_id}>
              <TableCell>
                <span className="ml-3">{abttest.version_id}</span>
              </TableCell>
              <TableCell>
                <span className="ml-3">{abttest.nb_tasks}</span>
              </TableCell>
              <TableCell>
                <span className="ml-3">{abttest.score} %</span>
              </TableCell>
              <TableCell>
                <span className="ml-3">{abttest.score_std} %</span>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </>
  );
};

export default ABTesting;
