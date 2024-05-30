"use client";

import { Spinner } from "@/components/small-spinner";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { useToast } from "@/components/ui/use-toast";
import { authFetcher } from "@/lib/fetcher";
import { formatUnixTimestampToLiteralDatetime } from "@/lib/time";
import { Topic } from "@/models/models";
import { navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import { Play } from "lucide-react";
import React from "react";
import { useEffect } from "react";
import useSWR from "swr";

import { TopicsTable } from "./topics-table";

const Topics: React.FC = () => {
  const project_id = navigationStateStore((state) => state.project_id);
  const { accessToken } = useUser();
  const [detectionRunTimestamp, setDetectionRunTimestamp] = React.useState<
    number | null
  >(null);
  const { toast } = useToast();

  const {
    data: topicsData,
  }: {
    data: Topic[] | null | undefined;
  } = useSWR(
    [`/api/explore/${project_id}/topics`, accessToken],
    ([url, accessToken]) =>
      authFetcher(url, accessToken, "POST").then((res) =>
        res?.topics.sort((a: Topic, b: Topic) => b.size - a.size),
      ),
    {
      keepPreviousData: true,
      refreshInterval: detectionRunTimestamp ? 3 : 30,
    },
  );

  // if Topic.created_at > detectionRunTimestamp, then set detectionRunTimestamp to null
  const maxCreatedAt = topicsData?.reduce((acc, topic) => {
    return topic.created_at > acc ? topic.created_at : acc;
  }, 0);
  const lastUpdateLabel = maxCreatedAt ? new Date(maxCreatedAt * 1000) : null;

  useEffect(() => {
    if (
      detectionRunTimestamp !== null &&
      maxCreatedAt !== undefined &&
      maxCreatedAt > detectionRunTimestamp
    ) {
      setDetectionRunTimestamp(null);
    }
  }, [maxCreatedAt, detectionRunTimestamp]);

  if (!project_id) {
    return <></>;
  }

  return (
    <>
      <Card className="bg-secondary">
        <CardHeader>
          <div className="flex justify-between items-start">
            <div>
              <CardTitle className="flex flex-row text-2xl font-bold tracking-tight items-center">
                Automatic topic detection
              </CardTitle>
              <CardDescription>
                <p className="text-muted-foreground">
                  Detect recurring conversation topics, outliers, and trends,
                  using unsupervized machine learning algorithms.
                </p>
              </CardDescription>
            </div>
            <div className="flex flex-col space-y-1 justify-center items-center">
              <Button
                variant="default"
                onClick={async () => {
                  setDetectionRunTimestamp(Date.now() / 1000);
                  try {
                    await fetch(`/api/explore/${project_id}/detect-topics`, {
                      method: "POST",
                      headers: {
                        Authorization: "Bearer " + accessToken,
                      },
                    }).then((response) => {
                      if (response.status == 200) {
                        toast({
                          title: "Topic detection started",
                          description: "This may take a few seconds.",
                        });
                      } else {
                        toast({
                          title: "Error when starting detection",
                          description: response.text(),
                        });
                        setDetectionRunTimestamp(null);
                      }
                    });
                  } catch (e) {
                    toast({
                      title: "Error when starting detection",
                      description: JSON.stringify(e),
                    });
                    setDetectionRunTimestamp(null);
                  }
                }}
                disabled={detectionRunTimestamp !== null}
              >
                {detectionRunTimestamp === null && (
                  <>
                    <Play className="w-4 h-4 mr-2 text-green-500" /> Run topic
                    detection
                  </>
                )}
                {detectionRunTimestamp !== null && (
                  <>
                    <Spinner className="mr-1" />
                    Detection in progress...
                  </>
                )}
              </Button>
              <div className="text-muted-foreground text-xs">
                Last update:{" "}
                {maxCreatedAt
                  ? formatUnixTimestampToLiteralDatetime(maxCreatedAt)
                  : "Never"}
              </div>
            </div>
          </div>
        </CardHeader>
      </Card>
      <div className="h-full flex-1 flex-col space-y-2 md:flex ">
        <TopicsTable topicsData={topicsData} />
      </div>
    </>
  );
};

export default Topics;
