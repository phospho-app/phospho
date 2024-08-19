import GenericDataviz from "@/components/dataviz/generic-dataviz";
import DatavizCard from "@/components/dataviz/dataviz-card";
import { time } from "console";

const TasksDataviz = () => {
    const analyticsQuery = {
        project_id: "8a357970ef4e460b88319d8d1a6c2f1c",
        collection: "tasks",
        aggregation_operation: "count",
        dimensions: ["day"],
        filters: {
            created_at_start: Math.floor(Date.now() / 1000) - 60 * 60 * 24 * 70,
        },
    };

    return (
        <GenericDataviz
            analyticsQuery={analyticsQuery}
            asFilledTimeSeries={true}
            xField="day"
            yFields={["value"]}
            chartType="stackedBar"
        />
    );
};

const ForPieDataviz = () => {
    const analyticsQuery = {
        project_id: "8a357970ef4e460b88319d8d1a6c2f1c",
        collection: "events",
        aggregation_operation: "count",
        dimensions: ["event_name"],
        filters: {
            created_at_start: Math.floor(Date.now() / 1000) - 60 * 60 * 24 * 70,
        }

    };

    return (
        <GenericDataviz
            analyticsQuery={analyticsQuery}
            xField="event_name"
            yFields={["value"]}
            chartType="pie"
        />
    );
};

const analyticsQuery = {
    project_id: "8a357970ef4e460b88319d8d1a6c2f1c",
    collection: "tasks",
    aggregation_operation: "count",
    dimensions: [],
    time_step: "hour",
    filters: {
        created_at_start: Math.floor(Date.now() / 1000) - 60 * 60 * 24 * 70,
    },
};

const analyticsQueryPie = {
    project_id: "8a357970ef4e460b88319d8d1a6c2f1c",
    collection: "events",
    aggregation_operation: "count",
    dimensions: ["event_name"],
    filters: {
        created_at_start: Math.floor(Date.now() / 1000) - 60 * 60 * 24 * 70,
    }

};

export default function DebugPage() {
    return (
        <div>
            <h1>Debug Page</h1>
            <DatavizCard analyticsQuery={analyticsQuery} xField="hour" yFields={["value"]} chartType="stackedBar" title="Tasks" />
            <DatavizCard analyticsQuery={analyticsQueryPie} xField="event_name" yFields={["value"]} chartType="pie" title="Pie Chart of events" />
        </div>
    );
}