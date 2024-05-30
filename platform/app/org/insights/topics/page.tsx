"use client";

import ComingSoon from "@/components/coming-soon";
import Topics from "@/components/insights/topics/topics";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCaption,
  TableCell,
  TableFooter,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { authFetcher } from "@/lib/fetcher";
import { Topic } from "@/models/models";
import { navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import { MessageCircleIcon } from "lucide-react";
import Link from "next/link";
import React, { useEffect, useState } from "react";
import useSWR from "swr";

const Page: React.FC<{}> = ({}) => {
  const { accessToken } = useUser();
  const project_id = navigationStateStore((state) => state.project_id);

  return (
    <>
      <ComingSoon />
      <Topics />
    </>
  );
};

export default Page;
