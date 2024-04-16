"use client";

import CreateProjectButton from "@/components/navbar/create-project-button";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { dataStateStore } from "@/store/store";
import { Sparkles, Star, Users } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { SelectProjectButton } from "./navbar/select-project-dropdown";
// zustand state management
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
      <div className="relative flex-grow max-h-[calc(100vh-6rem)] flex flex-col border-r border-gray-200 py-4 overflow-y-auto">
        <div>
          <div className="space-y-1">
            <Link href="/org/transcripts/tasks">
              <Button
                variant={
                  pathname.startsWith("/org/transcripts")
                    ? "secondary"
                    : "ghost"
                }
                className="w-full justify-start"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  width="24"
                  height="24"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  className="mr-2 h-4 w-4"
                >
                  <path d="m3 17 2 2 4-4" />
                  <path d="m3 7 2 2 4-4" />
                  <path d="M13 6h8" />
                  <path d="M13 12h8" />
                  <path d="M13 18h8" />
                </svg>
                Transcripts
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
            <Link href="/org/insights">
              <Button
                variant={
                  pathname.startsWith("/org/insights") ? "secondary" : "ghost"
                }
                className="w-full justify-start"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  className="mr-2 h-4 w-4"
                >
                  <path d="M21 6H3" />
                  <path d="M10 12H3" />
                  <path d="M10 18H3" />
                  <circle cx="17" cy="15" r="3" />
                  <path d="m21 19-1.9-1.9" />
                </svg>
                Insights
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
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  className="mr-2 h-4 w-4"
                >
                  <path d="M2 18h1.4c1.3 0 2.5-.6 3.3-1.7l6.1-8.6c.7-1.1 2-1.7 3.3-1.7H22" />
                  <path d="m18 2 4 4-4 4" />
                  <path d="M2 6h1.9c1.5 0 2.9.9 3.6 2.2" />
                  <path d="M22 18h-5.9c-1.3 0-2.6-.7-3.3-1.8l-.5-.8" />
                  <path d="m18 14 4 4-4 4" />
                </svg>
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
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  width="18"
                  height="18"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  className="mr-2 h-4 w-4"
                >
                  <path d="M21 7 6.82 21.18a2.83 2.83 0 0 1-3.99-.01v0a2.83 2.83 0 0 1 0-4L17 3" />
                  <path d="m16 2 6 6" />
                  <path d="M12 16H4" />
                </svg>
                Tests
              </Button>
            </Link>
          </div>
          <div>
            <Separator />
            <Link href="/org/settings">
              <Button
                variant={
                  pathname.startsWith("/org/settings") ? "secondary" : "ghost"
                }
                className="w-full justify-start"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  className="mr-2 h-4 w-4"
                >
                  <path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z" />
                  <circle cx="12" cy="12" r="3" />
                </svg>
                Settings
              </Button>
            </Link>
          </div>
        </div>

        <div className="flex justify-center mx-2 mb-4 mt-4">
          {selectedOrgMetadata &&
            selectedOrgMetadata?.plan === "hobby" &&
            hasTasks && (
              <Card>
                <CardContent className="flex justify-center mb-0">
                  <div>
                    <div className="flex items-baseline">
                      <Sparkles className="h-4 w-4 text-green-500 mr-1" />
                      <h2 className="font-semibold mt-4 mb-2">
                        Complete setup now
                      </h2>
                    </div>
                    <p className="mb-2">
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
