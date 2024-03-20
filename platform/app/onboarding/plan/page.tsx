"use client";

import FullPageLoader from "@/components/full-page-loader";
import Pricing from "@/components/settings/pricing";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { navigationStateStore } from "@/store/store";
import { useLogoutFunction } from "@propelauth/nextjs/client";
import { useSearchParams } from "next/navigation";
import { useRouter } from "next/navigation";

export default function Page({ params }: { params: { id: string } }) {
  const router = useRouter();
  // This page is used during the onboarding for the user to pick a plan.
  // It is also used as a paywall when the user tries to access a page that
  // requires a plan.

  // It is disbaled in preview mode
  // In this case, users are redirected to the root page

  // This page is used during the onboarding for the user to pick a plan.
  // It is also used as a paywall when the user tries to access a page that
  // requires a plan.

  // It is disbaled in preview mode
  // In this case, users are redirected to the root page
  if (process.env.NEXT_PUBLIC_APP_ENV === "preview") {
    router.push("/org/transcripts/tasks");
  }

  if (process.env.NEXT_PUBLIC_APP_ENV === "preview") {
    return <FullPageLoader />;
  }

  const logoutFn = useLogoutFunction();

  const setSelectedOrgId = navigationStateStore(
    (state) => state.setSelectedOrgId,
  );
  const setproject_id = navigationStateStore((state) => state.setproject_id);

  const searchParams = useSearchParams();
  const redirect = searchParams.get("redirect");
  // if redirect=true, then the user is trying to access a page that requires a plan
  // The tagline will be different in this case
  const tagline =
    redirect === "true"
      ? "phospho billing is evolving. Please pick a plan to continue."
      : "You're almost there! Please pick a plan to get started with phospho.";

  return (
    <>
      <Card className="mb-3">
        <CardHeader>
          <h2 className="text-2xl font-bold">One more thing...</h2>
        </CardHeader>
        <CardContent>
          <p>{tagline}</p>
        </CardContent>
      </Card>
      <Pricing
        currentPlan={null}
        selectedPlan={"pro"}
        proPlanTagline="Try for free"
        displayHobbyCTA={true}
      />
      <div>
        <Button
          variant="link"
          className="text-gray-500"
          onClick={async () => {
            // Reset the navigation store
            setSelectedOrgId(null);
            setproject_id(null);
            await logoutFn().then(() => router.push("/authenticate"));
          }}
        >
          Log out
        </Button>
      </div>
    </>
  );
}
