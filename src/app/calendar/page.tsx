import Link from "next/link";
import CalendarView from "@/src/components/calendar-view";

export default function calendar() {
  return (
    <div className="w-full h-dvh">
      <div className="flex flex-row w-full h-9/10">
        <div className="rounded-md p-4 m-4 w-1/3">user stuff
          <h1>Welcome back user</h1>
          <div className="bg-mauve p-4">
            <Link href="/acc" className="flex h-12 w-full items-center justify-center rounded-full border border-solid border-black/[.08] px-5 transition-colors hover:border-transparent hover:bg-black/[.04] dark:border-white/[.145] dark:hover:bg-[#1a1a1a] md:w-[158px]">
              Account
            </Link>
          </div>
        </div>
        <div className="rounded-md w-2/3 p-4 m-4 min-h-0 overflow-hidden flex">
          <CalendarView />
        </div>
      </div>
    </div>
  );
}
