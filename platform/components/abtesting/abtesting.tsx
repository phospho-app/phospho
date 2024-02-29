"use client";

import { dataStateStore } from "@/store/store";
import { QuestionMarkIcon } from "@radix-ui/react-icons";
import * as Tooltip from "@radix-ui/react-tooltip";
import Link from "next/link";
import React from "react";

import { Button } from "../ui/button";
// Shadcn ui
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../ui/table";

const ABTesting: React.FC = () => {
  const abTests = dataStateStore((state) => state.abTests);

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

        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Version id</TableHead>
              <TableHead>Sample size</TableHead>
              <TableHead>
                <div className="md:flex items-center align-items ">
                  <div className="mr-1">Average Success Rate</div>
                  <Tooltip.Provider>
                    <Tooltip.Root>
                      <Tooltip.Trigger asChild>
                        <QuestionMarkIcon />
                      </Tooltip.Trigger>
                      <Tooltip.Portal>
                        <Tooltip.Content
                          className="TooltipContent"
                          sideOffset={3}
                        >
                          The average success rate is the number of tasks marked
                          as "Success" divided by the total number of tasks.
                          Higher is better.
                          <Tooltip.Arrow className="TooltipArrow" />
                        </Tooltip.Content>
                      </Tooltip.Portal>
                    </Tooltip.Root>
                  </Tooltip.Provider>
                </div>
              </TableHead>
              <TableHead>
                <div className="md:flex items-center align-items ">
                  <div className="mr-1">Succes Rate Std</div>
                  <Tooltip.Provider>
                    <Tooltip.Root>
                      <Tooltip.Trigger asChild>
                        <QuestionMarkIcon />
                      </Tooltip.Trigger>
                      <Tooltip.Portal>
                        <Tooltip.Content
                          className="TooltipContent"
                          sideOffset={3}
                        >
                          The estimated standard deviation of the success rate.
                          Lower is better.
                          <Tooltip.Arrow className="TooltipArrow" />
                        </Tooltip.Content>
                      </Tooltip.Portal>
                    </Tooltip.Root>
                  </Tooltip.Provider>
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
