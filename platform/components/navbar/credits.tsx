import { navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import React, { useEffect, useState } from "react";

const Credits: React.FC = ({}) => {
  const org_id = navigationStateStore((state) => state.selectedOrgId);
  const { accessToken } = useUser();
  const [credits, setCredits] = useState<number>(0);

  const fetchCredits = async () => {
    try {
      const response = await fetch(`/api//organizations/${org_id}/credits`, {
        method: "GET",
        headers: {
          Authorization: "Bearer " + accessToken,
          "Content-Type": "application/json",
        },
      });
      const data = await response.json();
      setCredits(data.credits / 1000); // A credit is $0.001
    } catch (error) {
      console.error("Error in making the credits request:", error);
    }
  };

  useEffect(() => {
    fetchCredits();
  }, [org_id, accessToken]);

  return (
    <div className="w-fit">
      {credits !== null && <p>Credits: ${credits.toFixed(3)}</p>}
    </div>
  );
};

export default Credits;
