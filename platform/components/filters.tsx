import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuPortal,
  DropdownMenuSeparator,
  DropdownMenuSub,
  DropdownMenuSubContent,
  DropdownMenuSubTrigger,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  HoverCard,
  HoverCardContent,
  HoverCardTrigger,
} from "@/components/ui/hover-card";
import { authFetcher } from "@/lib/fetcher";
import { formatUnixTimestampToLiteralDatetime } from "@/lib/time";
import { getLanguageLabel } from "@/lib/utils";
import {
  Clustering,
  EventDefinition,
  MetadataFieldsToUniqueValues,
  Project,
} from "@/models/models";
import { navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import {
  EyeClosedIcon,
  EyeOpenIcon,
  MagnifyingGlassIcon,
} from "@radix-ui/react-icons";
import {
  Annoyed,
  Boxes,
  Code,
  FilterX,
  Flag,
  Frown,
  Languages,
  List,
  ListFilter,
  Meh,
  PenSquare,
  Plus,
  Scale,
  Shapes,
  Smile,
  SmilePlus,
  Tag,
  TextSearch,
  ThumbsDown,
  ThumbsUp,
  UserRound,
  X,
} from "lucide-react";
import Link from "next/link";
import React from "react";
import useSWR from "swr";

interface LanguageFilterOption {
  value: string;
  label: string;
}

const FilterComponent = ({
  variant = "tasks",
}: {
  variant: "tasks" | "sessions" | "users" | "messages";
}) => {
  const setDataFilters = navigationStateStore((state) => state.setDataFilters);
  const dataFilters = navigationStateStore((state) => state.dataFilters);
  const showSearchBar = navigationStateStore((state) => state.showSearchBar);
  const setShowSearchBar = navigationStateStore(
    (state) => state.setShowSearchBar,
  );
  const { accessToken } = useUser();

  if (variant === "messages") {
    variant = "tasks";
  }

  const project_id = navigationStateStore((state) => state.project_id);
  const setSessionsPagination = navigationStateStore(
    (state) => state.setSessionsPagination,
  );
  const setTasksPagination = navigationStateStore(
    (state) => state.setTasksPagination,
  );
  const dateRange = navigationStateStore((state) => state.dateRange);

  const { data: selectedProject }: { data: Project } = useSWR(
    project_id ? [`/api/projects/${project_id}`, accessToken] : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "GET"),
    {
      keepPreviousData: true,
    },
  );
  const events = selectedProject?.settings?.events;
  const tagger_events: Record<string, EventDefinition> = events
    ? Object.fromEntries(
        Object.entries(events).filter(
          ([, event]) =>
            event.score_range_settings?.score_type === "confidence",
        ),
      )
    : {};
  const scorer_events: Record<string, EventDefinition> = events
    ? Object.fromEntries(
        Object.entries(events).filter(
          ([, event]) => event.score_range_settings?.score_type === "range",
        ),
      )
    : {};
  const category_events: Record<string, EventDefinition> = events
    ? Object.fromEntries(
        Object.entries(events).filter(
          ([, event]) => event.score_range_settings?.score_type === "category",
        ),
      )
    : {};

  const resetPagination = () => {
    if (variant === "tasks") {
      setTasksPagination((prev) => ({
        ...prev,
        pageIndex: 0,
      }));
    } else {
      setSessionsPagination((prev) => ({
        ...prev,
        pageIndex: 0,
      }));
    }
  };

  // Language filters
  const { data: languages } = useSWR(
    selectedProject?.id
      ? [`/api/projects/${selectedProject?.id}/languages`, accessToken]
      : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "GET"),
    {
      keepPreviousData: true,
    },
  );

  const languageFilterOptions = languages?.map((language: string) => ({
    value: language,
    label: getLanguageLabel(language),
  }));

  // Metadata filters: {"string": {metadata_key: [unique_metadata_values]}}
  const { data: metadataFieldsToValues } = useSWR(
    selectedProject?.id
      ? [
          `/api/metadata/${selectedProject?.id}/fields/values`,
          accessToken,
          "unique_metadata_fields_to_values",
        ]
      : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "POST"),
    {
      keepPreviousData: true,
    },
  );
  const stringFields: MetadataFieldsToUniqueValues | undefined =
    metadataFieldsToValues?.string;

  // Clusterings filters
  const { data: clusteringsData } = useSWR(
    selectedProject?.id
      ? [`/api/explore/${selectedProject?.id}/clusterings`, accessToken]
      : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "POST"),
    {
      keepPreviousData: true,
    },
  );
  const clusterings = clusteringsData?.clusterings as Clustering[];

  // Number of active filters that are not the created_at_start and created_at_end
  const activeFilterCount =
    dataFilters &&
    Object.keys(dataFilters).filter(
      (key) =>
        key !== "created_at_start" &&
        key !== "created_at_end" &&
        key !== "task_id_search" &&
        key !== "session_id_search",
    ).length;

  if (!selectedProject) {
    return <></>;
  }

  return (
    <div className="flex flex-wrap gap-x-2 gap-y-2 items-end">
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="outline" className="min-w-[12rem] justify-start">
            <ListFilter className="size-4 mr-1" />
            <div className="flex-grow">Filters</div>
            <Plus className="size-4 ml-1" />
          </Button>
        </DropdownMenuTrigger>
        {dataFilters.flag && (
          <Button
            variant="outline"
            onClick={() => {
              setDataFilters({
                ...dataFilters,
                flag: null,
              });
              resetPagination();
            }}
          >
            {dataFilters.flag}
            <X className="size-4" />
          </Button>
        )}
        {dataFilters.has_notes && (
          <Button
            variant="outline"
            onClick={() => {
              setDataFilters({
                ...dataFilters,
                has_notes: false,
              });
              resetPagination();
            }}
          >
            Has notes
            <X className="size-4 ml-2" />
          </Button>
        )}
        {dataFilters.event_name &&
          dataFilters.event_name.map((event_name) => {
            return (
              <Button
                variant="outline"
                onClick={() => {
                  setDataFilters({ ...dataFilters, event_name: null });
                  resetPagination();
                }}
                key={event_name}
              >
                {dataFilters.event_name}
                <X className="size-4 ml-2" />
              </Button>
            );
          })}
        {dataFilters.scorer_value &&
          Object.entries(dataFilters.scorer_value).map(([event_id, value]) => {
            const event_name = Object.entries(scorer_events).find(
              ([, e]) => e.id === event_id,
            )?.[0];

            if (!event_name) return null;

            return (
              <Button
                key={event_id}
                variant="outline"
                onClick={() => {
                  setDataFilters({
                    ...dataFilters,
                    scorer_value: null,
                  });
                  resetPagination();
                }}
              >
                {event_name}: {value}
                <X className="size-4 ml-2" />
              </Button>
            );
          })}
        {dataFilters.classifier_value &&
          Object.entries(dataFilters.classifier_value).map(
            ([event_id, value]) => {
              const event_name = Object.entries(category_events).find(
                ([, e]) => e.id === event_id,
              )?.[0];

              if (!event_name) return null;

              return (
                <Button
                  key={event_id}
                  variant="outline"
                  onClick={() => {
                    setDataFilters({
                      ...dataFilters,
                      classifier_value: null,
                    });
                    resetPagination();
                  }}
                >
                  {event_name}: {value}
                  <X className="size-4 ml-2" />
                </Button>
              );
            },
          )}
        {dataFilters.language && (
          <Button
            variant="outline"
            onClick={() => {
              setDataFilters({
                ...dataFilters,
                language: null,
              });
              resetPagination();
            }}
          >
            {getLanguageLabel(dataFilters.language)}
            <X className="size-4 ml-2" />
          </Button>
        )}
        {dataFilters.sentiment && (
          <Button
            variant="outline"
            onClick={() => {
              setDataFilters({
                ...dataFilters,
                sentiment: null,
              });
              resetPagination();
            }}
          >
            {dataFilters.sentiment}
            <X className="size-4 ml-2" />
          </Button>
        )}
        {dataFilters.metadata &&
          Object.entries(dataFilters.metadata).map(([key, value]) => {
            return (
              <Button
                variant="outline"
                onClick={() => {
                  // Delete this metadata filter
                  if (!dataFilters.metadata) {
                    return;
                  }
                  delete dataFilters.metadata[key];
                  setDataFilters({
                    ...dataFilters,
                  });
                  resetPagination();
                }}
                key={key + value}
              >
                {key}:{" "}
                {value.length > 20 ? value.substring(0, 20) + "..." : value}
                <X className="size-4 ml-2" />
              </Button>
            );
          })}
        {dataFilters.clustering_id && (
          <Button
            variant="outline"
            onClick={() => {
              setDataFilters({
                ...dataFilters,
                clustering_id: null,
                clusters_ids: null,
              });
              resetPagination();
            }}
          >
            clustering:{" "}
            {formatUnixTimestampToLiteralDatetime(
              clusterings?.find(
                (clustering) => clustering.id === dataFilters.clustering_id,
              )?.created_at ?? 0,
            )}
            <X className="size-4 ml-2" />
          </Button>
        )}
        {dataFilters.clusters_ids &&
          dataFilters.clusters_ids.map((cluster_id) => {
            const clustering = clusterings?.find((clustering) =>
              clustering.clusters?.find((cluster) => cluster.id === cluster_id),
            );
            const cluster = clustering?.clusters?.find(
              (cluster) => cluster.id === cluster_id,
            ) ?? { name: "" };

            return (
              <Button
                variant="outline"
                onClick={() => {
                  const currentClustersIds = dataFilters.clusters_ids ?? [];
                  setDataFilters({
                    ...dataFilters,
                    clusters_ids: currentClustersIds.filter(
                      (id) => id !== cluster_id,
                    ),
                  });
                  resetPagination();
                }}
                key={cluster_id}
              >
                cluster: {""}
                {cluster?.name.length > 50
                  ? cluster?.name.substring(0, 50) + "..."
                  : cluster?.name}
                <X className="size-4 ml-2" />
              </Button>
            );
          })}
        {dataFilters.is_last_task && (
          <Button
            variant="outline"
            onClick={() => {
              setDataFilters({
                ...dataFilters,
                is_last_task: null,
              });
              resetPagination();
            }}
          >
            Is last message
            <X className="size-4 ml-2" />
          </Button>
        )}
        {dataFilters.exclude_users && (
          <Button
            variant="outline"
            onClick={() => {
              setDataFilters({
                ...dataFilters,
                exclude_users: null,
              });
              resetPagination();
            }}
          >
            Exclude users in settings
            <X className="size-4 ml-2" />
          </Button>
        )}
        {dataFilters && activeFilterCount > 0 && (
          <HoverCard openDelay={0} closeDelay={0}>
            <HoverCardTrigger>
              <Button
                variant="secondary"
                onClick={() => {
                  setDataFilters({
                    created_at_start: dateRange?.created_at_start,
                    created_at_end: dateRange?.created_at_end,
                  });
                  resetPagination();
                }}
              >
                <FilterX className="size-4" />
              </Button>
            </HoverCardTrigger>
            <HoverCardContent
              className="m-0 text-xs text-background bg-foreground"
              align="center"
            >
              Clear all filters
            </HoverCardContent>
          </HoverCard>
        )}
        <DropdownMenuContent className="w-56" align="start">
          <DropdownMenuLabel>Filters to apply</DropdownMenuLabel>
          <DropdownMenuSeparator />
          {/* Flag */}
          <DropdownMenuSub>
            <DropdownMenuSubTrigger>
              <Flag className="size-4 mr-2" />
              <span>Human rating</span>
            </DropdownMenuSubTrigger>
            <DropdownMenuPortal>
              <DropdownMenuSubContent>
                <DropdownMenuItem
                  onClick={() => {
                    setDataFilters({
                      ...dataFilters,
                      flag: "success",
                    });
                    resetPagination();
                  }}
                  style={{
                    color: dataFilters.flag === "success" ? "green" : "inherit",
                  }}
                >
                  <ThumbsUp className="size-4 mr-2" />
                  <span>Success</span>
                </DropdownMenuItem>
                <DropdownMenuItem
                  onClick={() => {
                    setDataFilters({
                      ...dataFilters,
                      flag: "failure",
                    });
                    resetPagination();
                  }}
                  style={{
                    color: dataFilters.flag === "failure" ? "red" : "inherit",
                  }}
                >
                  <ThumbsDown className="size-4 mr-2" />
                  <span>Failure</span>
                </DropdownMenuItem>
                {variant === "tasks" && (
                  <DropdownMenuItem
                    onClick={() => {
                      setDataFilters({
                        ...dataFilters,
                        has_notes: !dataFilters.has_notes,
                      });
                      resetPagination();
                    }}
                    style={{
                      color: dataFilters.has_notes ? "green" : "inherit",
                    }}
                  >
                    <PenSquare className="size-4 mr-2" />
                    <span>Has notes </span>
                  </DropdownMenuItem>
                )}
              </DropdownMenuSubContent>
            </DropdownMenuPortal>
          </DropdownMenuSub>
          {/* Tagger events */}
          <DropdownMenuSub>
            <DropdownMenuSubTrigger>
              <Tag className="size-4 mr-2" />
              <span>Taggers</span>
            </DropdownMenuSubTrigger>
            <DropdownMenuPortal>
              <DropdownMenuSubContent className="overflow-y-auto max-h-[20rem]">
                {tagger_events &&
                  Object.entries(tagger_events).map(([event_name, event]) => {
                    return (
                      <DropdownMenuItem
                        key={event.id}
                        onClick={() => {
                          // Override the event_name filter
                          // TODO: Allow multiple event_name filters
                          setDataFilters({
                            ...dataFilters,
                            event_name: [event_name],
                          });
                          resetPagination();
                        }}
                        style={{
                          color: dataFilters?.event_name?.includes(event_name)
                            ? "green"
                            : "inherit",
                        }}
                      >
                        {event_name}
                      </DropdownMenuItem>
                    );
                  })}
                {tagger_events && Object.entries(tagger_events).length == 0 && (
                  <DropdownMenuItem asChild>
                    <Link
                      href="/org/insights/events"
                      className="flex items-center px-2 py-1.5 text-sm cursor-pointer hover:bg-accent hover:text-accent-foreground focus:bg-accent focus:text-accent-foreground"
                    >
                      <TextSearch className="size-4 mr-2 flex-shrink-0" />
                      <span className="truncate">Setup taggers</span>
                    </Link>
                  </DropdownMenuItem>
                )}
              </DropdownMenuSubContent>
            </DropdownMenuPortal>
          </DropdownMenuSub>
          {/* Scorer */}
          <DropdownMenuSub>
            <DropdownMenuSubTrigger>
              <Scale className="size-4 mr-2" />
              <span>Scorers</span>
            </DropdownMenuSubTrigger>
            <DropdownMenuPortal>
              <DropdownMenuSubContent>
                {scorer_events &&
                  Object.entries(scorer_events).map(([event_name, event]) => {
                    if (!event.id) {
                      return null;
                    }

                    return (
                      <DropdownMenuSub key={"scorer_value_" + event.id}>
                        <DropdownMenuSubTrigger>
                          <span>{event_name}</span>
                        </DropdownMenuSubTrigger>
                        <DropdownMenuPortal>
                          <DropdownMenuSubContent className="overflow-y-auto max-h-[40rem]">
                            {Array.from(
                              {
                                length:
                                  (event.score_range_settings?.max ?? 5) -
                                  (event.score_range_settings?.min ?? 1) +
                                  1,
                              },
                              (_, i) =>
                                (event.score_range_settings?.min ?? 1) + i,
                            ).map((scorer_value) => {
                              const eventId = event.id as string;
                              return (
                                <DropdownMenuItem
                                  key={scorer_value}
                                  onClick={() => {
                                    setDataFilters({
                                      ...dataFilters,
                                      scorer_value: {
                                        [eventId]: scorer_value,
                                      },
                                    });
                                    resetPagination();
                                  }}
                                >
                                  {scorer_value}
                                </DropdownMenuItem>
                              );
                            })}
                          </DropdownMenuSubContent>
                        </DropdownMenuPortal>
                      </DropdownMenuSub>
                    );
                  })}
                {scorer_events && Object.entries(scorer_events).length == 0 && (
                  <DropdownMenuItem asChild>
                    <Link
                      href="/org/insights/events"
                      className="flex items-center px-2 py-1.5 text-sm cursor-pointer hover:bg-accent hover:text-accent-foreground focus:bg-accent focus:text-accent-foreground"
                    >
                      <TextSearch className="size-4 mr-2 flex-shrink-0" />
                      <span className="truncate">Setup scorers</span>
                    </Link>
                  </DropdownMenuItem>
                )}
              </DropdownMenuSubContent>
            </DropdownMenuPortal>
          </DropdownMenuSub>
          {/* Category */}
          <DropdownMenuSub>
            <DropdownMenuSubTrigger>
              <Shapes className="size-4 mr-2" />
              <span>Classifiers</span>
            </DropdownMenuSubTrigger>
            <DropdownMenuPortal>
              <DropdownMenuSubContent>
                {category_events &&
                  Object.entries(category_events).map(([event_name, event]) => {
                    if (!event.id || !event.score_range_settings?.categories) {
                      return null;
                    }

                    return (
                      <DropdownMenuSub key={"category_value_" + event.id}>
                        <DropdownMenuSubTrigger>
                          <span>{event_name}</span>
                        </DropdownMenuSubTrigger>
                        <DropdownMenuPortal>
                          <DropdownMenuSubContent className="overflow-y-auto max-h-[40rem]">
                            {event.score_range_settings.categories.map(
                              (category) => {
                                const eventId = event.id as string;
                                return (
                                  <DropdownMenuItem
                                    key={category}
                                    onClick={() => {
                                      setDataFilters({
                                        ...dataFilters,
                                        classifier_value: {
                                          [eventId]: category,
                                        },
                                      });
                                      resetPagination();
                                    }}
                                  >
                                    {category}
                                  </DropdownMenuItem>
                                );
                              },
                            )}
                          </DropdownMenuSubContent>
                        </DropdownMenuPortal>
                      </DropdownMenuSub>
                    );
                  })}
                {category_events &&
                  Object.entries(category_events).length == 0 && (
                    <DropdownMenuItem asChild>
                      <Link
                        href="/org/insights/events"
                        className="flex items-center px-2 py-1.5 text-sm cursor-pointer hover:bg-accent hover:text-accent-foreground focus:bg-accent focus:text-accent-foreground"
                      >
                        <TextSearch className="size-4 mr-2 flex-shrink-0" />
                        <span className="truncate">Setup classifiers</span>
                      </Link>
                    </DropdownMenuItem>
                  )}
              </DropdownMenuSubContent>
            </DropdownMenuPortal>
          </DropdownMenuSub>
          {/* Language */}
          <DropdownMenuSub>
            <DropdownMenuSubTrigger>
              <Languages className="size-4 mr-2" />
              <span>Language</span>
            </DropdownMenuSubTrigger>
            <DropdownMenuPortal>
              <DropdownMenuSubContent>
                {languageFilterOptions && languageFilterOptions.length == 0 && (
                  <DropdownMenuItem disabled>
                    No language available
                  </DropdownMenuItem>
                )}
                {languageFilterOptions &&
                  languageFilterOptions.map(
                    (languageFilterOption: LanguageFilterOption) => {
                      return (
                        <DropdownMenuItem
                          key={languageFilterOption.value}
                          onClick={() => {
                            setDataFilters({
                              ...dataFilters,
                              language: languageFilterOption.value,
                            });
                            resetPagination();
                          }}
                          style={{
                            color:
                              dataFilters.language ===
                              languageFilterOption.value
                                ? "green"
                                : "inherit",
                          }}
                        >
                          {languageFilterOption.label}
                        </DropdownMenuItem>
                      );
                    },
                  )}
              </DropdownMenuSubContent>
            </DropdownMenuPortal>
          </DropdownMenuSub>
          {/* Sentiment */}
          <DropdownMenuSub>
            <DropdownMenuSubTrigger>
              <SmilePlus className="size-4 mr-2" />
              <span>Sentiment</span>
            </DropdownMenuSubTrigger>
            <DropdownMenuPortal>
              <DropdownMenuSubContent>
                <DropdownMenuItem
                  onClick={() => {
                    setDataFilters({
                      ...dataFilters,
                      sentiment: "positive",
                    });
                    resetPagination();
                  }}
                  style={{
                    color:
                      dataFilters.sentiment === "positive"
                        ? "green"
                        : "inherit",
                  }}
                >
                  <Smile className="size-4 mr-2" />
                  <span>Positive</span>
                </DropdownMenuItem>
                <DropdownMenuItem
                  onClick={() => {
                    setDataFilters({
                      ...dataFilters,
                      sentiment: "neutral",
                    });
                    resetPagination();
                  }}
                  style={{
                    color:
                      dataFilters.sentiment === "neutral" ? "green" : "inherit",
                  }}
                >
                  <Meh className="size-4 mr-2" />
                  <span>Neutral</span>
                </DropdownMenuItem>
                <DropdownMenuItem
                  onClick={() => {
                    setDataFilters({
                      ...dataFilters,
                      sentiment: "mixed",
                    });
                    resetPagination();
                  }}
                  style={{
                    color:
                      dataFilters.sentiment === "mixed" ? "green" : "inherit",
                  }}
                >
                  <Annoyed className="size-4 mr-2" />
                  <span>Mixed</span>
                </DropdownMenuItem>
                <DropdownMenuItem
                  onClick={() => {
                    setDataFilters({
                      ...dataFilters,
                      sentiment: "negative",
                    });
                    resetPagination();
                  }}
                  style={{
                    color:
                      dataFilters.sentiment === "negative" ? "red" : "inherit",
                  }}
                >
                  <Frown className="size-4 mr-2" />
                  <span>Negative</span>
                </DropdownMenuItem>
              </DropdownMenuSubContent>
            </DropdownMenuPortal>
          </DropdownMenuSub>
          <div>
            {variant === "tasks" && (
              <DropdownMenuSub>
                <DropdownMenuSubTrigger>
                  <List className="size-4 mr-2" />
                  Message position
                </DropdownMenuSubTrigger>
                <DropdownMenuSubContent>
                  <DropdownMenuItem
                    onClick={() => {
                      const currentIsLastTask =
                        dataFilters.is_last_task ?? false;
                      setDataFilters({
                        ...dataFilters,
                        is_last_task: !currentIsLastTask,
                      });
                      resetPagination();
                    }}
                  >
                    Is last message
                  </DropdownMenuItem>
                </DropdownMenuSubContent>
              </DropdownMenuSub>
            )}
          </div>
          {variant == "tasks" && (
            <DropdownMenuSub>
              <DropdownMenuSubTrigger>
                <Code className="size-4 mr-2" />
                <span>Metadata</span>
              </DropdownMenuSubTrigger>
              <DropdownMenuPortal>
                <DropdownMenuSubContent className="overflow-y-auto max-h-[40rem]">
                  {stringFields && Object.entries(stringFields).length == 0 && (
                    <DropdownMenuItem disabled>
                      No metadata available
                    </DropdownMenuItem>
                  )}
                  {stringFields &&
                    Object.entries(stringFields).map(([field, values]) => {
                      return (
                        <DropdownMenuSub key={field}>
                          <DropdownMenuSubTrigger>
                            <span>{field}</span>
                          </DropdownMenuSubTrigger>
                          <DropdownMenuPortal>
                            <DropdownMenuSubContent className="overflow-y-auto max-h-[40rem]">
                              {values.map((value) => {
                                return (
                                  <DropdownMenuItem
                                    key={value}
                                    onClick={() => {
                                      setDataFilters({
                                        ...dataFilters,
                                        metadata: {
                                          ...dataFilters.metadata,
                                          [field]: value,
                                        },
                                      });
                                      resetPagination();
                                    }}
                                  >
                                    {field !== "language"
                                      ? value
                                        ? value.length > 50
                                          ? value.substring(0, 50) + "..."
                                          : value
                                        : "-"
                                      : getLanguageLabel(value)}
                                  </DropdownMenuItem>
                                );
                              })}
                            </DropdownMenuSubContent>
                          </DropdownMenuPortal>
                        </DropdownMenuSub>
                      );
                    })}
                </DropdownMenuSubContent>
              </DropdownMenuPortal>
            </DropdownMenuSub>
          )}
          <DropdownMenuSub>
            <DropdownMenuSubTrigger>
              <Boxes className="size-4 mr-2" />
              <span>Clusterings</span>
            </DropdownMenuSubTrigger>
            <DropdownMenuPortal>
              <DropdownMenuSubContent className="overflow-y-auto max-h-[30rem]">
                {clusterings && clusterings.length == 0 && (
                  <DropdownMenuItem disabled>
                    No clusterings available
                  </DropdownMenuItem>
                )}
                {clusterings &&
                  clusterings.map((clustering) => {
                    return (
                      <DropdownMenuSub key={clustering.id}>
                        <DropdownMenuSubTrigger>
                          {clustering?.name ??
                            formatUnixTimestampToLiteralDatetime(
                              clustering.created_at,
                            )}
                        </DropdownMenuSubTrigger>
                        <DropdownMenuPortal>
                          <DropdownMenuSubContent className="overflow-y-auto max-h-[40rem]">
                            <DropdownMenuItem
                              onClick={() => {
                                setDataFilters({
                                  ...dataFilters,
                                  clustering_id: clustering.id,
                                  clusters_ids: null,
                                });
                                resetPagination();
                              }}
                            >
                              <Boxes className="size-4 mr-2" />
                              <span>All clusters</span>
                            </DropdownMenuItem>
                            {clustering.clusters?.map((cluster) => {
                              return (
                                <DropdownMenuItem
                                  key={cluster.id}
                                  onClick={() => {
                                    setDataFilters({
                                      ...dataFilters,
                                      clustering_id: clustering.id,
                                      clusters_ids: [cluster.id],
                                    });
                                    resetPagination();
                                  }}
                                >
                                  {cluster.name}
                                </DropdownMenuItem>
                              );
                            })}
                          </DropdownMenuSubContent>
                        </DropdownMenuPortal>
                      </DropdownMenuSub>
                    );
                  })}
              </DropdownMenuSubContent>
            </DropdownMenuPortal>
          </DropdownMenuSub>
          <DropdownMenuSub>
            <DropdownMenuSubTrigger>
              <UserRound className="size-4 mr-2" />
              <span>Users</span>
            </DropdownMenuSubTrigger>
            <DropdownMenuPortal>
              <DropdownMenuSubContent className="overflow-y-auto max-h-[30rem]">
                {dataFilters.exclude_users !== null && (
                  <>
                    <DropdownMenuItem
                      onClick={() => {
                        // Override the event_name filter
                        // TODO: Allow multiple event_name filters
                        setDataFilters({
                          ...dataFilters,
                          exclude_users: true,
                        });
                        resetPagination();
                      }}
                      style={{
                        color: dataFilters.exclude_users ? "green" : "inherit",
                      }}
                    >
                      Exclude users in settings
                    </DropdownMenuItem>
                    <DropdownMenuItem asChild>
                      <Link
                        href="/org/settings/project"
                        className="flex items-center px-2 py-1.5 text-sm cursor-pointer hover:bg-accent hover:text-accent-foreground focus:bg-accent focus:text-accent-foreground"
                      >
                        <TextSearch className="size-4 mr-2 flex-shrink-0" />
                        <span className="truncate">Manage list</span>
                      </Link>
                    </DropdownMenuItem>
                  </>
                )}
                {dataFilters.exclude_users === null && (
                  <Link
                    href="/org/settings/project"
                    className="flex items-center px-2 py-1.5 text-sm cursor-pointer hover:bg-accent hover:text-accent-foreground focus:bg-accent focus:text-accent-foreground"
                  >
                    <TextSearch className="size-4 mr-2 flex-shrink-0" />
                    <span className="truncate">Setup list</span>
                  </Link>
                )}
              </DropdownMenuSubContent>
            </DropdownMenuPortal>
          </DropdownMenuSub>
          {/* Toggle search bar */}
          <DropdownMenuSeparator />
          <DropdownMenuItem
            onClick={() => {
              setShowSearchBar(!showSearchBar);
            }}
            className="flex justify-between items-center"
          >
            <div className="flex flex-row items-center">
              <MagnifyingGlassIcon className="size-4 mr-2" />
              Filter by id
            </div>
            {showSearchBar ? (
              <EyeOpenIcon className="size-4 ml-2" />
            ) : (
              <EyeClosedIcon className="size-4 ml-2" />
            )}
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
};

export default FilterComponent;
