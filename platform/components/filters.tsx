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
import { authFetcher } from "@/lib/fetcher";
import { getLanguageLabel } from "@/lib/utils";
import { MetadataFieldsToUniqueValues } from "@/models/models";
import { navigationStateStore } from "@/store/store";
import { dataStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import { da } from "date-fns/locale";
import {
  Annoyed,
  Calendar,
  CandlestickChart,
  Code,
  Flag,
  Frown,
  Languages,
  ListFilter,
  Meh,
  PenSquare,
  Smile,
  SmilePlus,
  ThumbsDown,
  ThumbsUp,
  X,
} from "lucide-react";
import React from "react";
import useSWR from "swr";

const FilterComponent = ({
  variant = "tasks",
}: {
  variant: "tasks" | "sessions";
}) => {
  const setDataFilters = navigationStateStore((state) => state.setDataFilters);
  const dataFilters = navigationStateStore((state) => state.dataFilters);
  const selectedProject = dataStateStore((state) => state.selectedProject);
  const { accessToken } = useUser();
  const events = selectedProject?.settings?.events;

  const setSessionsPagination = navigationStateStore(
    (state) => state.setSessionsPagination,
  );
  const setTasksPagination = navigationStateStore(
    (state) => state.setTasksPagination,
  );
  const dateRange = navigationStateStore((state) => state.dateRange);

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
  console.log("languageFilterOptions", languageFilterOptions);

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

  // Number of active filters that are not the created_at_start and created_at_end
  const activeFilterCount =
    dataFilters &&
    Object.keys(dataFilters).filter(
      (key) => key !== "created_at_start" && key !== "created_at_end",
    ).length;

  if (!selectedProject) {
    return <></>;
  }

  return (
    <div>
      <DropdownMenu>
        <div className="flex align-items space-x-2">
          <DropdownMenuTrigger asChild>
            <Button variant="outline">
              <ListFilter className="h-4 w-4 mr-1" />
              Filters
            </Button>
          </DropdownMenuTrigger>
          {dataFilters.flag && (
            <Button
              className={`ml-2 color: ${dataFilters.flag === "success" ? "green" : "red"} `}
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
              <X className="h-4 w-4" />
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
              <X className="h-4 w-4 ml-2" />
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
                >
                  {dataFilters.event_name}
                  <X className="h-4 w-4 ml-2" />
                </Button>
              );
            })}
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
              <X className="h-4 w-4 ml-2" />
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
              <X className="h-4 w-4 ml-2" />
            </Button>
          )}
          {dataFilters.last_eval_source && (
            <Button
              variant="outline"
              onClick={() => {
                setDataFilters({
                  ...dataFilters,
                  last_eval_source: null,
                });
                resetPagination();
              }}
            >
              {dataFilters.last_eval_source}
              <X className="h-4 w-4 ml-2" />
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
                >
                  {key}:{" "}
                  {value.length > 20 ? value.substring(0, 20) + "..." : value}
                  <X className="h-4 w-4 ml-2" />
                </Button>
              );
            })}
          {dataFilters && activeFilterCount > 0 && (
            <Button
              variant="destructive"
              onClick={() => {
                setDataFilters({
                  created_at_start: dateRange?.created_at_start,
                  created_at_end: dateRange?.created_at_end,
                });
                resetPagination();
              }}
            >
              <X className="h-4 w-4 mr-1" />
              Clear all filters
            </Button>
          )}
        </div>
        <DropdownMenuContent className="w-56" align="start">
          <DropdownMenuLabel>Filters to apply</DropdownMenuLabel>
          <DropdownMenuSeparator />
          {/* Flag */}
          <DropdownMenuSub>
            <DropdownMenuSubTrigger>
              <Flag className="h-4 w-4 mr-2" />
              <span>Eval</span>
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
                  <ThumbsUp className="h-4 w-4 mr-2" />
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
                  <ThumbsDown className="h-4 w-4 mr-2" />
                  <span>Failure</span>
                </DropdownMenuItem>
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
                  <PenSquare className="h-4 w-4 mr-2" />
                  <span>Has notes </span>
                </DropdownMenuItem>
              </DropdownMenuSubContent>
            </DropdownMenuPortal>
          </DropdownMenuSub>
          {/* Events */}
          <DropdownMenuSub>
            <DropdownMenuSubTrigger>
              <Calendar className="h-4 w-4 mr-2" />
              <span>Events</span>
            </DropdownMenuSubTrigger>
            <DropdownMenuPortal>
              <DropdownMenuSubContent className="overflow-y-auto">
                {events &&
                  Object.entries(events).map(([event_name, event]) => {
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
              </DropdownMenuSubContent>
            </DropdownMenuPortal>
          </DropdownMenuSub>
          {/* Language */}
          <DropdownMenuSub>
            <DropdownMenuSubTrigger>
              <Languages className="h-4 w-4 mr-2" />
              <span>Language</span>
            </DropdownMenuSubTrigger>
            <DropdownMenuPortal>
              <DropdownMenuSubContent>
                {languageFilterOptions &&
                  languageFilterOptions.map((languageFilterOption: any) => {
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
                            dataFilters.language === languageFilterOption.value
                              ? "green"
                              : "inherit",
                        }}
                      >
                        {languageFilterOption.label}
                      </DropdownMenuItem>
                    );
                  })}
              </DropdownMenuSubContent>
            </DropdownMenuPortal>
          </DropdownMenuSub>
          {/* Sentiment */}
          <DropdownMenuSub>
            <DropdownMenuSubTrigger>
              <SmilePlus className="h-4 w-4 mr-2" />
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
                  <Smile className="h-4 w-4 mr-2" />
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
                  <Meh className="h-4 w-4 mr-2" />
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
                  <Annoyed className="h-4 w-4 mr-2" />
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
                  <Frown className="h-4 w-4 mr-2" />
                  <span>Negative</span>
                </DropdownMenuItem>
              </DropdownMenuSubContent>
            </DropdownMenuPortal>
          </DropdownMenuSub>
          {/* Last Eval Source */}
          <DropdownMenuSub>
            <DropdownMenuSubTrigger>
              <CandlestickChart className="h-4 w-4 mr-2" />
              <span>Last Eval Source</span>
            </DropdownMenuSubTrigger>
            <DropdownMenuPortal>
              <DropdownMenuSubContent>
                <DropdownMenuItem
                  onClick={() => {
                    setDataFilters({
                      ...dataFilters,
                      last_eval_source: "phospho",
                    });
                    resetPagination();
                  }}
                  style={{
                    color:
                      dataFilters.last_eval_source === "phospho"
                        ? "green"
                        : "inherit",
                  }}
                >
                  phospho
                </DropdownMenuItem>
                <DropdownMenuItem
                  onClick={() => {
                    setDataFilters({
                      ...dataFilters,
                      last_eval_source: "user",
                    });
                    resetPagination();
                  }}
                  style={{
                    color:
                      dataFilters.last_eval_source === "user"
                        ? "green"
                        : "inherit",
                  }}
                >
                  user
                </DropdownMenuItem>
              </DropdownMenuSubContent>
            </DropdownMenuPortal>
          </DropdownMenuSub>
          <DropdownMenuSub>
            <DropdownMenuSubTrigger>
              <Code className="h-4 w-4 mr-2" />
              <span>Metadata</span>
            </DropdownMenuSubTrigger>
            <DropdownMenuPortal>
              <DropdownMenuSubContent className="overflow-y-auto max-h-[40rem]">
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
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
};

export default FilterComponent;
