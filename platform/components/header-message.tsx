import Link from "next/link";
import React from "react";

const AlphaNotificationBar: React.FC = () => {
  return (
    <div className="bg-green-500 p-1 text-center sticky top-14 z-10 text-gray-600">
      ⚠️ Our service is still in beta. Provide us feedbacks
      <Link
        href="https://a6gysudbx4d.typeform.com/to/V4dZO5A3"
        target="_blank"
        className="ml-1 underline"
      >
        here
      </Link>
    </div>
  );
};

export default AlphaNotificationBar;
