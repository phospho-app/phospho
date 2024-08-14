import GenericDataviz from "@/components/dataviz/generic-dataviz";

const TasksDataviz = () => {
    const analyticsQuery = {
        project_id: "ec3d59abb7284520abb90f546c7344e4",
        collection: "tasks",
        aggregation_operation: "count",
        dimensions: ["day", "metadata.user_id"],
        filters: {
            created_at_start: Math.floor(Date.now() / 1000) - 60 * 60 * 24 * 7,
        },
    };

    return (
        <GenericDataviz
            analyticsQuery={analyticsQuery}
            xField="day"
            yFields={["value"]}
            chartType="bar"
            title="Messages"
            subtitle="Last 7 days"
        />
    );
};

export default function DebugPage() {
    return (
        <div>
            <h1>Debug Page</h1>
            <TasksDataviz />
        </div>
    );
}