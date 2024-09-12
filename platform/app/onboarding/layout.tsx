"use client";

import FetchOrgProject from "@/components/fetch-data/fetch-org-project";
import { Button } from "@/components/ui/button";
import { navigationStateStore } from "@/store/store";
import { useLogoutFunction } from "@propelauth/nextjs/client";
import { useRouter } from "next/navigation";

import "../globals.css";

export default function OnboardingLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const logoutFn = useLogoutFunction();

  const setSelectedOrgId = navigationStateStore(
    (state) => state.setSelectedOrgId,
  );
  const setproject_id = navigationStateStore((state) => state.setproject_id);
  const router = useRouter();

  return (
    <>
      <FetchOrgProject />
      <section>
        <div className="flex flex-row justify-between items-bottom p-8">
          <div>
            <h2
              className="text-3xl font-semibold text-green-500 pt-0"
              style={{
                position: "fixed",
              }}
            >
              phospho
            </h2>
          </div>
          <div>
            <Button
              variant="link"
              className="text-muted-foreground"
              onClick={async () => {
                // Reset the navigation store
                setSelectedOrgId(null);
                setproject_id(null);
                await logoutFn().then(() => {
                  navigationStateStore.persist.clearStorage();
                  router.push("/authenticate");
                });
              }}
            >
              Log out
            </Button>
          </div>
        </div>
        <div className="max-w-screen overflow-hidden ">
          {/* <div className="flex flex-col align-middle"> */}
          <div className="flex flex-col items-center justify-center p-4">
            {children}
          </div>
        </div>
      </section>
    </>
  );
}
