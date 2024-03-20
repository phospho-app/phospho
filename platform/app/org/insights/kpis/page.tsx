"use client";

import ComingSoon from "@/components/coming-soon";
import TopRowKpis from "@/components/insights/top-row";
// State store
import { navigationStateStore } from "@/store/store";
// PropelAuth
import { useUser } from "@propelauth/nextjs/client";
import React, { useEffect, useState } from "react";

const KPIs: React.FC<{}> = ({}) => {
  // PropelAuth
  const { accessToken } = useUser();
  // Store variables
  const project_id = navigationStateStore((state) => state.project_id);

  // Number of users
  const [userCountIsLoading, setUserCountIsLoading] = useState<boolean>(true);
  const [userCount, setUserCount] = useState<number>(0);
  // Async call to fetch the metadata
  useEffect(() => {
    // Fetch aggregated metrics from the API
    (async () => {
      const response = await fetch(
        `/api/explore/${project_id}/nb_items_with_a_metadata_field/tasks/user_id`,
        {
          method: "GET",
          headers: {
            Authorization: "Bearer " + accessToken,
            "Content-Type": "application/json",
          },
        },
      );
      const response_json = await response.json();
      console.log("user count", response_json);
      setUserCount(response_json.value);
      setUserCountIsLoading(false);
    })();
  }, [project_id]);

  // KPIs on number of messages
  const [kpiMessagesIsLoading, setKpiMessagesIsLoading] =
    useState<boolean>(true);
  const [kpiMessagesCount, setKpiMessagesCount] = useState<number>(0);
  const [kpiMessagesAverage, setKpiMessagesAverage] = useState<number>(0);
  const [kpiMessagesTop10, setKpiMessagesTop10] = useState<number>(0);
  const [kpiMessagesBottom10, setKpiMessagesBottom10] = useState<number>(0);
  // Async call to fetch the metadata
  useEffect(() => {
    // Fetch aggregated metrics from the API
    (async () => {
      const authorization_header = "Bearer " + accessToken;

      const headers = {
        Authorization: authorization_header, // Use an empty string if authorization_header is null
        "Content-Type": "application/json",
      };
      const response = await fetch(
        `/api/explore/${project_id}/nb_items_with_a_metadata_field/tasks/user_id`,
        {
          method: "GET",
          headers: headers,
        },
      );
      const response_json = await response.json();
      console.log("user count", response_json);
      setKpiMessagesCount(response_json.value);
      setKpiMessagesIsLoading(false);
    })();
  }, [project_id]);

  useEffect(() => {
    // Fetch aggregated metrics from the API
    (async () => {
      const authorization_header = "Bearer " + accessToken;

      const headers = {
        Authorization: authorization_header, // Use an empty string if authorization_header is null
        "Content-Type": "application/json",
      };
      const response = await fetch(
        `/api/explore/${project_id}/compute_nb_items_with_metadata_field/tasks/user_id`,
        {
          method: "GET",
          headers: headers,
        },
      );
      const response_json = await response.json();
      setKpiMessagesBottom10(response_json.bottom_quantile);
      setKpiMessagesAverage(response_json.average);
      setKpiMessagesTop10(response_json.top_quantile);
      console.log("quantile value is ", response_json.quantile_value);
      setKpiMessagesIsLoading(false);
    })();
  }, [project_id]);

  // Do the same for sessions instead of tasks

  // KPIs on number of messages
  const [kpiSessionsIsLoading, setKpiSessionsIsLoading] =
    useState<boolean>(true);
  const [kpiSessionsCount, setKpiSessionsCount] = useState<number>(0);
  const [kpiSessionsAverage, setKpiSessionsAverage] = useState<number>(0);
  const [kpiSessionsTop10, setKpiSessionsTop10] = useState<number>(0);
  const [kpiSessionsBottom10, setKpiSessionsBottom10] = useState<number>(0);
  // Async call to fetch the metadata
  useEffect(() => {
    // Fetch aggregated metrics from the API
    (async () => {
      const authorization_header = "Bearer " + accessToken;

      const headers = {
        Authorization: authorization_header, // Use an empty string if authorization_header is null
        "Content-Type": "application/json",
      };
      const response = await fetch(
        `/api/explore/${project_id}/nb_items_with_a_metadata_field/sessions/user_id`,
        {
          method: "GET",
          headers: headers,
        },
      );
      const response_json = await response.json();
      console.log("user count", response_json);
      setKpiSessionsCount(response_json.value);
      setKpiSessionsIsLoading(false);
    })();
  }, [project_id]);

  useEffect(() => {
    // Fetch aggregated metrics from the API
    (async () => {
      const authorization_header = "Bearer " + accessToken;

      const headers = {
        Authorization: authorization_header, // Use an empty string if authorization_header is null
        "Content-Type": "application/json",
      };
      const response = await fetch(
        `/api/explore/${project_id}/compute_nb_items_with_metadata_field/sessions/user_id`,
        {
          method: "GET",
          headers: headers,
        },
      );
      const response_json = await response.json();
      setKpiSessionsBottom10(response_json.bottom_quantile);
      setKpiSessionsAverage(response_json.average);
      setKpiSessionsTop10(response_json.top_quantile);
      console.log("quantile value is ", response_json.quantile_value);
      setKpiSessionsIsLoading(false);
    })();
  }, [project_id]);

  // Do the same as for tasks and sessions fo rthe success rate
  const [kpiSuccessIsLoading, setKpiSuccessIsLoading] = useState<boolean>(true);
  const [kpiSuccessAverage, setKpiSuccessAverage] = useState<number>(0);
  const [kpiSuccessTop10, setKpiSuccessTop10] = useState<number>(0);
  const [kpiSuccessBottom10, setKpiSuccessBottom10] = useState<number>(0);

  useEffect(() => {
    // Fetch aggregated metrics from the API
    (async () => {
      const authorization_header = "Bearer " + accessToken;

      const headers = {
        Authorization: authorization_header, // Use an empty string if authorization_header is null
        "Content-Type": "application/json",
      };
      const response = await fetch(
        `/api/explore/${project_id}/successrate-stats/tasks/user_id`,
        {
          method: "GET",
          headers: headers,
        },
      );
      const response_json = await response.json();
      setKpiSuccessBottom10(response_json.bottom_quantile);
      setKpiSuccessAverage(response_json.average);
      setKpiSuccessTop10(response_json.top_quantile);
      setKpiSuccessIsLoading(false);
    })();
  }, [project_id]);

  return <ComingSoon />;

  return (
    <>
      <div>
        <span>
          Number of user : {userCountIsLoading ? "loading" : userCount}
        </span>
      </div>
      <div className="mt-2">
        <TopRowKpis
          name="Number of messages"
          count={kpiMessagesCount}
          bottom10={kpiMessagesBottom10}
          average={kpiMessagesAverage}
          top10={kpiMessagesTop10}
        />
      </div>
      <div className="mt-2">
        <TopRowKpis
          name="Number of sessions"
          count={kpiSessionsCount}
          bottom10={kpiSessionsBottom10}
          average={kpiSessionsAverage}
          top10={kpiSessionsTop10}
        />
      </div>
      <div className="mt-2">
        <TopRowKpis
          name="Success rate"
          count={0}
          average={kpiSuccessAverage}
          bottom10={kpiSuccessBottom10}
          top10={kpiSuccessTop10}
        />
      </div>
    </>
  );
};

export default KPIs;
