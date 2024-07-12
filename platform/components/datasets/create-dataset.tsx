import { DatePickerWithRange } from "@/components/date-range";
import FilterComponent from "@/components/filters";
import { Spinner } from "@/components/small-spinner";
import { Button } from "@/components/ui/button";
import {
    Sheet,
    SheetContent,
    SheetDescription,
    SheetTitle,
    SheetTrigger,
} from "@/components/ui/sheet";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { toast } from "@/components/ui/use-toast";
import UpgradeButton from "@/components/upgrade-button";
import { authFetcher } from "@/lib/fetcher";
import { Clustering, Project } from "@/models/models";
import { dataStateStore } from "@/store/store";
import { navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import { Separator } from "@radix-ui/react-dropdown-menu";
import { ChevronRight, Sparkles } from "lucide-react";
import React from "react";
import { useEffect, useState } from "react";
import useSWR from "swr";
import { Input } from "@/components/ui/input";
import { CircleAlert } from "lucide-react";

const CreateDataset = () => {
    const { accessToken } = useUser();
    const project_id = navigationStateStore((state) => state.project_id);
    const orgMetadata = dataStateStore((state) => state.selectedOrgMetadata);
    const dataFilters = navigationStateStore((state) => state.dataFilters);
    const [datasetName, setDatasetName] = useState("");

    const hobby = orgMetadata?.plan === "hobby";

    if (!project_id) {
        return <></>;
    }

    async function createNewDataset() {
        try {
            await fetch(`/api/datasets`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: "Bearer " + accessToken,
                },
                body: JSON.stringify({
                    project_id: project_id,
                    limit: 100000, // TODO: remove this limit
                    workspace_id: orgMetadata?.argilla_workspace_id,
                    dataset_name: datasetName,
                    filters: dataFilters,

                }),
            }).then((response) => {
                if (response.status == 200) {
                    toast({
                        title: "Dataset created",
                        description: "View it in your Argilla platform",
                    });
                } else {
                    toast({
                        title: "Could not create dataset",
                        description: response.text(),
                    });
                }
            });
        } catch (e) {
            toast({
                title: "Error when creating dataset",
                description: JSON.stringify(e),
            });
        }
    }

    return (
        <Sheet>
            <SheetTrigger>
                <Button className="default">
                    Export new dataset
                    <ChevronRight className="w-4 h-4 ml-2" />
                </Button>
            </SheetTrigger>
            <SheetContent className="md:w-1/2 overflow-auto">
                <SheetTitle>Export data</SheetTitle>
                <SheetDescription>
                    Export datasets from your project for labelling in your Argilla platform.
                </SheetDescription>
                <Separator className="my-8" />
                <Alert>
                    <CircleAlert className="h-4 w-4" />
                    <AlertTitle>Heads up!</AlertTitle>
                    <AlertDescription>
                        Dataset names must be unique within your Argilla workspace.
                    </AlertDescription>
                </Alert>
                <div className="flex flex-wrap mt-4">
                    <DatePickerWithRange className="mr-2" />
                    <FilterComponent variant="tasks" />
                </div>
                <div className="mt-4">
                    <label htmlFor="datasetName" className="block text-sm font-medium text-gray-700">
                        Dataset Name
                    </label>
                    <Input
                        type="text"
                        name="datasetName"
                        id="datasetName"
                        value={datasetName}
                        onChange={(e) => setDatasetName(e.target.value)}
                        className="mt-1 block w-full"
                        placeholder="your-dataset-name"
                    />
                </div>
                <div className="flex justify-end mt-4">
                    <Button
                        type="submit"
                        onClick={createNewDataset}
                    >
                        Create dataset
                    </Button>
                </div>
            </SheetContent>
        </Sheet>
    );
};

export default CreateDataset;
