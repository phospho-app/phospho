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
      <TasksDataviz />
      <TasksTable />
    </>
  );
};

export default Tasks;
