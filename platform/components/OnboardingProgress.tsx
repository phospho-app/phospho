import React from "react";

interface Step {
  label: string;
  isActive: boolean;
  isCompleted: boolean;
}

interface OnboardingProgressProps {
  steps: Step[];
}

const OnboardingProgress: React.FC<OnboardingProgressProps> = ({ steps }) => {
  return (
    <div className="p-4 md:p-6 md:fixed md:left-0 md:top-12 md:h-full md:w-56 md:overflow-y-auto">
      <h2 className="text-xl font-semibold mb-4 md:mb-6">
        Onboarding progress
      </h2>
      <ol className="relative border-l text-muted-foreground space-y-6 md:space-y-8 ml-6">
        {steps.map((step, index) => (
          <li key={index} className="ml-6 flex items-center">
            <span
              className={`absolute flex items-center justify-center w-8 h-8 rounded-full -left-4 ring-2 ring-secondary-foreground
                ${step.isCompleted || step.isActive ? "bg-green-500" : "bg-secondary"}`}
            >
              {step.isCompleted ? (
                <svg
                  className="w-5 h-5 text-secondary-foreground"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                    clipRule="evenodd"
                  />
                </svg>
              ) : (
                <span className="text-white">{index + 1}</span>
              )}
            </span>
            <h3
              className={`pl-1 ${step.isActive ? "font-semibold text-green-500" : "text-muted-foreground"}`}
            >
              {step.label}
            </h3>
          </li>
        ))}
      </ol>
    </div>
  );
};

export default OnboardingProgress;
