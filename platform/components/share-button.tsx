import { Spinner } from "@/components/small-spinner";
import {
  AlertDialog,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import { authFetcher } from "@/lib/fetcher";
import { cn } from "@/lib/utils";
import { navigationStateStore } from "@/store/store";
import { useRedirectFunctions, useUser } from "@propelauth/nextjs/client";
import { Share2 } from "lucide-react";
import React, { useState } from "react";
import useSWR from "swr";

import UpgradeButton from "./upgrade-button";

interface ShareButtonProps {
  className?: string;
  variant?:
    | "outline"
    | "link"
    | "default"
    | "destructive"
    | "secondary"
    | "ghost"
    | null
    | undefined;
}

const ShareButton: React.FC<ShareButtonProps> = ({
  className,
  variant = "outline",
}) => {
  const [isLoading, setIsLoading] = useState(false);
  const [showAlert, setShowAlert] = useState(false);
  const { redirectToOrgPage } = useRedirectFunctions();
  const { user, accessToken } = useUser();

  const org_id = navigationStateStore((state) => state.selectedOrgId);

  const { data: orgData } = useSWR(
    org_id
      ? [`/api/organizations/${org_id}/nb-users-and-plan`, accessToken]
      : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "GET"),
    { keepPreviousData: true },
  );
  const nbrUsersInOrg: number = orgData?.total_users;
  const orgPlan: string = orgData?.plan;

  if (!org_id) {
    return null;
  }

  // A user can invite others if they have the pro tier or usage based plan
  // On the free tier, they can only invite others if they have less than 3 members
  const userCanInviteOthers =
    (user?.orgIdToOrgMemberInfo?.[org_id]?.hasPermission(
      "propelauth::can_invite",
    ) &&
      (nbrUsersInOrg < 3 || orgPlan === "usage_based" || orgPlan === "pro")) ??
    false;

  const handleShare = async () => {
    setIsLoading(true);
    if (userCanInviteOthers) {
      try {
        await redirectToOrgPage(org_id);
      } catch (error) {
        console.error("Error redirecting:", error);
        setIsLoading(false);
      }
    } else {
      setShowAlert(true);
      setIsLoading(false);
    }
  };

  return (
    <>
      <Button
        onClick={handleShare}
        disabled={isLoading}
        className={cn("h-8", className)}
        variant={variant}
      >
        {isLoading ? (
          <Spinner className="w-4 h-4 mr-2" />
        ) : (
          <Share2 className="w-4 h-4 mr-2" />
        )}
        Share
      </Button>

      <AlertDialog open={showAlert} onOpenChange={setShowAlert}>
        <AlertDialogContent className="md:max-w-1/2 flex flex-col justify-between">
          <AlertDialogHeader>
            <AlertDialogTitle>Organization Size Limit Reached</AlertDialogTitle>
            <AlertDialogDescription>
              Your organization already has 3 or more members. To invite more
              members, please upgrade your plan.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <div className="flex justify-between">
            <AlertDialogCancel onClick={() => setShowAlert(false)}>
              Cancel
            </AlertDialogCancel>
            <UpgradeButton tagline="Upgrade plan" green={false} />
          </div>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
};

export default ShareButton;
export { ShareButton };
