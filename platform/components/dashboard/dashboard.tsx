"use client";

import EventsLast7Days from "@/components/dashboard/events-last7days";
import OverviewLast7Days from "@/components/dashboard/overview-last7days";
import DatavizGraph from "@/components/dataviz";
import { DatePickerWithRange } from "@/components/date-range";
import FilterComponent from "@/components/filters";
import { CenteredSpinner } from "@/components/small-spinner";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Form, FormField, FormItem, FormLabel } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { useToast } from "@/components/ui/use-toast";
import { authFetcher } from "@/lib/fetcher";
import { DashboardTile, Project } from "@/models/models";
import { navigationStateStore } from "@/store/store";
import { zodResolver } from "@hookform/resolvers/zod";
import { useUser } from "@propelauth/nextjs/client";
import { GridStack, GridStackNode } from "gridstack";
import "gridstack/dist/gridstack-extra.min.css";
import "gridstack/dist/gridstack.min.css";
import {
  BarChartBig,
  EllipsisVertical,
  Pencil,
  Plus,
  Trash,
} from "lucide-react";
import Link from "next/link";
import React, { useEffect } from "react";
import { useForm } from "react-hook-form";
import useSWR, { mutate } from "swr";
import { z } from "zod";

interface RenameDashboardTileProps {
  tile: DashboardTile;
  setOpen: (open: boolean) => void;
}

const RenameDashboardTile: React.FC<RenameDashboardTileProps> = ({
  tile,
  setOpen,
}) => {
  const { accessToken, loading } = useUser();
  const { toast } = useToast();
  const project_id = navigationStateStore((state) => state.project_id);
  const { data: selectedProject }: { data: Project } = useSWR(
    project_id ? [`/api/projects/${project_id}`, accessToken] : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "GET"),
    {
      keepPreviousData: true,
    },
  );

  const formSchema = z.object({
    name: z.string().min(1).max(100),
  });

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      name: tile.tile_name,
    },
  });

  async function onSubmit(values: z.infer<typeof formSchema>) {
    if (!selectedProject) return;
    if (!selectedProject.settings) return;

    tile.tile_name = values.name;
    // Edit the selected project settings based on the tile id
    selectedProject.settings.dashboard_tiles.map((t) => {
      if (t.id === tile.id) {
        t.tile_name = tile.tile_name;
      }
    });

    try {
      await fetch(`/api/projects/${selectedProject.id}`, {
        method: "POST",
        headers: {
          Authorization: "Bearer " + accessToken,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(selectedProject),
      }).then(() => {
        setOpen(false);
        mutate(
          [`/api/projects/${selectedProject.id}`, accessToken],
          async () => {
            return { project: selectedProject };
          },
        );
      });
    } catch (error) {
      toast({
        title: "Error when renaming the tile",
        description: `${error}`,
      });
    }
  }

  return (
    <AlertDialogContent className="md:w-1/3">
      <Form {...form}>
        <form
          onSubmit={form.handleSubmit(onSubmit)}
          className="font-normal space-y-4"
          key={`editTileName${tile.id}`}
        >
          <AlertDialogHeader>
            <FormField
              control={form.control}
              name="name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Detection scope</FormLabel>
                  <Input value={field.value} onChange={field.onChange} />
                </FormItem>
              )}
            />
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction type="submit" disabled={loading}>
              Rename
            </AlertDialogAction>
          </AlertDialogFooter>
        </form>
      </Form>
    </AlertDialogContent>
  );
};

interface DashboardTileProps {
  children: React.ReactNode;
  tile: DashboardTile;
  grid: GridStack | null;
}

const DashboardTileCard: React.FC<DashboardTileProps> = ({
  children,
  tile,
  grid,
}) => {
  const [renameOpen, setRenameOpen] = React.useState(false);
  const { accessToken } = useUser();
  const { toast } = useToast();
  const project_id = navigationStateStore((state) => state.project_id);
  const { data: selectedProject }: { data: Project } = useSWR(
    project_id ? [`/api/projects/${project_id}`, accessToken] : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "GET"),
    {
      keepPreviousData: true,
    },
  );

  return (
    <Card
      className="grid-stack-item"
      gs-w={tile.w}
      gs-h={tile.h}
      gs-x={tile.x}
      gs-y={tile.y}
      gs-id={tile.id} // used to update the tile's position
      id={`gridstackitem-${tile.id}`} // used when deleting the tile
    >
      <div className="grid-stack-item-content">
        <CardHeader className="flex flex-row justify-between items-center py-1">
          <CardTitle>{tile.tile_name}</CardTitle>
          <AlertDialog open={renameOpen} onOpenChange={setRenameOpen}>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon">
                  <EllipsisVertical />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <AlertDialogTrigger asChild>
                  <DropdownMenuItem className="flex flex-row space-x-2 items-center">
                    <Pencil className="w-4 h-4" /> <span>Rename</span>
                  </DropdownMenuItem>
                </AlertDialogTrigger>
                <DropdownMenuItem
                  className="text-red-500 flex flex-row items-center space-x-2"
                  onClick={async () => {
                    // Remove the card from the grid
                    // Get this card's parent gridstack item using the id
                    const closestParentGridStackItem = document.getElementById(
                      `gridstackitem-${tile.id}`,
                    );
                    if (grid && closestParentGridStackItem) {
                      grid.removeWidget(
                        closestParentGridStackItem as HTMLElement,
                        true,
                      );
                      // Remove it from the project settings
                      if (!selectedProject) return;
                      if (!selectedProject.settings) return;

                      // Remove based on the tile's id
                      const newTiles =
                        selectedProject.settings.dashboard_tiles.filter(
                          (t) => t.id !== tile.id,
                        );
                      selectedProject.settings.dashboard_tiles = newTiles;
                      // Update the project settings
                      try {
                        await fetch(`/api/projects/${selectedProject.id}`, {
                          method: "POST",
                          headers: {
                            Authorization: "Bearer " + accessToken,
                            "Content-Type": "application/json",
                          },
                          body: JSON.stringify(selectedProject),
                        }).then(() => {
                          mutate(
                            [
                              `/api/projects/${selectedProject.id}`,
                              accessToken,
                            ],
                            async () => {
                              return { project: selectedProject };
                            },
                          );
                        });
                      } catch (error) {
                        toast({
                          title: "Error when removing the tile",
                          description: `${error}`,
                        });
                      }
                    }
                  }}
                >
                  <Trash className="w-4 h-4" /> <span>Remove</span>
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
            <RenameDashboardTile tile={tile} setOpen={setRenameOpen} />
          </AlertDialog>
        </CardHeader>
        <CardContent className="h-4/5">{children}</CardContent>
      </div>
    </Card>
  );
};

