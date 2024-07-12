"use client";

import { SendDataCallout } from "@/components/callouts/ImportData";
import { RunClusteringCallout } from "@/components/callouts/RunClustering";
import React from "react";

import TasksDataviz from "./TasksDataviz";
import { TasksTable } from "./TasksTable";

const Tasks: React.FC = () => {
  return (
    <>
      <SendDataCallout />
      <RunClusteringCallout />
      <TasksDataviz />
      <TasksTable />
    </>
  );
};

export default Tasks;
