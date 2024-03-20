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
import { ABTest } from "@/models/abtests";
import { navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import { QuestionMarkIcon } from "@radix-ui/react-icons";
import * as Tooltip from "@radix-ui/react-tooltip";
import Link from "next/link";
import React from "react";
import useSWR from "swr";

const ABTesting: React.FC = () => {
  const { accessToken } = useUser();
  const selectedProject = navigationStateStore(
    (state) => state.selectedProject,
  );
  const project_id = selectedProject?.id;

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

  // Handle the case abtests is null
  if (!abTests) {
    return (
      <>
        <div className="flex flex-col justify-center items-center h-full">
          <p className="text-gray-500 mb-4">No AB Tests (yet?)</p>
          <Link href="https://docs.phospho.ai/guides/ab-test" target="_blank">
            <Button variant="outline">Setup AB Testing for your project</Button>
          </Link>
        </div>
      </>
    );
  }
  // if we only have the default version (len = 1) we display this
  if ((abTests?.length ?? 0) <= 1) {
    return (
      <>
        <div className="flex flex-col justify-center items-center h-full">
          <p className="text-gray-500 mb-4">No AB Tests (yet?)</p>
          <Link href="https://docs.phospho.ai/guides/ab-test" target="_blank">
            <Button variant="outline">Setup AB Testing for your project</Button>
          </Link>
        </div>
      </>
    );
  } else {
    return (
      <>
        <h2 className="text-3xl font-bold tracking-tight mb-4">AB Testing</h2>
        <Link href="https://docs.phospho.ai/guides/ab-test" target="_blank">
          <Button variant="link">Read the documentation</Button>
        </Link>
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
                      <QuestionMarkIcon />
                    </HoverCardTrigger>
                    <HoverCardContent>
                      <div>
                        The average success rate is (nb of "success"
                        tasks)/(total nb of tasks).{" "}
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
                      <QuestionMarkIcon />
                    </HoverCardTrigger>
                    <HoverCardContent>
                      The estimated standard deviation of the success rate.
                      Lower is better.
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
  }
};

export default ABTesting;
