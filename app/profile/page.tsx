import Link from "next/link";
import Image from "next/image";
export default function profile() {
  return (
    <div>
      <div className="flex justify-center">
        <h1 className="max-w-xs text-3xl font-semibold leading-10 tracking-tight text-black dark:text-zinc-50">
          Profile
        </h1>
      </div>
      <Link href="/acc">
        <button className="flex h-12 w-full items-center justify-center rounded-full border border-solid border-black/[.08] px-5 transition-colors hover:border-transparent hover:bg-black/[.04] dark:border-white/[.145] dark:hover:bg-[#1a1a1a] md:w-[158px]">
          return
        </button>
      </Link>
      <div className="flex justify-center border border-gray-300 p-2 rounded-[100%]">
        <Image src="/file.svg" width={100} height={100} alt="test"></Image>
      </div>
      <div className="flex justify-center">
        <input
          type="text"
          className="md:w-[158px] focus:border-brand block w-full px-3 py-2.5 shadow-xs placeholder:text-body  hover:bg-black/[.04] border border-gray-300"
          placeholder="First Name"
        ></input>
        <input
          type="text"
          className="md:w-[158px] focus:border-brand block w-full px-3 py-2.5 shadow-xs placeholder:text-body  hover:bg-black/[.04] border border-gray-300"
          placeholder="Last Name"
        ></input>
        <select name="Grade Level" id="Grade-Level">
          <option value="fresh">Freshman</option>
          <option value="soph">Sophomore</option>
          <option value="junior">Junior</option>
          <option value="senior">Senior</option>
        </select>
        <button className="flex h-12 w-full items-center justify-center gap-2 rounded-full bg-foreground px-5 text-background transition-colors hover:bg-[#383838] dark:hover:bg-[#ccc] md:w-[158px]">
          Submit
        </button>
      </div>
    </div>
  );
}
