"use client";

import EventsLast7Days from "@/components/dashboard/events-last7days";
import EventsLast30m from "@/components/dashboard/events-last30m";
import OverviewLast7Days from "@/components/dashboard/overview-last7days";
import UsageLast30m from "@/components/dashboard/usage-last30m";
import DatavizGraph from "@/components/insights/dataviz";
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
import { Input } from "@/components/ui/input";
import { authFetcher } from "@/lib/fetcher";
import { DashboardTile } from "@/models/models";
import { dataStateStore, navigationStateStore } from "@/store/store";
import { zodResolver } from "@hookform/resolvers/zod";
import { useUser } from "@propelauth/nextjs/client";
import { set } from "date-fns";
import { GridStack, GridStackNode } from "gridstack";
import "gridstack/dist/gridstack-extra.min.css";
import "gridstack/dist/gridstack.min.css";
import {
  BarChartBig,
  EllipsisVertical,
  Pencil,
  Plus,
  Trash,
  X,
} from "lucide-react";
import Link from "next/link";
import React, { useEffect } from "react";
import { useForm } from "react-hook-form";
import useSWR, { mutate } from "swr";
import { z } from "zod";

import { DatePickerWithRange } from "../date-range";
import FilterComponent from "../filters";
import { Form, FormField, FormItem, FormLabel } from "../ui/form";
import { useToast } from "../ui/use-toast";

interface RenameDashboardTileProps {
  tile_index: number;
  tile: DashboardTile;
  setOpen: (open: boolean) => void;
}

