import Link from "next/link";

export default function calendar() {
  return (
    <div>
      <div className="flex justify-center">
        <h1 className="max-w-xs text-3xl font-semibold leading-10 tracking-tight text-black dark:text-zinc-50">
          Calendar
        </h1>
      </div>
      <Link href="/acc">
        <button className="flex h-12 w-full items-center justify-center rounded-full border border-solid border-black/[.08] px-5 transition-colors hover:border-transparent hover:bg-black/[.04] dark:border-white/[.145] dark:hover:bg-[#1a1a1a] md:w-[158px]">
          return
        </button>
      </Link>
    </div>
  );
}
