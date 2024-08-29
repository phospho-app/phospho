"use client";

import FetchOrgProject from "@/components/fetch-data/fetch-org-project";
import FullPageLoader from "@/components/full-page-loader";
import { useUser } from "@propelauth/nextjs/client";
import { useRouter } from "next/navigation";
import React from "react";

const Page: React.FC = () => {
  if (process.env.NODE_ENV === "production") {
    console.log = function () {};
  }

  const { loading, isLoggedIn } = useUser();
  const router = useRouter();
  if (!loading && !isLoggedIn) {
    router.push("/authenticate");
  }

  return (
    <>
      <FetchOrgProject />
      <FullPageLoader />
    </>
  );
};

export default Page;
