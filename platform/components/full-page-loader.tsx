import React from "react";

interface FullPageLoaderProps {
  // Add any props you need for the component
}

const FullPageLoader: React.FC<FullPageLoaderProps> = (
  {
    /* destructure props here */
  },
) => {
  return (
    <div className="fixed top-0 left-0 z-50 w-full h-full flex items-center justify-center bg-slate-950">
      <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-green-500"></div>
    </div>
  );
};

export default FullPageLoader;
