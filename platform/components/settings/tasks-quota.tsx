import * as Progress from "@radix-ui/react-progress";
import React from "react";
import { useEffect } from "react";

// TODO : Refacto this to use shadcn instead

interface ProgressProps {
  currentValue: number | undefined;
  maxValue: number | undefined;
}

const TaskProgress = ({ currentValue, maxValue }: ProgressProps) => {
  const [progress, setProgress] = React.useState(0);

  useEffect(() => {
    if (currentValue === undefined || maxValue === undefined) {
      return;
    }
    const timer = setTimeout(() => setProgress(currentValue), 500);
    return () => clearTimeout(timer);
  }, [currentValue, maxValue]);

  if (currentValue === undefined || maxValue === undefined) {
    return <></>;
  }

  const translation = currentValue ? currentValue / maxValue : 0;

  return (
    <Progress.Root
      className="relative overflow-hidden bg-gray-300 rounded-full w-[300px] h-[25px]"
      style={{
        // Fix overflow clipping in Safari
        // https://gist.github.com/domske/b66047671c780a238b51c51ffde8d3a0
        transform: "translateZ(0)",
      }}
      value={progress}
    >
      <Progress.Indicator
        className="bg-green-500 w-full h-full transition-transform duration-&lsqb;660ms&rsqb; ease-[cubic-bezier(0.65, 0, 0.35, 1)]"
        style={{
          transform: `translateX(-${Math.round(100 - translation * 100)}%)`,
        }}
      />
    </Progress.Root>
  );
};

export default TaskProgress;
