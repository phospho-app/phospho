import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuPortal,
  DropdownMenuSeparator,
  DropdownMenuSub,
  DropdownMenuSubContent,
  DropdownMenuSubTrigger,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { authFetcher } from "@/lib/fetcher";
import { getLanguageLabel } from "@/lib/utils";
import { MetadataFieldsToUniqueValues } from "@/models/models";
import { navigationStateStore } from "@/store/store";
import { dataStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import {
  Annoyed,
  Calendar,
  CandlestickChart,
  Code,
  Flag,
  Frown,
  Languages,
  ListFilter,
  Meh,
  PenSquare,
  Smile,
  SmilePlus,
  ThumbsDown,
  ThumbsUp,
  X,
} from "lucide-react";
import React from "react";
import useSWR from "swr";

const RunAnalysisInPast = () => {
  return <div>Hey There !</div>;
};

export default RunAnalysisInPast;
