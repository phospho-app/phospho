import { DatePickerWithRange } from "@/components/date-range";
import FilterComponent from "@/components/filters";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
    Sheet,
    SheetContent,
    SheetDescription,
    SheetTitle,
    SheetTrigger,
} from "@/components/ui/sheet";
import { toast } from "@/components/ui/use-toast";
import { dataStateStore } from "@/store/store";
import { navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import { Separator } from "@radix-ui/react-dropdown-menu";
import { ChevronRight, Download } from "lucide-react";
import React from "react";
import { useState } from "react";

const PullDataset = () => {
    const { accessToken } = useUser();
    const project_id = navigationStateStore((state) => state.project_id);
    const [isPullingDataset, setIsPullingDataset] = useState(false);
    const orgMetadata = dataStateStore((state) => state.selectedOrgMetadata);
    const dataFilters = navigationStateStore((state) => state.dataFilters);

    if (!project_id) {
        return <></>;
    }

    const [datasetName, setDatasetName] = useState("");

    async function pullArgillaDataset() {
        // Disable the button while we are creating the dataset
        setIsPullingDataset(true);
        try {
            await fetch(`/api/argila/pull`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: "Bearer " + accessToken,
                },
                body: JSON.stringify({
                    project_id: project_id,
                    workspace_id: orgMetadata?.argilla_workspace_id,
                    dataset_name: datasetName,
                    filters: dataFilters,
                }),
            }).then((response) => {
                if (response.status == 200) {
                    toast({
                        title: "Dataset pulled",
                        description: "Annotated dataset is now available in your project",
                    });
                } else if (response.status == 400) {
                    response.json().then((data) => {
                        toast({
                            title: "Could not pull dataset",
                            description: data.detail,
                        });
                    });
                } else {
                    toast({
                        title: "Could not pull dataset",
                        description: response.text(),
                    });
                }
                setIsPullingDataset(false);
            });
        } catch (e) {
            toast({
                title: "Error when pulling dataset",
                description: JSON.stringify(e),
            });
            setIsPullingDataset(false);
        }
    }

    return (
        <Sheet>
            <SheetTrigger>
                <Button className="default">
                    Pull dataset
                    <Download className="w-4 h-4 ml-2" />
                </Button>
            </SheetTrigger>
            <SheetContent className="md:w-1/2 overflow-auto">
                <SheetTitle>Import data</SheetTitle>
                <SheetDescription>
                    Import a labelled dataset from Argilla
                </SheetDescription>
                {/* <div className="items-top flex space-x-2 mt-4">
                    <Checkbox
                        id="terms1"
                        checked={useSmartSampling}
                        onCheckedChange={handleSmartSamplingChange}
                    />
                    <div className="grid gap-1.5 leading-none">
                        <label
                            htmlFor="terms1"
                            className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                        >
                            Force balanced dataset
                        </label>
                    </div>
                </div> */}
                <div className="mt-4">
                    <div className="block text-sm font-medium">
                        Dataset to import
                    </div>
                    <Input
                        type="string"
                        name="dataset_name"
                        id="dataset_name"
                        value={datasetName}
                        onChange={(e) => setDatasetName(e.target.value)}
                        className="mt-1 block w-full"
                    />
                </div>
                <div className="flex justify-end mt-4">
                    <Button
                        type="submit"
                        onClick={pullArgillaDataset}
                        disabled={isPullingDataset}
                    >
                        Pull dataset
                    </Button>
                </div>
            </SheetContent>
        </Sheet>
    );
};

export default PullDataset;
