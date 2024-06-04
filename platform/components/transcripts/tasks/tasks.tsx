"use client";

import { SendDataCallout } from "@/components/callouts/import-data";
import { RunClusteringCallout } from "@/components/callouts/run-clustering";
import React from "react";

import TasksDataviz from "./tasks-dataviz";
import { TasksTable } from "./tasks-table";

const Tasks: React.FC = () => {
  return (
    <>
      <SendDataCallout />
      <RunClusteringCallout />
      <div className="hidden h-full flex-1 flex-col space-y-2 md:flex relative">
        <TasksDataviz />
        <TasksTable />
      </div>
    </>
  );
};

export default Tasks;
