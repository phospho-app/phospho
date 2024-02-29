import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";

import { Project, HasEnoughLabelledTasks } from "../models/project";
import { Event } from "../models/events";
import { Task, TaskWithEvents } from "../models/tasks";
import { SessionWithEvents } from "../models/sessions";
import { Test } from "@/models/tests";
import { OrgMetadata } from "@/models/organizations";

import { ColumnFiltersState, Updater } from "@tanstack/react-table";
import { UserMetadata } from "@/models/metadata";
import { ABTest } from "@/models/abtests";

// The navigation store stores local state, that are based
// on what buttons were clicked or selected
// It's persisted to local storage
interface navigationState {
  selectedOrgId: string | null | undefined;
  setSelectedOrgId: (orgId: string | null) => void;
  selectedProject: Project | null | undefined;
  setSelectedProject: (project: Project | null) => void;

  tasksColumnsFilters: ColumnFiltersState;
  setTasksColumnsFilters: (
    tasksColumnsFilters: Updater<ColumnFiltersState>
  ) => void;
  sessionsColumnsFilters: ColumnFiltersState;
  setSessionsColumnsFilters: (
    sessionsColumnsFilters: Updater<ColumnFiltersState>
  ) => void;
}

export const navigationStateStore = create(
  persist<navigationState>(
    (set) => ({
      selectedOrgId: undefined,
      setSelectedOrgId: (orgId: string | null) =>
        set((state) => ({ selectedOrgId: orgId })),

      selectedProject: undefined,
      setSelectedProject: (project: Project | null) =>
        set((state) => ({ selectedProject: project })),

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
      sessionsColumnsFilters: [],
      setSessionsColumnsFilters: (
        updaterOrValue: Updater<ColumnFiltersState>
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
    }),
    {
      name: "navigation-storage",
      storage: createJSONStorage(() => sessionStorage),
    }
  )
);

// The data state store share the data between the different components
// Those data were fetched from the backend
// Not persist when you reload
interface dataState {
  selectedOrgMetadata: OrgMetadata | null;
  setSelectOrgMetadata: (selectOrgMetadata: OrgMetadata) => void;

  projects: Project[] | null;
  setProjects: (projects: Project[]) => void;

  hasTasks: boolean | null;
  setHasTasks: (hasTasks: boolean | null) => void;
  hasSessions: boolean | null;
  setHasSessions: (hasSessions: boolean | null) => void;
  hasLabelledTasks: HasEnoughLabelledTasks | null;
  setHasLabelledTasks: (
    hasLabelledTasks: HasEnoughLabelledTasks | null
  ) => void;

  tasksWithEvents: TaskWithEvents[];
  setTasksWithEvents: (tasks: TaskWithEvents[]) => void;
  sessionsWithEvents: SessionWithEvents[];
  setSessionsWithEvents: (sessions: SessionWithEvents[]) => void;
  events: Event[];
  setEvents: (events: Event[]) => void;

  tests: Test[];
  setTests: (tests: Test[]) => void;
  abTests: ABTest[];
  setABTests: (abTests: ABTest[]) => void;

  tasksWithoutHumanLabel: Task[] | null;
  setTasksWithoutHumanLabel: (tasks: Task[]) => void;

  usersMetadata: UserMetadata[];
  setUsersMetadata: (usersMetadata: UserMetadata[]) => void;

  uniqueEventNames: string[];
  setUniqueEventNames: (uniqueEventNames: string[]) => void;
  uniqueEventNamesInData: string[];
  setUniqueEventNamesInData: (uniqueEventNamesInData: string[]) => void;
}

export const dataStateStore = create<dataState>((set) => ({
  selectedOrgMetadata: null,
  setSelectOrgMetadata: (selectOrgMetadata: OrgMetadata) =>
    set((state) => ({ selectedOrgMetadata: selectOrgMetadata })),

  projects: null,
  setProjects: (projects: Project[]) =>
    set((state) => ({ projects: projects })),

  hasTasks: null,
  setHasTasks: (hasTasks: boolean | null) =>
    set((state) => ({ hasTasks: hasTasks })),
  hasSessions: null,
  setHasSessions: (hasSessions: boolean | null) =>
    set((state) => ({ hasSessions: hasSessions })),
  hasLabelledTasks: null,
  setHasLabelledTasks: (hasLabelledTasks: HasEnoughLabelledTasks | null) =>
    set((state) => ({ hasLabelledTasks: hasLabelledTasks })),

  tasksWithEvents: [],
  setTasksWithEvents: (tasks: TaskWithEvents[]) =>
    set((state) => ({ tasksWithEvents: tasks })),
  sessionsWithEvents: [],
  setSessionsWithEvents: (sessions: SessionWithEvents[]) =>
    set((state) => ({ sessionsWithEvents: sessions })),
  events: [],
  setEvents: (events: Event[]) => set((state) => ({ events: events })),

  tests: [],
  setTests: (tests: Test[]) => set((state) => ({ tests: tests })),
  abTests: [],
  setABTests: (abTests: ABTest[]) => set((state) => ({ abTests: abTests })),

  tasksWithoutHumanLabel: null,
  setTasksWithoutHumanLabel: (tasks: Task[]) =>
    set((state) => ({ tasksWithoutHumanLabel: tasks })),

  usersMetadata: [],
  setUsersMetadata: (usersMetadata: UserMetadata[]) =>
    set((state) => ({ usersMetadata: usersMetadata })),

  uniqueEventNames: [],
  setUniqueEventNames: (uniqueEventNames: string[]) =>
    set((state) => ({ uniqueEventNames: uniqueEventNames })),
  uniqueEventNamesInData: [],
  setUniqueEventNamesInData: (uniqueEventNamesInData: string[]) =>
    set((state) => ({ uniqueEventNamesInData: uniqueEventNamesInData })),
}));
