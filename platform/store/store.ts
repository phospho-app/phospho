import {
  CustomDateRange,
  Event,
  HasEnoughLabelledTasks,
  OrgMetadata,
  Project,
  SessionWithEvents,
  Task,
  TaskWithEvents,
} from "@/models/models";
import {
  ColumnFiltersState,
  PaginationState,
  SortingState,
  Updater,
} from "@tanstack/react-table";
import { addDays } from "date-fns";
import { DateRange } from "react-day-picker";
import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";

// The navigation store stores local state, that are based
// on what buttons were clicked or selected
// It's persisted to local storage
interface navigationState {
  selectedOrgId: string | null | undefined;
  setSelectedOrgId: (orgId: string | null) => void;
  project_id: string | null | undefined;
  setproject_id: (projectId: string | null) => void;

  tasksColumnsFilters: ColumnFiltersState;
  setTasksColumnsFilters: (
    tasksColumnsFilters: Updater<ColumnFiltersState>,
  ) => void;
  tasksPagination: PaginationState;
  setTasksPagination: (taskPagination: Updater<PaginationState>) => void;
  tasksSorting: SortingState;
  setTasksSorting: (taskSorting: Updater<SortingState>) => void;

  sessionsColumnsFilters: ColumnFiltersState;
  setSessionsColumnsFilters: (
    sessionsColumnsFilters: Updater<ColumnFiltersState>,
  ) => void;
  sessionsPagination: PaginationState;
  setSessionsPagination: (sessionsPagination: Updater<PaginationState>) => void;
  sessionsSorting: SortingState;
  setSessionsSorting: (sessionsSorting: Updater<SortingState>) => void;

  dateRangePreset: string | null;
  dateRange: CustomDateRange | undefined;
  setDateRangePreset: (dateRangePreset: string | null) => void;
  setDateRange: (dateRange: DateRange) => void;
}

export const navigationStateStore = create(
  persist<navigationState>(
    (set) => ({
      selectedOrgId: undefined,
      setSelectedOrgId: (orgId: string | null) =>
        set((state) => ({ selectedOrgId: orgId })),

      project_id: null,
      setproject_id: (projectId: string | null) =>
        set((state) => ({ project_id: projectId })),

      tasksColumnsFilters: [],
      setTasksColumnsFilters: (updaterOrValue: Updater<ColumnFiltersState>) =>
        set((state) => {
          if (typeof updaterOrValue === "function") {
            const update = updaterOrValue(state.tasksColumnsFilters);
            return {
              tasksColumnsFilters: update,
            };
          }
          return {
            tasksColumnsFilters: updaterOrValue,
          };
        }),
      tasksPagination: {
        pageSize: 10,
        pageIndex: 0,
      } as PaginationState,
      setTasksPagination: (taskPagination: Updater<PaginationState>) =>
        set((state) => {
          if (typeof taskPagination === "function") {
            const update = taskPagination(state.tasksPagination);
            return {
              tasksPagination: update,
            };
          }
          return {
            tasksPagination: taskPagination,
          };
        }),
      tasksSorting: [
        {
          id: "created_at",
          desc: false,
        },
      ],
      setTasksSorting: (updaterOrValue: Updater<SortingState>) =>
        set((state) => {
          if (typeof updaterOrValue === "function") {
            const update = updaterOrValue(state.tasksSorting);
            return {
              tasksSorting: update,
            };
          }
          return {
            tasksSorting: updaterOrValue,
          };
        }),

      sessionsColumnsFilters: [],
      setSessionsColumnsFilters: (
        updaterOrValue: Updater<ColumnFiltersState>,
      ) =>
        set((state) => {
          if (typeof updaterOrValue === "function") {
            const update = updaterOrValue(state.sessionsColumnsFilters);
            return {
              sessionsColumnsFilters: update,
            };
          }
          return {
            sessionsColumnsFilters: updaterOrValue,
          };
        }),
      sessionsPagination: {
        pageSize: 10,
        pageIndex: 0,
      } as PaginationState,
      setSessionsPagination: (sessionsPagination: Updater<PaginationState>) =>
        set((state) => {
          if (typeof sessionsPagination === "function") {
            const update = sessionsPagination(state.sessionsPagination);
            return {
              sessionsPagination: update,
            };
          }
          return {
            sessionsPagination: sessionsPagination,
          };
        }),
      sessionsSorting: [
        {
          id: "created_at",
          desc: false,
        },
      ],
      setSessionsSorting: (updaterOrValue: Updater<SortingState>) =>
        set((state) => {
          console.log("sorting updaterOrValue");
          console.log(updaterOrValue);
          if (typeof updaterOrValue === "function") {
            const update = updaterOrValue(state.sessionsSorting);
            return {
              sessionsSorting: update,
            };
          }
          return {
            sessionsSorting: updaterOrValue,
          };
        }),

      dateRangePreset: "all-time",
      dateRange: {
        from: undefined,
        to: undefined,
        created_at_start: undefined,
        created_at_end: undefined,
      } as CustomDateRange,
      setDateRangePreset: (dateRangePreset: string | null) => {
        // The date range preset and the date range are linked
        // We also store the timestamp. Note: the timestamp is in seconds

        // If the date range preset is null, we reset the date range
        if (dateRangePreset === null) {
          set((state) => ({
            dateRangePreset: null,
            dateRange: undefined,
          }));
          return;
        }

        // Otherwise, we set the date range based on the date range preset
        const dateRangePresetToRange = new Map<string, CustomDateRange>([
          [
            "last-24-hours",
            {
              from: addDays(new Date(), -1),
              to: new Date(),
              created_at_start: Date.now() / 1000 - 24 * 60 * 60,
              created_at_end: undefined,
            },
          ],
          [
            "last-7-days",
            {
              from: addDays(new Date(), -7),
              to: undefined,
              created_at_start: Date.now() / 1000 - 7 * 24 * 60 * 60,
              created_at_end: undefined,
            },
          ],
          [
            "last-30-days",
            {
              from: addDays(new Date(), -30),
              to: undefined,
              created_at_start: Date.now() / 1000 - 30 * 24 * 60 * 60,
              created_at_end: undefined,
            },
          ],
          [
            "all-time",
            {
              from: undefined,
              to: undefined,
              created_at_start: undefined,
              created_at_end: undefined,
            },
          ],
        ]);

        set((state) => ({
          dateRangePreset: dateRangePreset,
          dateRange: dateRangePresetToRange.get(dateRangePreset),
        }));
      },
      setDateRange: (dateRange: DateRange) => {
        // If the date range is directly set without a preset, we reset the date range preset
        set((state) => ({
          dateRangePreset: null,
          dateRange: {
            from: dateRange.from,
            to: dateRange.to,
            created_at_start: dateRange.from
              ? dateRange.from.getTime() / 1000
              : undefined,
            created_at_end: dateRange.to
              ? dateRange.to.getTime() / 1000
              : undefined,
          },
        }));
      },
    }),

    {
      name: "navigation-storage",
      storage: createJSONStorage(() => sessionStorage),
    },
  ),
);

