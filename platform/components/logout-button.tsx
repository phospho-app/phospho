"use client";

import { Button } from "@/components/ui/button";
import { navigationStateStore } from "@/store/store";
import { useLogoutFunction } from "@propelauth/nextjs/client";
import { useRouter } from "next/navigation";
import React from "react";

const LogoutButton: React.FC = () => {
  const logoutFn = useLogoutFunction();
  const router = useRouter();

  const setSelectedOrgId = navigationStateStore(
    (state) => state.setSelectedOrgId,
  );
  const setSelectedProject = navigationStateStore(
    (state) => state.setSelectedProject,
  );

  return (
    <Button
      className="text-muted-foreground hover:text-primary"
      variant="ghost"
      onClick={async () => {
        // Reset the navigation store
        setSelectedOrgId(null);
        setSelectedProject(null);
        await logoutFn().then(() => router.push("/authenticate"));
      }}
    >
      Log Out
    </Button>
  );
};

export default LogoutButton;
