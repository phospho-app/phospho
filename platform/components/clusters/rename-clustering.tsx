"use client";

import {
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Clustering } from "@/models/models";
// zustand state management
import { zodResolver } from "@hookform/resolvers/zod";
import { X } from "lucide-react";
// PropelAuth
import { useForm } from "react-hook-form";
import * as z from "zod";

interface RenameClusteringDialogProps {
  open: boolean;
  setOpen: (open: boolean) => void;
  clusteringToEdit?: Clustering;
}

const RenameClusteringDialog: React.FC<RenameClusteringDialogProps> = ({
  open,
  setOpen,
  clusteringToEdit,
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

  const handleClose = () => {
    setOpen(false);
  };

  const onSubmit = async (data: z.infer<typeof FormSchema>) => {
    console.log("data", data);
  };

  return (
    <>
      <AlertDialogContent>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
            {/* 
            <AlertDialogHeader>
              <X onClick={handleClose} className="cursor-pointer h-8 w-8" />
              <AlertDialogTitle>Vouvcou</AlertDialogTitle>
            </AlertDialogHeader> */}
            {clusteringToEdit && (
              <>
                <FormField
                  control={form.control}
                  name="clustering_name"
                  render={({ field }) => (
                    <FormItem>
                      <div>Clustering Name</div>
                      <FormControl>
                        <Input
                          placeholder="Enter a clustering name"
                          maxLength={32}
                          {...field}
                          autoFocus
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <Button type="submit">Rename</Button>
              </>
            )}
          </form>
        </Form>
      </AlertDialogContent>
    </>
  );
};

export default RenameClusteringDialog;
