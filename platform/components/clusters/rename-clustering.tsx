"use client";

import {
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Form } from "@/components/ui/form";
import { Clustering } from "@/models/models";
// zustand state management
import { zodResolver } from "@hookform/resolvers/zod";
// PropelAuth
import { useForm } from "react-hook-form";
import * as z from "zod";

const RenameClusteringDialog = ({
  setOpen,
  clusteringToEdit,
}: {
  setOpen: (open: boolean) => void;
  clusteringToEdit?: Clustering;
}) => {
  const FormSchema = z.object({
    clustering_name: z
      .string({
        required_error: "Please enter a clustering name",
      })
      .min(3, "Project name must be at least 3 characters long")
      .max(32, "Project name must be at most 32 characters long"),
  });

  const form = useForm<z.infer<typeof FormSchema>>({
    resolver: zodResolver(FormSchema),
    defaultValues: {
      clustering_name: clusteringToEdit?.name || "",
    },
  });

  return (
    <AlertDialogHeader>
      <AlertDialogTitle>Vouvcou</AlertDialogTitle>
    </AlertDialogHeader>
  );
};

export default RenameClusteringDialog;
