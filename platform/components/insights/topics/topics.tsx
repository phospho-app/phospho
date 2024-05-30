"use client";

import SessionsDataviz from "@/components/transcripts/sessions/session-dataviz";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { authFetcher } from "@/lib/fetcher";
import { Topic } from "@/models/models";
import { dataStateStore, navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import Link from "next/link";
import React from "react";
import useSWR from "swr";

import { TopicsTable } from "./topics-table";

const Topics: React.FC = () => {
  const project_id = navigationStateStore((state) => state.project_id);
  const hasSessions = dataStateStore((state) => state.hasSessions);
  const { accessToken } = useUser();

  const {
    data: topicsData,
  }: {
    data: Topic[] | null | undefined;
  } = useSWR(
    [`/api/explore/${project_id}/topics`, accessToken],
    ([url, accessToken]) =>
      authFetcher(url, accessToken, "GET").then((res) =>
        res?.topics.sort((a: Topic, b: Topic) => b.size - a.size),
      ),
  );

  if (!project_id) {
    return <></>;
  }

  return (
    <>
      <Card className="bg-secondary">
        <CardHeader>
          <div className="flex justify-between items-center">
            <div>
              <CardTitle className="flex flex-row text-2xl font-bold tracking-tight items-center">
                Automatic topic detection
              </CardTitle>
              <CardDescription>
                <p className="text-gray-500">
                  Automatically analyze your data to detect recurring
                  conversation topics, outliers, and trends.
                </p>
              </CardDescription>
            </div>

            <Button variant="default">Run topic detection</Button>
          </div>
        </CardHeader>
      </Card>
      <div className="hidden h-full flex-1 flex-col space-y-2 md:flex ">
        <TopicsTable topicsData={topicsData} />
      </div>
    </>
  );
};

export default Topics;
