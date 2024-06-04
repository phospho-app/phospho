"use client";

import ComingSoon from "@/components/coming-soon";
import Clusters from "@/components/insights/clusters/clusters";
import React from "react";

const Page: React.FC<{}> = ({}) => {
  return (
    <>
      <ComingSoon customMessage="This feature is still in alpha." />
      <Clusters />
    </>
  );
};

export default Page;
