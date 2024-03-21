import { Separator } from "@radix-ui/react-separator";
import { Check } from "lucide-react";
import Link from "next/link";

import { Button } from "../ui/button";
import { Card, CardContent, CardFooter, CardHeader } from "../ui/card";
import UpgradeButton from "../upgrade-button";

interface PricingData {
  tiers: {
    hobby: {
      title: string;
      price: string;
      tagline: string;
    };
    pro: {
      title: string;
      price: string;
      tagline: string;
    };
    enterprise: {
      title: string;
      price: string | null;
      tagline: string;
    };
  };
  criterias: {
    type: "title" | "section";
    label: string;
    tiers?: {
      hobby: string | number | boolean;
      pro: string | number | boolean;
      enterprise: string | number | boolean;
    };
  }[];
}

function CtaButton({
  currentPlan,
  tierName,
  proPlanTagline,
  displayHobbyCTA,
}: {
  currentPlan: string | null;
  tierName: string;
  proPlanTagline?: string;
  displayHobbyCTA?: boolean;
}) {
  if (currentPlan === tierName) {
    return <p className="text-green-500">Current Plan</p>;
  }

  if (tierName === "pro") {
    return <UpgradeButton tagline={proPlanTagline} />;
  }

  if (tierName === "enterprise") {
    return (
      <Link href="mailto:contact@phospho.app">
        <Button>Contact Sales</Button>
      </Link>
    );
  }

  if (tierName === "hobby" && displayHobbyCTA === true) {
    return (
      <Link href="https://github.com/phospho-app/phospho" target="_blank">
        <Button>Self host</Button>
      </Link>
    );
  }

  return <></>;
}

function CriteriaDisplay({ tierName, criteria }: any) {
  // if currentPlan not in criteria.tiers, then return nothing

  const { type, label, tiers } = criteria;

  if (type === "title") {
    // Don't return Support for the Hobby plan
    if (label === "Support" && tierName === "hobby") {
      return <></>;
    }
    return (
      <>
        <Separator orientation="horizontal" className="my-2 " />
        <h3 className="font-semibold">{label}</h3>
      </>
    );
  }
  // if currentPlan is not in criteria.tiers, then return nothing
  if (!tiers[tierName]) {
    return <></>;
  }

  // Don't return the Pricing section
  if (label === "Pricing") {
    return <></>;
  }

  // if currentPlan in criteria.tiers, then return the value
  // If value is a string, then return title: value
  // If value is a boolean and false, then return nothing
  // If value is a boolean and true, then return checkmark title
  // If value is a number, then return title: value

  if (typeof tiers[tierName] === "string") {
    return (
      <div>
        {label}: {tiers[tierName]}
      </div>
    );
  }

  if (typeof tiers[tierName] === "boolean") {
    if (tiers[tierName]) {
      return (
        <div className="flex items-center">
          <Check size={16} className="mr-1" /> {label}
        </div>
      );
    }
    return <></>;
  }

  if (typeof tiers[tierName] === "number") {
    return (
      <div>
        {label}: {tiers[tierName]}
      </div>
    );
  }
}

function PricingCard({
  currentPlan,
  selectedPlan,
  tierName,
  tier,
  pricingData,
  proPlanTagline,
  displayHobbyCTA,
}: {
  currentPlan: string | null;
  selectedPlan: string | null;
  tierName: string;
  tier: any;
  pricingData: PricingData;
  proPlanTagline?: string;
  displayHobbyCTA?: boolean;
}) {
  // If currentPlan = tier, then put a green
  // border around the card to show it's the current plan

  const border =
    selectedPlan === tierName ? "border-green-500 border-2" : "border-gray-300";

  return (
    <Card className={`${border} `}>
      <CardHeader className="pb-2">
        <h2 className="text-2xl font-bold mb-0">{tier.title}</h2>
        {selectedPlan === tierName && (
          <p className="text-green-500 font-semibold text-xl">{tier.tagline}</p>
        )}
        {selectedPlan !== tierName && (
          <div>
            <p className="font-semibold">{tier.tagline}</p>
          </div>
        )}
        <p className="font-light text-gray-500"> {tier.price}</p>
      </CardHeader>
      <CardContent className="mt-0">
        <div>
          {pricingData.criterias.map((criteria) => (
            <CriteriaDisplay
              tierName={tierName}
              criteria={criteria}
              key={criteria.label}
            />
          ))}
        </div>
      </CardContent>
      <CardFooter className="flex justify-center">
        <CtaButton
          currentPlan={currentPlan}
          tierName={tierName}
          proPlanTagline={proPlanTagline}
          displayHobbyCTA={displayHobbyCTA}
        />
      </CardFooter>
    </Card>
  );
}

