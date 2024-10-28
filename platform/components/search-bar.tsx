import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { navigationStateStore } from "@/store/store";
import { X } from "lucide-react";
import { useEffect, useState } from "react";

interface SearchBarProps {
  variant: "messages" | "sessions";
}

const SearchBar = ({ variant }: SearchBarProps) => {
  const [searchTerm, setSearchTerm] = useState("");
  const setDataFilters = navigationStateStore((state) => state.setDataFilters);
  const dataFilters = navigationStateStore((state) => state.dataFilters);
  const setTasksPagination = navigationStateStore(
    (state) => state.setTasksPagination,
  );

  // Update filters when search term changes
  useEffect(() => {
    const filterKey =
      variant === "messages" ? "task_id_search" : "session_id_search";

    const debounceTimeout = setTimeout(() => {
      const newFilters = { ...dataFilters };

      if (searchTerm.trim() !== "") {
        newFilters[filterKey] = searchTerm;
      } else {
        delete newFilters[filterKey];
      }

      setDataFilters(newFilters);

      setTasksPagination((prev) => ({
        ...prev,
        pageIndex: 0,
      }));
    }, 300);

    return () => clearTimeout(debounceTimeout);
  }, [searchTerm, variant, dataFilters, setDataFilters, setTasksPagination]);

  // Initialize search term from filters only once when component mounts
  useEffect(() => {
    const filterKey =
      variant === "messages" ? "task_id_search" : "session_id_search";
    const currentFilter = dataFilters?.[filterKey];

    if (currentFilter && searchTerm === "") {
      setSearchTerm(currentFilter);
    }
    //  we don't want to run this effect on every render so no search term in the dependency array
  }, [variant, dataFilters]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(e.target.value);
  };

  const clearSearch = () => {
    setSearchTerm("");
    const filterKey =
      variant === "messages" ? "task_id_search" : "session_id_search";
    const newFilters = { ...dataFilters };
    delete newFilters[filterKey];
    setDataFilters(newFilters);
  };

  return (
    <div className="relative w-full max-w-sm mb-4">
      <Input
        type="text"
        placeholder={
          variant === "messages"
            ? "Search for a message ID..."
            : "Search for a session ID..."
        }
        value={searchTerm}
        onChange={handleInputChange}
        className="pr-10"
      />
      {searchTerm && (
        <Button
          variant="ghost"
          size="sm"
          className="absolute right-2 top-1/2 -translate-y-1/2 h-6 w-6 p-0"
          onClick={clearSearch}
        >
          <X className="h-4 w-4" />
        </Button>
      )}
    </div>
  );
};

export { SearchBar };
