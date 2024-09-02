"use client";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
} from "@/components/ui/card";
import React from "react";

const TopRowKpis = ({
  name,
  count,
  bottom10,
  average,
  top10,
}: {
  name: string;
  count: number;
  bottom10: number;
  average: number;
  top10: number;
}) => {
  // TODO : Add a histogram for the distribution of the tasks instead of the bottom and top 10%
  return (
    <div>
      <div className="container mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardHeader>
              <CardDescription>Total Nb of {name}</CardDescription>
            </CardHeader>
            <CardContent>
              {((count === null || count === undefined) && <p>...</p>) || (
                <p className="text-xl">{count}</p>
              )}
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardDescription>
                Nb user messages Bottom 10% {name}
              </CardDescription>
            </CardHeader>
            <CardContent>
              {((bottom10 === null || bottom10 === undefined) && (
                <p>...</p>
              )) || <p className="text-xl">{bottom10}</p>}
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardDescription>Avg Nb user messages per {name}</CardDescription>
            </CardHeader>
            <CardContent>
              {((average === null || average === undefined) && <p>...</p>) || (
                <p className="text-xl">{average.toString()}</p>
              )}
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardDescription>Nb user messages Top 10% {name}</CardDescription>
            </CardHeader>
            <CardContent>
              {((top10 === null || top10 === undefined) && <p>...</p>) || (
                <p className="text-xl">{top10}</p>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default TopRowKpis;