export default function Pricing({
  currentPlan,
  selectedPlan,
  proPlanTagline,
  displayHobbyCTA,
}: {
  currentPlan: string | null;
  selectedPlan?: string | null;
  proPlanTagline?: string;
  displayHobbyCTA?: boolean;
}) {
  if (!selectedPlan) {
    selectedPlan = currentPlan;
  }

  const pricingData: PricingData = {
    tiers: {
      hobby: {
        title: "Open source",
        price: "Free",
        tagline: "Join the community!",
      },
      pro: {
        title: "Pro",
        price: "Cancel anytime",
        tagline: "Try for free for 15 days",
      },
      enterprise: {
        title: "Enterprise",
        price: "Custom pricing",
        tagline: "Enterprise-wide deployment",
      },
    },
    criterias: [
      { type: "title", label: "Usage" },
      {
        type: "section",
        label: "Pricing",
        tiers: {
          hobby: "0$ up to 10K logs",
          pro: "1$ / 10K logs",
          enterprise: "Custom",
        },
      },
      {
        type: "section",
        label: "Team members",
        tiers: {
          hobby: "Self-hosted",
          pro: "15 max",
          enterprise: "Custom",
        },
      },
      {
        type: "section",
        label: "Custom events",
        tiers: {
          hobby: "Self-billed",
          pro: "100 different",
          enterprise: "Unlimited",
        },
      },
      {
        type: "title",
        label: "Features",
      },
      {
        type: "section",
        label: "Custom Evaluations",
        tiers: { hobby: true, pro: true, enterprise: true },
      },
      {
        type: "section",
        label: "Events Detection",
        tiers: { hobby: true, pro: true, enterprise: true },
      },
      {
        type: "section",
        label: "Cloud hosting",
        tiers: { hobby: false, pro: true, enterprise: true },
      },
      {
        type: "section",
        label: "Team Workspace",
        tiers: { hobby: false, pro: true, enterprise: true },
      },
      {
        type: "section",
        label: "SSO + SAML",
        tiers: { hobby: false, pro: false, enterprise: true },
      },
      {
        type: "section",
        label: "Higher Rate Limits",
        tiers: { hobby: false, pro: false, enterprise: true },
      },
      { type: "title", label: "Support" },
      {
        type: "section",
        label: "Dedicated Support",
        tiers: { hobby: false, pro: true, enterprise: true },
      },
      {
        type: "section",
        label: "White Glove Migration",
        tiers: { hobby: false, pro: false, enterprise: true },
      },
      {
        type: "section",
        label: "Priority on Feature Release",
        tiers: { hobby: false, pro: false, enterprise: true },
      },
    ],
  };

  //   const allPricingCards = Object.entries(pricingData.tiers).map(
  //     ([tierName, tier]) => (
  //       <PricingCard
  //         currentPlan={plan}
  //         tierName={tierName}
  //         tier={tier}
  //         pricingData={pricingData}
  //       />
  //     )
  //   );

  const hobbyPricingCard = (
    <PricingCard
      currentPlan={currentPlan}
      selectedPlan={selectedPlan}
      tierName="hobby"
      tier={pricingData.tiers.hobby}
      pricingData={pricingData}
      displayHobbyCTA={displayHobbyCTA}
    />
  );
  const proPricingCard = (
    <PricingCard
      currentPlan={currentPlan}
      selectedPlan={selectedPlan}
      tierName="pro"
      tier={pricingData.tiers.pro}
      pricingData={pricingData}
      proPlanTagline={proPlanTagline}
    />
  );
  const enterprisePricingCard = (
    <PricingCard
      currentPlan={currentPlan}
      selectedPlan={selectedPlan}
      tierName="enterprise"
      tier={pricingData.tiers.enterprise}
      pricingData={pricingData}
    />
  );

  return (
    <div className="flex items-start gap-x-4 ">
      {(currentPlan === "hobby" || currentPlan === null) && hobbyPricingCard}
      {proPricingCard}
      {enterprisePricingCard}
    </div>
  );
}
