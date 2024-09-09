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
import { generateSlug } from "@/lib/utils";
import { dataStateStore } from "@/store/store";
import { navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import { Separator } from "@radix-ui/react-dropdown-menu";
import { ChevronRight } from "lucide-react";
import React from "react";
import { useState } from "react";

const CreateDataset = () => {
  const { accessToken } = useUser();
  const project_id = navigationStateStore((state) => state.project_id);
  const orgMetadata = dataStateStore((state) => state.selectedOrgMetadata);
  const dataFilters = navigationStateStore((state) => state.dataFilters);
  const [isCreatingDataset, setIsCreatingDataset] = useState(false);
  // Params for the dataset creation
  const [limit, setLimit] = useState(400); // Limit on the dataset size
  const [useSmartSampling, setUseSmartSampling] = useState(false); // To know wich sampling_type send to the backend
  const [datasetName, setDatasetName] = useState(generateSlug());

  // Hardcoded limit for the dataset size
  const MAX_LIMIT = 2000;

  if (!project_id) {
    return <></>;
  }

  async function createNewDataset() {
    // Disable the button while we are creating the dataset
    setIsCreatingDataset(true);
    try {
      await fetch(`/api/argilla/datasets/create`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: "Bearer " + accessToken,
        },
        body: JSON.stringify({
          project_id: project_id,
          limit: limit,
          workspace_id: orgMetadata?.argilla_workspace_id,
          dataset_name: datasetName,
          filters: dataFilters,
          sampling_parameters: {
            sampling_type: useSmartSampling ? "balanced" : "naive",
          },
        }),
      }).then((response) => {
        if (response.status == 200) {
          toast({
            title: "Dataset created",
            description: "View it in your Argilla platform",
          });
        } else if (response.status == 400) {
          response.json().then((data) => {
            toast({
              title: "Could not create dataset",
              description: data.detail,
            });
          });
        } else {
          toast({
            title: "Could not create dataset",
            description: response.text(),
          });
        }
        setIsCreatingDataset(false);
      });
    } catch (e) {
      toast({
        title: "Error when creating dataset",
        description: JSON.stringify(e),
      });
      setIsCreatingDataset(false);
    }
  }

  const handleSmartSamplingChange = (checked: boolean) => {
    setUseSmartSampling(checked === true);
  };

  return (
    <Sheet>
      <SheetTrigger>
        <Button className="default">
          Create dataset
          <ChevronRight className="w-4 h-4 ml-2" />
        </Button>
      </SheetTrigger>
      <SheetContent className="md:w-1/2 overflow-auto">
        <SheetTitle>Export data</SheetTitle>
        <SheetDescription>
          Export your project data into a dataset for labelling
        </SheetDescription>
        <Separator className="my-8" />
        <div className="flex flex-wrap mt-4 space-x-2">
          <DatePickerWithRange />
          <FilterComponent variant="tasks" />
        </div>
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
            Dataset size (max {MAX_LIMIT} rows)
          </div>
          <Input
            type="number"
            name="limit"
            id="limit"
            value={limit}
            onChange={(e) =>
              setLimit(Math.min(Number(e.target.value), MAX_LIMIT))
            }
            className="mt-1 block w-full"
            placeholder="100"
            min={1}
            max={MAX_LIMIT}
          />
        </div>
        <div className="mt-4">
          <div className="block text-sm font-medium">Dataset Name</div>
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
            disabled={isCreatingDataset}
          >
            Create dataset
          </Button>
        </div>
      </SheetContent>
    </Sheet>
  );
};

export default CreateDataset;
