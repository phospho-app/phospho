"use client"

import {
    AnalyticsQuery,
} from "@/models/models";
import React from 'react';

import {
    Card,
    CardTitle,
    CardContent,
    CardDescription,
    CardHeader,
    CardFooter,
} from "@/components/ui/card";

import GenericDataviz from "./generic-dataviz";

type DatavizParams = {
    analyticsQuery: AnalyticsQuery;
    xField: string; // Field to be used on the x-axis
    yFields: string[]; // Fields to be used on the y-axis
    chartType: string; // line, bar, pie, etc.
    title: string;
    subtitle: string;
    asFilledTimeSerie?: boolean; // If true, the chart will be displayed as a filled time serie
    // showTotal: boolean; // Show total value in the chart
};


const DatavizCard: React.FC<DatavizParams> = ({ analyticsQuery, xField, yFields, chartType, title, subtitle }) => {

    return (
        <>
            <Card className='max-w-[500px] mx-auto'>
                <CardHeader>
                    <CardTitle>{title}</CardTitle>
                    <CardDescription>{subtitle}</CardDescription>
                </CardHeader>
                <CardContent>
                    <GenericDataviz analyticsQuery={analyticsQuery} xField={xField} yFields={yFields} chartType={chartType} />
                </CardContent>
            </Card>
        </>
    );
}

export default DatavizCard;