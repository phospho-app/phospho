"use client";

import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { dataStateStore } from "@/store/store";
import {
  ListChecks,
  Monitor,
  Settings,
  Shuffle,
  Sparkles,
  Star,
  TestTubeDiagonal,
  TextSearch,
  Users,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { Card, CardContent, CardHeader } from "./ui/card";
import UpgradeButton from "./upgrade-button";

export function Sidebar() {
  const selectedOrgMetadata = dataStateStore(
    (state) => state.selectedOrgMetadata,
  );
  const hasTasks = dataStateStore((state) => state.hasTasks);
  const pathname = usePathname();

  return (
    <>
      <div className="relative flex-grow max-h-[calc(100vh-6rem)] flex flex-col border-r py-4 overflow-y-auto border-secondary">
        <div>
          <Link href="/org/transcripts/tasks">
            <Button
              variant={
                pathname.startsWith("/org/transcripts") ? "secondary" : "ghost"
              }
              className="w-full justify-start"
            >
              <ListChecks size={16} className="mr-2" />
              Transcripts
            </Button>
          </Link>
          <Link href="/org/insights">
            <Button
              variant={
                pathname.startsWith("/org/insights") ? "secondary" : "ghost"
              }
              className="w-full justify-start"
            >
              <TextSearch size={16} className="mr-2" />
              Insights
            </Button>
          </Link>
          <Link href="/org/users">
            <Button
              variant={
                pathname.startsWith("/org/users") ? "secondary" : "ghost"
              }
              className="w-full justify-start"
            >
              <Users size={16} className="mr-2" />
              Users
            </Button>
          </Link>
          <Separator />
          <Link href="/org/ab-testing">
            <Button
              variant={
                pathname.startsWith("/org/ab-testing") ? "secondary" : "ghost"
              }
              className="w-full justify-start"
            >
              <Shuffle size={16} className="mr-2" />
              AB Testing
            </Button>
          </Link>
          <Link href="/org/tests">
            <Button
              variant={
                pathname.startsWith("/org/tests") ? "secondary" : "ghost"
              }
              className="w-full justify-start"
            >
              <TestTubeDiagonal size={16} className="mr-2" />
              Tests
            </Button>
          </Link>
          <Separator />
          <Link href="/org/settings">
            <Button
              variant={
                pathname.startsWith("/org/settings") ? "secondary" : "ghost"
              }
              className="w-full justify-start"
            >
              <Settings size={16} className="mr-2" />
              Settings
            </Button>
          </Link>
        </div>

        <div className="flex justify-center mx-2 mb-4 mt-4">
          {selectedOrgMetadata && selectedOrgMetadata?.plan === "hobby" && (
            <Card>
              <CardContent className="flex justify-center mb-0">
                <div>
                  <div className="flex items-baseline">
                    <Sparkles className="h-4 w-4 text-green-500 mr-1" />
                    <h2 className="font-semibold mt-4 mb-1">Complete setup</h2>
                  </div>
                  <p className="mb-2 text-sm">
                    Enable automatic evaluation and event detection
                  </p>
                  <div className="flex justify-center">
                    <UpgradeButton
                      tagline="Add payment method"
                      enlarge={false}
                      green={false}
                    />
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
          {selectedOrgMetadata && selectedOrgMetadata?.plan === "pro" && (
            <Card>
              <CardContent className="flex justify-center items-center mt-6">
                <Star size={16} className="mr-2" />
                Pro plan member
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </>
  );
}
