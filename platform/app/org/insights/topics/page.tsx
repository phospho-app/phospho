"use client";

import ComingSoon from "@/components/coming-soon";
import Topics from "@/components/insights/topics/topics";
import { useUser } from "@propelauth/nextjs/client";
import React from "react";

const Page: React.FC<{}> = ({}) => {
  const { accessToken } = useUser();
  return (
    <>
      <ComingSoon customMessage="This feature is still in alpha." />
      <Topics />
    </>
  );
};

export default Page;
