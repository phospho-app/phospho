"use client"

import {
    AnalyticsQuery,
} from "@/models/models";
import React from 'react';

import {
    Card,
    CardTitle,
    CardContent,
    CardHeader,
} from "@/components/ui/card";

import GenericDataviz from "./generic-dataviz";

type DatavizParams = {
    analyticsQuery: AnalyticsQuery;
    xField: string; // Field to be used on the x-axis
    yFields: string[]; // Fields to be used on the y-axis
    chartType: string; // line, bar, pie, etc.
    title: string;
    // showTotal: boolean; // Show total value in the chart
};


const DatavizCard: React.FC<DatavizParams> = ({ analyticsQuery, xField, yFields, chartType, title }) => {

    return (
        <>
            <Card className='max-w-[500px] mx-auto'>
                <CardHeader>
                    <CardTitle>{title}</CardTitle>
                </CardHeader>
                <CardContent>
                    <GenericDataviz analyticsQuery={analyticsQuery} xField={xField} yFields={yFields} chartType={chartType} />
                </CardContent>
            </Card>
        </>
    );
}

export default DatavizCard;