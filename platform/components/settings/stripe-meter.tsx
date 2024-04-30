import { authFetcher } from "@/lib/fetcher";
import { navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import React from "react";
import useSWR from "swr";

const StripeMeter: React.FC = () => {
  const selectedOrgId = navigationStateStore((state) => state.selectedOrgId);
  const { accessToken } = useUser();

  const { data: credits_used } = useSWR(
    selectedOrgId
      ? [`/api/organizations/${selectedOrgId}/update-usage`, accessToken]
      : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "GET"),
    {
      keepPreviousData: true,
    },
  );

  if (selectedOrgId && typeof credits_used === "number") {
    return (
      <div className="stripe-meter">
        You have spent ${credits_used / 1000} so far this month
      </div>
    );
  }

  return (
    <div className="stripe-meter">
      Updating your total spending for the month...
    </div>
  );
};

export default StripeMeter;
