import Image from "next/image";
import Link from "next/link";
import { Bell, Clock, Search } from "lucide-react";

const nav = [
  { label: "Home", href: "/", active: false },
  { label: "AI Scout", href: "/#scout", active: true },
  { label: "Orders", href: "/#orders", active: false },
];

export function SiteHeader() {
  return (
    <header className="sticky top-0 z-50 border-b border-outline-variant/20 bg-surface shadow-sm">
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-5 py-4">
        <div className="flex items-center gap-8">
          <Link href="/" className="font-heading text-xl font-extrabold">
            <span className="text-primary">Zomato</span>
            <span className="text-on-surface"> AI</span>
          </Link>
          <nav className="hidden gap-6 md:flex">
            {nav.map((item) => (
              <Link
                key={item.label}
                href={item.href}
                className={
                  item.active
                    ? "rounded border-b-2 border-primary px-2 py-1 font-bold text-primary"
                    : "rounded px-2 py-1 text-on-surface-variant transition-colors hover:bg-surface-container"
                }
              >
                {item.label}
              </Link>
            ))}
          </nav>
        </div>
        <div className="flex items-center gap-2 sm:gap-4">
          <div className="hidden w-56 items-center rounded-full bg-surface-container px-4 py-2 md:flex lg:w-64">
            <Search
              className="mr-2 size-5 shrink-0 text-on-surface-variant"
              aria-hidden
            />
            <input
              type="search"
              placeholder="Search dishes..."
              className="w-full bg-transparent text-sm outline-none placeholder:text-on-surface-variant/80"
            />
          </div>
          <button
            type="button"
            className="rounded-full p-2 text-on-surface-variant transition-colors hover:bg-surface-container"
            aria-label="Notifications"
          >
            <Bell className="size-5" />
          </button>
          <button
            type="button"
            className="rounded-full p-2 text-on-surface-variant transition-colors hover:bg-surface-container"
            aria-label="Order history"
          >
            <Clock className="size-5" />
          </button>
          <Image
            src="https://images.unsplash.com/photo-1560250097-0b93528c311a?w=160&h=160&fit=crop&q=80"
            alt="User profile"
            width={40}
            height={40}
            className="size-10 rounded-full border-2 border-outline-variant object-cover"
          />
        </div>
      </div>
    </header>
  );
}
