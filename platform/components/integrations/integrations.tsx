"use client";

import ArgillaIntegrations from "../argilla/argilla";
import PowerBIIntegrations from "../powerBI/powerbi";

const Integrations: React.FC = () => {
  return (
    <div>
      <h2 className="text-2xl font-bold tracking-tight mb-4">
        <div className="flex items-center">
          <div className="flex flex-row items-center">
            {/* <BriefcaseBusiness className="w-6 h-6 mr-2" /> */}
            Integrations
          </div>
        </div>
      </h2>
      <div className="text-sm text-muted-foreground">
        Easily export your data to your favorite tools.
      </div>
      <div className="mt-4">
        <ArgillaIntegrations />
        <PowerBIIntegrations />
      </div>
    </div>
  );
};

export default Integrations;
