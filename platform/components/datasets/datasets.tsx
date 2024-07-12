"use client";

import { useUser } from "@propelauth/nextjs/client";
import { dataStateStore, navigationStateStore } from "@/store/store";
import { useEffect, useState } from "react";
import { Card, CardDescription, CardHeader, CardTitle } from "../ui/card";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import CreateDataset from "@/components/datasets/create-dataset";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { CircleAlert } from "lucide-react";

const Datasets: React.FC = () => {

    const project_id = navigationStateStore((state) => state.project_id);
    const selectedOrgId = navigationStateStore((state) => state.selectedOrgId);
    const selectedOrgMetadata = dataStateStore(
        (state) => state.selectedOrgMetadata,
    );

    // If the selectedOrgMetadata.argilla_worspace_id exists and is not null, then Argilla is set up
    const [isArgillaSetup, setIsArgillaSetup] = useState<boolean>(false);

    useEffect(() => {
        if (selectedOrgMetadata?.argilla_workspace_id) {
            setIsArgillaSetup(true);
        }
    }, [selectedOrgMetadata?.argilla_workspace_id]);

    const { user } = useUser();

    return (
        <>
            {isArgillaSetup ? (
                <div>
                    <div>
                        <h2 className="text-2xl font-bold tracking-tight mb-4">
                            <div className="flex items-center">
                                <div className="flex flex-row items-center">
                                    {/* <BriefcaseBusiness className="w-6 h-6 mr-2" /> */}
                                    Datasets
                                </div>
                            </div>
                        </h2>
                        <div className="text-sm text-muted-foreground">
                            You can view and label your exported datasets in your Argilla platform. Learn more here.
                        </div>
                        <div className="mt-4">
                            <Link
                                href={process.env.NEXT_PUBLIC_ARGILLA_URL || "https://argilla.phospho.ai"}
                                target="_blank"
                            >
                                <Button>View your datasets</Button>
                            </Link>
                        </div>
                        <h2 className="text-xl font-bold tracking-tight mt-6">Export data</h2>
                        <div className="text-sm text-muted-foreground">
                            Export datasets from your project for labelling in your Argilla platform.
                        </div>
                        <div className="mt-4">
                            < CreateDataset />
                        </div>
                    </div>
                </div>
            ) : (<div>
                <Card className="bg-secondary">
                    <CardHeader>
                        <div className="flex justify-between items-center">
                            <div>
                                <CardTitle className="flex flex-row text-2xl font-bold tracking-tight items-center">
                                    Export datasets from your project for labelling
                                </CardTitle>
                                <CardDescription>
                                    <div className="text-muted-foreground">
                                        Enable your team to manually label messages to evaluate the quality of phospho's predictions and improve them if needed.
                                    </div>
                                </CardDescription>
                            </div>
                            <Button disabled={true}>Export dataset</Button>

                        </div>
                    </CardHeader>
                </Card>
                <div className="mt-4">
                    <Alert>
                        <CircleAlert className="h-4 w-4" />
                        <AlertTitle>This feature is not enabled for your organization</AlertTitle>
                        <AlertDescription>
                            Contact us at <Link href="mailto:contact@phospho.ai" className="underline">contact@phospho.ai</Link> to get access.
                        </AlertDescription>
                    </Alert>
                </div>

            </div>
            )}
        </>
    );
};

export default Datasets;
