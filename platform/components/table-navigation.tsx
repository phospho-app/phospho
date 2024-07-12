import { Button } from "@/components/ui/button";
import { Table } from "@tanstack/react-table";
import {
  ChevronFirstIcon,
  ChevronLastIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
} from "lucide-react";

export function TableNavigation({ table }: { table: Table<any> }) {
  return (
    <div className="flex space-x-1 items-center align-middle">
      <Button
        variant="outline"
        className="w-8 p-0"
        size="icon"
        onClick={() => table.firstPage()}
        disabled={!table.getCanPreviousPage()}
      >
        <span className="sr-only">Go to first page</span>
        <ChevronFirstIcon className="h-4 w-4" />
      </Button>
      <Button
        variant="outline"
        className="w-8 p-0"
        size="icon"
        onClick={() => table.previousPage()}
        disabled={!table.getCanPreviousPage()}
      >
        <span className="sr-only">Go to previous page</span>
        <ChevronLeftIcon className="h-4 w-4" />
      </Button>
      <div className="">
        {table.getPageCount() !== -1
          ? `${table.getState().pagination.pageIndex + 1}/${table.getPageCount()}`
          : `${table.getState().pagination.pageIndex + 1}`}
      </div>
      <Button
        variant="outline"
        className="w-8 p-0"
        size="icon"
        onClick={() => table.nextPage()}
        disabled={!table.getCanNextPage()}
      >
        <span className="sr-only">Go to next page</span>
        <ChevronRightIcon className="h-4 w-4" />
      </Button>
      <Button
        variant="outline"
        className="w-8 p-0"
        size="icon"
        onClick={() => table.lastPage()}
        disabled={!table.getCanNextPage()}
      >
        <span className="sr-only">Go to last page</span>
        <ChevronLastIcon className="h-4 w-4" />
      </Button>
    </div>
  );
}