const RenameDashboardTile: React.FC<RenameDashboardTileProps> = ({
  tile_index,
  tile,
  setOpen,
}) => {
  const selectedProject = dataStateStore((state) => state.selectedProject);
  const { accessToken, loading } = useUser();
  const { toast } = useToast();

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
    selectedProject.settings.dashboard_tiles[tile_index] = tile;

    try {
      const creation_response = await fetch(
        `/api/projects/${selectedProject.id}`,
        {
          method: "POST",
          headers: {
            Authorization: "Bearer " + accessToken,
            "Content-Type": "application/json",
          },
          body: JSON.stringify(selectedProject),
        },
      ).then((response) => {
        setOpen(false);
        mutate(
          [`/api/projects/${selectedProject.id}`, accessToken],
          async (data: any) => {
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
          key={`editTileName${tile_index}`}
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
  tile_index: number;
}

const DashboardTileCard: React.FC<DashboardTileProps> = ({
  children,
  tile,
  grid,
  tile_index,
}) => {
  const [renameOpen, setRenameOpen] = React.useState(false);
  const selectedProject = dataStateStore((state) => state.selectedProject);
  const { accessToken } = useUser();
  const { toast } = useToast();

  return (
    <Card
      className="grid-stack-item"
      gs-w={tile.w}
      gs-h={tile.h}
      gs-x={tile.x}
      gs-y={tile.y}
      gs-id={tile_index} // used to update the tile's position
      id={`gridstackitem-${tile_index}`} // used when deleting the tile
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
                  onClick={async (mouseEvent) => {
                    // Remove the card from the grid
                    // Get this card's parent gridstack item using the id
                    const closestParentGridStackItem = document.getElementById(
                      `gridstackitem-${tile_index}`,
                    );
                    console.log(
                      "closestParentGridStackItem",
                      closestParentGridStackItem,
                    );
                    if (grid && closestParentGridStackItem) {
                      grid.removeWidget(
                        closestParentGridStackItem as HTMLElement,
                        true,
                      );
                      // Remove it from the project settings
                      if (!selectedProject) return;
                      if (!selectedProject.settings) return;

                      selectedProject.settings.dashboard_tiles.splice(
                        tile_index,
                        1,
                      );
                      // Update the project settings
                      try {
                        const creation_response = await fetch(
                          `/api/projects/${selectedProject.id}`,
                          {
                            method: "POST",
                            headers: {
                              Authorization: "Bearer " + accessToken,
                              "Content-Type": "application/json",
                            },
                            body: JSON.stringify(selectedProject),
                          },
                        ).then((response) => {
                          mutate(
                            [
                              `/api/projects/${selectedProject.id}`,
                              accessToken,
                            ],
                            async (data: any) => {
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
            <RenameDashboardTile
              tile_index={tile_index}
              tile={tile}
              setOpen={setRenameOpen}
            />
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
  const selectedProject = dataStateStore((state) => state.selectedProject);
  const { toast } = useToast();

  const { data: hasTasksData } = useSWR(
    project_id ? [`/api/explore/${project_id}/has-tasks`, accessToken] : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "POST"),
    { keepPreviousData: true },
  );
  const hasTasks: boolean = hasTasksData?.has_tasks ?? false;
  const [grid, setGrid] = React.useState<GridStack | null>(null);
  const customDashboardTiles = selectedProject?.settings?.dashboard_tiles;
  console.log("customDashboardTiles", customDashboardTiles);

  useEffect(() => {
    console.log("Initializing grid");
    if (!selectedProject) return;
    if (grid) {
      grid.removeAll();
    }

    const initializedGrid = GridStack.init({
      column: 8,
      minRow: 1,
      margin: 12,
      // removable: true,
    });

    if (initializedGrid) {
      initializedGrid.on("change", (event: Event, items: GridStackNode[]) => {
        if (!selectedProject) return;
        if (!selectedProject.settings) return;

        // Find the tile that was moved
        selectedProject.settings.dashboard_tiles.forEach((tile, tile_index) => {
          items.forEach((item) => {
            console.log("Change event item", item);
            if (item.id === tile_index.toString()) {
              if (!selectedProject.settings) return;

              // Update the tile's position
              tile.x = item.x;
              tile.y = item.y;
              tile.w = item.w ?? 4;
              tile.h = item.h ?? 2;

              // Update the project settings
              selectedProject.settings.dashboard_tiles[tile_index] = tile;
            }
          });
        });

        console.log("Change event items", items);

        // Push updates
        (async () => {
          if (!selectedProject) return;
          try {
            const creation_response = await fetch(
              `/api/projects/${selectedProject.id}`,
              {
                method: "POST",
                headers: {
                  Authorization: "Bearer " + accessToken,
                  "Content-Type": "application/json",
                },
                body: JSON.stringify(selectedProject),
              },
            ).then((response) => {
              mutate(
                [`/api/projects/${selectedProject.id}`, accessToken],
                async (data: any) => {
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
      });
    }

    setGrid(initializedGrid);
  }, [selectedProject?.id]);

  if (!project_id) {
    return <></>;
  }

  // The normal dashboard displays a session overview
  const normalDashboard = (
    <>
      <div className="flex flex-row space-x-2 items-center">
        <DatePickerWithRange />
        <FilterComponent variant="tasks" />
        <Link href="/org/insights/dataviz">
          <Button variant="default">
            <Plus className="w-3 h-3 " />
            <BarChartBig className="w-4 h-4 mr-2" />
            Add new graph
          </Button>
        </Link>
      </div>
      {customDashboardTiles && (
        <div className="grid-stack">
          {customDashboardTiles.map((tile, index) => (
            <DashboardTileCard
              key={index}
              tile={tile}
              grid={grid}
              tile_index={index}
            >
              <DatavizGraph
                metric={tile.metric}
                metadata_metric={tile.metadata_metric}
                breakdown_by={tile.breakdown_by}
              />
            </DashboardTileCard>
          ))}
        </div>
      )}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-6">
        <Card className="col-span-full lg:col-span-4">
          <CardHeader>
            <CardTitle>Number of Daily Tasks</CardTitle>
          </CardHeader>
          <CardContent>
            <OverviewLast7Days />
          </CardContent>
        </Card>
        <Card className="col-span-full lg:col-span-2">
          <CardHeader>
            <CardTitle>Last 30 min</CardTitle>
          </CardHeader>
          <CardContent>
            <UsageLast30m />
          </CardContent>
        </Card>
      </div>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-6">
        <Card className="col-span-full lg:col-span-4">
          <CardHeader>
            <CardTitle>Number of Daily Events</CardTitle>
          </CardHeader>
          <CardContent>
            <EventsLast7Days />
          </CardContent>
        </Card>

        <Card className="col-span-full lg:col-span-2">
          <CardHeader>
            <CardTitle>Last 30 min</CardTitle>
          </CardHeader>
          <CardContent>
            <EventsLast30m />
          </CardContent>
        </Card>
      </div>
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
