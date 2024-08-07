import { DatePickerWithRange } from "@/components/date-range";
import FilterComponent from "@/components/filters";
import { Spinner } from "@/components/small-spinner";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { toast } from "@/components/ui/use-toast";
import UpgradeButton from "@/components/upgrade-button";
import { authFetcher } from "@/lib/fetcher";
import { Clustering, Project } from "@/models/models";
import { dataStateStore } from "@/store/store";
import { navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import { Separator } from "@radix-ui/react-dropdown-menu";
import { ChevronRight, Sparkles } from "lucide-react";
import React, { use } from "react";
import { useEffect, useState } from "react";
import useSWR from "swr";
import * as SelectPrimitive from "@radix-ui/react-select";
import { cn } from "@/lib/utils";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { MessagesOrSessions } from "@/components/messages-or-sessions";

const RunClusters = ({
  totalNbTasks,
  totalNbSessions,
  mutateClusterings,
  clusteringUnavailable,
}: {
  totalNbTasks: number | null | undefined;
  totalNbSessions: number | null | undefined;
  mutateClusterings: any;
  clusteringUnavailable: boolean;
}) => {
  const { accessToken } = useUser();
  const [clusteringCost, setClusteringCost] = useState(0);
  const project_id = navigationStateStore((state) => state.project_id);
  const orgMetadata = dataStateStore((state) => state.selectedOrgMetadata);
  const dataFilters = navigationStateStore((state) => state.dataFilters);

  const hobby = orgMetadata?.plan === "hobby";

  const [loading, setLoading] = React.useState(false);
  const [open, setOpen] = React.useState(false);

  const messagesOrSessions = navigationStateStore((state) => state.messagesOrSessions);

  if (messagesOrSessions === "sessions") {
    useEffect(() => {
      if (totalNbSessions) {
        setClusteringCost(totalNbSessions * 2);
      }
    }, [totalNbSessions]);
  } else {
    useEffect(() => {
      if (totalNbTasks) {
        setClusteringCost(totalNbTasks * 2);
      }
    }, [totalNbTasks]);
  }

  if (!project_id) {
    return <></>;
  }

  async function runClusterAnalysis() {
    setLoading(true);
    mutateClusterings((data: any) => {
      const newClustering: Clustering = {
        id: "",
        clustering_id: "",
        project_id: project_id || "", // Should not be ""
        org_id: "",
        created_at: Date.now() / 1000,
        status: "started",
        clusters_ids: [],
      };
      const newData = {
        clusterings: [newClustering, ...data?.clusterings],
      };
      return newData;
    });
    try {
      await fetch(`/api/explore/${project_id}/detect-clusters`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: "Bearer " + accessToken,
        },
        body: JSON.stringify({
          filters: dataFilters,
        }),
      }).then((response) => {
        if (response.status == 200) {
          toast({
            title: "Cluster detection started ⏳",
            description: "This may take a few minutes.",
          });
          setOpen(false);
        } else {
          toast({
            title: "Error when starting detection",
            description: response.text(),
          });
        }
        setLoading(false);
      });
    } catch (e) {
      toast({
        title: "Error when starting detection",
        description: JSON.stringify(e),
      });
      setLoading(false);

    }
  }

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger>
        <Button className="default">
          <Sparkles className="w-4 h-4 mr-2 text-green-500" /> Configure
          clusters detection
          <ChevronRight className="w-4 h-4 ml-2" />
        </Button>
      </SheetTrigger>
      <SheetContent className="md:w-1/2 overflow-auto">
        <SheetTitle>
          Configure clusters detection
        </SheetTitle>
        {messagesOrSessions === "messages" && (
          <SheetDescription>
            Run a cluster analysis on your user messages to detect patterns and group similar messages together.
          </SheetDescription>
        )}
        {messagesOrSessions === "sessions" && (
          <SheetDescription>
            Run a cluster analysis on your user sessions to detect patterns and group similar sessions together.
          </SheetDescription>
        )}
        <Separator className="my-8" />
        <div className="flex">
          <DatePickerWithRange className="mr-2" />
          <MessagesOrSessions className="mr-2" />
          <FilterComponent variant="tasks" />

        </div>
        {messagesOrSessions === "messages" && (
          <>
            {(!totalNbTasks || totalNbTasks < 5) && (
              <div className="mt-4">
                You need at least 5 user messages to run a cluster analysis. There are currently {totalNbTasks ? totalNbTasks : 0} user messages.
              </div>
            )}
            {totalNbTasks && totalNbTasks >= 5 && (
              <div className="mt-4">
                We will clusterize {totalNbTasks} user messages for a total of {clusteringCost} credits.
              </div>
            )}
            {hobby && (
              <div className="flex justify-end mt-4">
                <UpgradeButton tagline="Run cluster analysis" green={false} />
              </div>
            )}
            {!hobby && totalNbTasks && totalNbTasks >= 5 && (
              <div className="flex justify-end">
                <Button
                  type="submit"
                  onClick={runClusterAnalysis}
                  disabled={clusteringUnavailable || loading}
                >
                  {(loading || clusteringUnavailable) && <Spinner className="mr-2" />}
                  Run cluster analysis
                </Button>
              </div>
            )}
          </>
        )}
        {messagesOrSessions === "sessions" && (
          <>
            {(!totalNbSessions || totalNbSessions < 5) && (
              <div className="mt-4">
                You need at least 5 user sessions to run a cluster analysis. There are currently {totalNbSessions ? totalNbSessions : 0} user sessions.
              </div>
            )}
            {totalNbSessions && totalNbSessions >= 5 && (
              <div className="mt-4">
                We will clusterize {totalNbSessions} user sessions for a total of {clusteringCost} credits.
              </div>
            )}
            {hobby && (
              <div className="flex justify-end mt-4">
                <UpgradeButton tagline="Run cluster analysis" green={false} />
              </div>
            )}
            {!hobby && totalNbSessions && totalNbSessions >= 5 && (
              <div className="flex justify-end">
                <Button
                  type="submit"
                  onClick={runClusterAnalysis}
                  disabled={clusteringUnavailable || loading}
                >
                  {(loading || clusteringUnavailable) && <Spinner className="mr-2" />}
                  Run cluster analysis
                </Button>
              </div>
            )}
          </>
        )}

      </SheetContent>
    </Sheet>
  );
};

export default RunClusters;