// The data state store share the data between the different components
// Those data were fetched from the backend
// Not persist when you reload
interface dataState {
  selectedOrgMetadata: OrgMetadata | null;
  setSelectOrgMetadata: (selectOrgMetadata: OrgMetadata) => void;

  projects: Project[] | null;
  setProjects: (projects: Project[]) => void;
  selectedProject: Project | null;
  setSelectedProject: (project: Project | null) => void;

  hasTasks: boolean | null;
  setHasTasks: (hasTasks: boolean | null) => void;
  hasSessions: boolean | null;
  setHasSessions: (hasSessions: boolean | null) => void;
  hasLabelledTasks: HasEnoughLabelledTasks | null;
  setHasLabelledTasks: (
    hasLabelledTasks: HasEnoughLabelledTasks | null,
  ) => void;

  tasksWithoutHumanLabel: Task[] | null;
  setTasksWithoutHumanLabel: (tasks: Task[]) => void;
}

export const dataStateStore = create<dataState>((set) => ({
  selectedOrgMetadata: null,
  setSelectOrgMetadata: (selectOrgMetadata: OrgMetadata) =>
    set((state) => ({ selectedOrgMetadata: selectOrgMetadata })),

  projects: null,
  setProjects: (projects: Project[]) =>
    set((state) => ({ projects: projects })),
  selectedProject: null,
  setSelectedProject: (project: Project | null) =>
    set((state) => ({ selectedProject: project })),

  hasTasks: null,
  setHasTasks: (hasTasks: boolean | null) =>
    set((state) => ({ hasTasks: hasTasks })),
  hasSessions: null,
  setHasSessions: (hasSessions: boolean | null) =>
    set((state) => ({ hasSessions: hasSessions })),
  hasLabelledTasks: null,
  setHasLabelledTasks: (hasLabelledTasks: HasEnoughLabelledTasks | null) =>
    set((state) => ({ hasLabelledTasks: hasLabelledTasks })),

  tasksWithoutHumanLabel: null,
  setTasksWithoutHumanLabel: (tasks: Task[]) =>
    set((state) => ({ tasksWithoutHumanLabel: tasks })),
}));
