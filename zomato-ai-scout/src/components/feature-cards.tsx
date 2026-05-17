import Image from "next/image";
import { ArrowRight, ScrollText, Star } from "lucide-react";

const CAFE_IMAGE =
  "https://images.unsplash.com/photo-1554118811-1e0d58224f24?w=600&q=80";

export function FeatureCards() {
  return (
    <div className="mx-auto max-w-7xl px-5 pb-16">
      <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
        <article className="flex flex-col gap-6 rounded-xl border border-outline-variant/30 bg-white p-6 shadow-sm sm:flex-row sm:items-center md:col-span-2 md:p-8">
          <div className="relative aspect-square w-full shrink-0 overflow-hidden rounded-lg shadow-md sm:w-2/5 md:w-1/3">
            <Image
              src={CAFE_IMAGE}
              alt="Warm interior of Artisan Bakery and Cafe"
              fill
              className="object-cover"
              sizes="(max-width: 768px) 100vw, 33vw"
            />
          </div>
          <div className="min-w-0 flex-1">
            <span className="mb-2 block text-xs font-bold text-primary">
              LOCAL FAVORITE
            </span>
            <h3 className="font-heading mb-2 text-xl font-semibold text-on-surface">
              Artisan Bakery &amp; Cafe
            </h3>
            <p className="mb-4 text-sm italic leading-relaxed text-on-surface-variant">
              &ldquo;The AI Scout accurately predicted my love for sourdough. This
              hidden gem in Manhattan has the best crust I&apos;ve ever
              tasted.&rdquo;
            </p>
            <div className="flex flex-wrap items-center gap-4">
              <div className="flex items-center rounded bg-surface-container px-2 py-1">
                <Star
                  className="size-4 fill-primary text-primary"
                  aria-hidden
                />
                <span className="ml-1 text-xs font-bold">4.9</span>
              </div>
              <span className="text-xs text-on-surface-variant">
                2.4 km away
              </span>
            </div>
          </div>
        </article>

        <article className="flex flex-col justify-between rounded-xl bg-primary-container p-8 text-white shadow-md">
          <div>
            <div className="mb-6 flex size-12 items-center justify-center rounded-lg bg-white/20">
              <ScrollText className="size-6 text-white" aria-hidden />
            </div>
            <h3 className="font-heading mb-2 text-xl font-semibold">
              Personal History
            </h3>
            <p className="text-sm leading-relaxed text-white/85">
              Your Scout gets smarter with every order. View how your
              preferences have evolved.
            </p>
          </div>
          <button
            type="button"
            className="group mt-6 flex items-center gap-2 font-semibold text-white"
          >
            View Trends
            <ArrowRight className="size-4 transition-transform group-hover:translate-x-1" />
          </button>
        </article>
      </div>
    </div>
  );
}
