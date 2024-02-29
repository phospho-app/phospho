"use client";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCaption,
  TableCell,
  TableFooter,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { authFetcher } from "@/lib/fetcher";
import { Topic } from "@/models/topics";
import { navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import { MessageCircleIcon } from "lucide-react";
import Link from "next/link";
import React, { useEffect, useState } from "react";
import useSWR from "swr";

const Topics: React.FC<{}> = ({}) => {
  const { accessToken } = useUser();
  const selectedProject = navigationStateStore(
    (state) => state.selectedProject,
  );

  const project_id = selectedProject?.id;

  const {
    data: topics,
  }: {
    data: Topic[] | null | undefined;
  } = useSWR(
    [`/api/explore/${project_id}/topics`, accessToken],
    ([url, accessToken]) =>
      authFetcher(url, accessToken, "GET").then((res) =>
        res?.topics.sort((a: Topic, b: Topic) => b.count - a.count),
      ),
  );

  return (
    <>
      <Alert>
        <MessageCircleIcon className="h-4 w-4" />
        <AlertTitle>Get a vibe of what people say.</AlertTitle>
        <AlertDescription>
          Topics are automatically extracted from tasks logged to phospho.
        </AlertDescription>
      </Alert>
      {topics !== null && topics?.length && topics?.length > 0 ? (
        <>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead className="text-right">Count</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {topics.map((topic) => (
                <TableRow key={topic.topic_name}>
                  <TableCell>{topic.topic_name}</TableCell>
                  <TableCell className="text-right">{topic.count}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </>
      ) : (
        <div className="flex flex-col justify-center items-center">
          <p className="text-gray-500 mb-4">No task found</p>
          <Link href="https://docs.phospho.ai/getting-started" target="_blank">
            <Button>Setup phospho in your app</Button>
          </Link>
        </div>
      )}
    </>
  );
};

export default Topics;
