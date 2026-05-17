import Image from "next/image";
import { Sparkles } from "lucide-react";

const HERO_IMAGE =
  "https://images.unsplash.com/photo-1544025162-d76694265947?w=1920&q=85";

export function Hero() {
  return (
    <section className="relative flex h-[min(500px,70vh)] items-center overflow-hidden">
      <div className="absolute inset-0 z-0">
        <Image
          src={HERO_IMAGE}
          alt="Gourmet plated scallops and fine dining dish"
          fill
          className="object-cover"
          priority
          sizes="100vw"
        />
        <div className="absolute inset-0 hero-gradient" aria-hidden />
      </div>
      <div className="relative z-10 mx-auto w-full max-w-7xl px-5 text-white">
        <div className="max-w-2xl">
          <div className="mb-4 flex w-fit items-center gap-2 rounded-full border border-white/20 bg-white/10 px-4 py-1 backdrop-blur-md">
            <Sparkles className="size-4 text-rose-200" aria-hidden />
            <span className="text-xs font-bold uppercase tracking-wide">
              Premium AI Concierge
            </span>
          </div>
          <h1 className="font-heading mb-6 text-3xl font-bold leading-tight tracking-tight md:text-4xl">
            Discover your next favorite meal with AI Scout.
          </h1>
          <p className="text-lg leading-relaxed text-white/90 md:text-xl">
            Our intelligent engine analyzes millions of reviews and preferences
            to curate a personalized dining experience just for you.
          </p>
        </div>
      </div>
    </section>
  );
}
