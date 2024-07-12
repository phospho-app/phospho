import CreateProjectButton from "./CreateProjectButton";
import { SelectProjectButton } from "./SelectProjectDropdown";

export function NavBarProject() {
  return (
    <>
      <SelectProjectButton />
      <CreateProjectButton />
    </>
  );
}
