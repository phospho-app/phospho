"use client";

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
  const setproject_id = navigationStateStore((state) => state.setproject_id);

  return (
    <div
      onClick={async () => {
        // Reset the navigation store
        setSelectedOrgId(null);
        setproject_id(null);
        await logoutFn().then(() => router.push("/authenticate"));
      }}
    >
      Log Out
    </div>
  );
};

export default LogoutButton;
