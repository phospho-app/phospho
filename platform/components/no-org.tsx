import Link from "next/link";

export default function NoOrg() {
  // To be displayed when the user has no org but is logged in
  return (
    <div className="flex flex-col justify-center items-center mt-5 mb-7 mx-10 text-justify">
      <h2 className="text-xl font-semibold">Welcome!</h2>
      <p className="text-neutral-100 mt-10 max-w-[1089px]">
        Thank you for creating an account on phospho. The team will get in
        contact with you as soon as possible, using the email address you
        provided.
      </p>
      <p className="text-neutral-100 mt-4 max-w-[1089px]">
        Our aim is to understand your organization's needs and ensure a smooth
        onboarding process. You can expect to hear from us within the next 24-48
        hours. If you have any immediate questions or concerns, feel free to
        reach out to us at{" "}
        <a className="italic" href="mailto:contact@phospho.app">
          contact@phospho.app
        </a>
      </p>
    </div>
  );
}
