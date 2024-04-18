import CreateProjectButton from "./create-project-button";
import { SelectProjectButton } from "./select-project-dropdown";

export function NavBarProject() {
  return (
    <>
      <SelectProjectButton />

      <CreateProjectButton />
    </>
  );
}
