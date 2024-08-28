"use client";

import FetchOrgProject from "@/components/fetch-data/fetch-org-project";
import FullPageLoader from "@/components/full-page-loader";
import React from "react";

const Page: React.FC = () => {
  if (process.env.NODE_ENV === "production") {
    console.log = function () {};
  }

  return (
    <>
      <FetchOrgProject />
      <FullPageLoader />
    </>
  );
};

export default Page;