const Dashboard: React.FC = () => {
  const project_id = navigationStateStore((state) => state.project_id);
  const { accessToken } = useUser();
  const { toast } = useToast();
  const { data: selectedProject }: { data: Project } = useSWR(
    project_id
      ? [`/api/projects/${project_id}`, accessToken, "initial_tiles"]
      : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "GET"),
    {
      keepPreviousData: true,
    },
  );

  const { data: hasTasksData } = useSWR(
    project_id ? [`/api/explore/${project_id}/has-tasks`, accessToken] : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "POST"),
    { keepPreviousData: true },
  );
  const hasTasks: boolean = hasTasksData?.has_tasks ?? false;
  const [grid, setGrid] = React.useState<GridStack | null>(null);
  const [currentGridProjectId, setCurrentGridProjectId] = React.useState<
    string | undefined
  >(undefined);
  const customDashboardTiles = selectedProject?.settings?.dashboard_tiles;

  useEffect(() => {
    if (grid && currentGridProjectId !== selectedProject?.id) {
      grid.destroy(false);
    }

    const allYValues = customDashboardTiles?.map((t) => t.y ?? 0) ?? [];
    const initializedGrid = GridStack.init({
      column: 8,
      minRow: Math.max(...allYValues, 1),
      margin: 12,
      // float: true,
      // removable: true,
    });

    const onChangeFunction = (event: Event, items: GridStackNode[]) => {
      if (!selectedProject) return;
      if (!selectedProject.settings) return;

      // Find the tile that was moved
      selectedProject.settings.dashboard_tiles.forEach((tile) => {
        items.forEach((item) => {
          if (item.id === tile.id) {
            if (!selectedProject.settings) return;

            // Update the tile's position
            tile.x = item.x;
            tile.y = item.y;
            tile.w = item.w ?? 4;
            tile.h = item.h ?? 2;
          }
        });
      });

      // Push updates
      (async () => {
        if (!selectedProject) return;
        try {
          await fetch(`/api/projects/${selectedProject.id}`, {
            method: "POST",
            headers: {
              Authorization: "Bearer " + accessToken,
              "Content-Type": "application/json",
            },
            body: JSON.stringify(selectedProject),
          }).then(() => {
            mutate(
              [`/api/projects/${selectedProject.id}`, accessToken],
              async () => {
                return { project: selectedProject };
              },
            );
          });
        } catch (error) {
          toast({
            title: "Error when moving the tile",
            description: `${error}`,
          });
        }
      })();
    };

    if (initializedGrid) {
      initializedGrid.on("change", onChangeFunction);
      setGrid(initializedGrid);
      setCurrentGridProjectId(selectedProject?.id);
      return;
    }
  }, [
    selectedProject?.id,
    currentGridProjectId,
    accessToken,
    customDashboardTiles,
    grid,
    selectedProject,
    toast,
  ]);

  if (!project_id) {
    return <></>;
  }

  // The normal dashboard displays a session overview
  const normalDashboard = (
    <>
      <div className="flex flex-row space-x-2 items-end">
        <DatePickerWithRange />
        <FilterComponent variant="tasks" />
        <Link href="/org/dataviz/studio">
          <Button variant="default">
            <Plus className="w-3 h-3 " />
            <BarChartBig className="w-4 h-4 mr-2" />
            Add new graph
          </Button>
        </Link>
      </div>

      {customDashboardTiles && (
        <div className="grid-stack">
          {customDashboardTiles.map((tile) => (
            <DashboardTileCard key={tile.id} tile={tile} grid={grid}>
              <DatavizGraph
                metric={tile.metric}
                metadata_metric={tile.metadata_metric}
                breakdown_by={tile.breakdown_by}
                scorer_id={tile.scorer_id ?? null}
                filters={tile.filters}
              />
            </DashboardTileCard>
          ))}
        </div>
      )}
      <Card className="col-span-full lg:col-span-4">
        <CardHeader>
          <CardTitle>Number of messages per day</CardTitle>
        </CardHeader>
        <CardContent>
          <OverviewLast7Days />
        </CardContent>
      </Card>
      <Card className="col-span-full lg:col-span-4">
        <CardHeader>
          <CardTitle>Tags detected per day</CardTitle>
        </CardHeader>
        <CardContent>
          <EventsLast7Days />
        </CardContent>
      </Card>
    </>
  );

  // The no data dashboard displays a message to setup phospho in the app

  return (
    <>
      <div className="flex flex-1 flex-col space-y-4">
        {hasTasks === null && <CenteredSpinner />}
        {normalDashboard}
      </div>
    </>
  );
};

export default Dashboard;
