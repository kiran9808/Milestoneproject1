import { FeatureCards } from "@/components/feature-cards";
import { Hero } from "@/components/hero";
import { RecommendationEngine } from "@/components/recommendation-engine";
import { SiteFooter } from "@/components/site-footer";
import { SiteHeader } from "@/components/site-header";

export default function Home() {
  return (
    <div className="flex min-h-screen flex-col bg-surface">
      <SiteHeader />
      <main className="flex-1">
        <Hero />
        <RecommendationEngine />
        <FeatureCards />
      </main>
      <SiteFooter />
    </div>
  );
}
