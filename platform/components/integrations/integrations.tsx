"use client";

import ArgillaIntegrations from "./argilla/argilla";
import PowerBIIntegrations from "./powerbi/powerbi";

const Integrations: React.FC = () => {
  return (
    <div>
      <h2 className="text-2xl font-bold tracking-tight mb-4">
        <div className="flex items-center">
          <div className="flex flex-row items-center">Integrations</div>
        </div>
      </h2>
      <div className="text-sm text-muted-foreground">
        Connect your data to external tools.
      </div>
      <div className="mt-4">
        <ArgillaIntegrations />
        <PowerBIIntegrations />
      </div>
    </div>
  );
};

export default Integrations;
