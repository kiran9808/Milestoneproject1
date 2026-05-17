import Link from "next/link";
import { Bot, Globe } from "lucide-react";
import { STREAMLIT_APP_URL } from "@/lib/backend";

export function SiteFooter() {
  return (
    <footer className="border-t border-outline-variant bg-surface-container-highest">
      <div className="mx-auto flex max-w-7xl flex-col gap-8 px-5 py-12 md:flex-row md:justify-between md:items-start">
        <div className="max-w-xs">
          <span className="font-heading mb-4 block text-xl font-bold text-primary">
            Zomato AI
          </span>
          <p className="text-sm text-on-surface-variant">
            Revolutionizing the way you discover food through the power of
            artificial intelligence and community insights.
          </p>
        </div>
        <div className="grid grid-cols-2 gap-12 sm:grid-cols-3">
          <div>
            <h4 className="mb-4 text-xs font-bold uppercase tracking-wider text-on-surface">
              Company
            </h4>
            <div className="flex flex-col gap-2">
              <FooterLink href="#">About Us</FooterLink>
              <FooterLink href="#">Partner with Us</FooterLink>
              <FooterLink href="#">Careers</FooterLink>
            </div>
          </div>
          <div>
            <h4 className="mb-4 text-xs font-bold uppercase tracking-wider text-on-surface">
              Product
            </h4>
            <div className="flex flex-col gap-2">
              {STREAMLIT_APP_URL ? (
                <FooterLink href={STREAMLIT_APP_URL} external>
                  Streamlit backend UI
                </FooterLink>
              ) : null}
            </div>
          </div>
          <div>
            <h4 className="mb-4 text-xs font-bold uppercase tracking-wider text-on-surface">
              Legal
            </h4>
            <div className="flex flex-col gap-2">
              <FooterLink href="#">Terms of Service</FooterLink>
              <FooterLink href="#">Privacy Policy</FooterLink>
              <FooterLink href="#">Cookie Policy</FooterLink>
            </div>
          </div>
        </div>
      </div>
      <div className="mx-auto mt-8 flex max-w-7xl flex-col items-center justify-between gap-4 border-t border-outline-variant/30 px-5 pt-8 sm:flex-row">
        <p className="text-sm text-on-surface-variant">
          © {new Date().getFullYear()} Zomato Ltd. All rights reserved.
        </p>
        <div className="flex gap-4 text-on-surface-variant">
          <Globe className="size-5 cursor-pointer hover:text-primary" aria-hidden />
          <Bot className="size-5 cursor-pointer hover:text-primary" aria-hidden />
        </div>
      </div>
    </footer>
  );
}

function FooterLink({
  href,
  children,
  external = false,
}: {
  href: string;
  children: React.ReactNode;
  external?: boolean;
}) {
  if (external) {
    return (
      <a
        href={href}
        target="_blank"
        rel="noopener noreferrer"
        className="text-sm text-on-surface-variant transition-colors hover:text-primary"
      >
        {children}
      </a>
    );
  }

  return (
    <Link
      href={href}
      className="text-sm text-on-surface-variant transition-colors hover:text-primary"
    >
      {children}
    </Link>
  );
}
