import { DatePickerWithRange } from "@/components/date-range";
import FilterComponent from "@/components/filters"; ``
import { authFetcher } from "@/lib/fetcher";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
    Sheet,
    SheetContent,
    SheetDescription,
    SheetTitle,
    SheetTrigger,
} from "@/components/ui/sheet";
import {
    Select,
    SelectContent,
    SelectGroup,
    SelectItem,
    SelectLabel,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { toast } from "@/components/ui/use-toast";
import { dataStateStore } from "@/store/store";
import { navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import { Separator } from "@radix-ui/react-dropdown-menu";
import { BriefcaseBusiness, ChevronRight, Database, Download } from "lucide-react";
import React from "react";
import { useState } from "react";
import useSWR from "swr";
import { list } from "postcss";

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
            await fetch(`/api/argilla/pull`, {
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

    const { data: datasets_names }: { data: string[] | undefined } = useSWR(
        project_id ? [`/api/argilla/names`, accessToken] : null,
        ([url, accessToken]) => authFetcher(url, accessToken, "POST", {
            project_id: project_id,
            workspace_id: orgMetadata?.argilla_workspace_id,
            filters: dataFilters,
        }),
        {
            keepPreviousData: true,
        }
    );


    const handleValueChange = (dataset_name: string) => {
        console.log("Selected Dataset Name in selectbutton:", dataset_name);
        // Match the selected project name with the project in the projects array
        setDatasetName(dataset_name);
    };

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
                    <Select
                        onValueChange={handleValueChange}
                        defaultValue={datasetName}
                    >
                        <SelectTrigger className="py-1 h-8">
                            <span className="flex space-x-1">
                                <div className="flex items-center">{datasetName || "Select a dataset"}</div>
                                <SelectValue asChild={true} id={project_id}>
                                    <div>{datasetName}</div>
                                </SelectValue>
                            </span>
                        </SelectTrigger>
                        <SelectContent position="popper" className="overflow-y-auto max-h-[40rem]">
                            <SelectGroup>
                                <SelectLabel>
                                    <div className="flex flex-row items-center">
                                        <Database className="w-4 h-4 mr-1" />
                                        Datasets ({datasets_names?.length})
                                    </div>
                                </SelectLabel>
                                {datasets_names?.map((name) => (
                                    <SelectItem
                                        key={name} // Added key for each item
                                        value={name}
                                        onClick={(mouseEvent) => {
                                            mouseEvent.stopPropagation();
                                        }}
                                    >
                                        {name}
                                    </SelectItem>
                                ))}
                            </SelectGroup>
                        </SelectContent>
                    </Select>
                </div>
                {/* <Input
                        type="string"
                        name="dataset_name"
                        id="dataset_name"
                        value={datasetName}
                        onChange={(e) => setDatasetName(e.target.value)}
                        className="mt-1 block w-full"
                    /> */}

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
