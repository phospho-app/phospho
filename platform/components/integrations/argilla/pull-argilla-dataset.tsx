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

    if (!project_id) {
        return <></>;
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
                        className="mt-1 block w-full"
                    />
                </div>
                <div className="flex justify-end mt-4">
                    <Button>
                        Pull dataset
                    </Button>
                </div>
            </SheetContent>
        </Sheet>
    );
};

export default PullDataset;
