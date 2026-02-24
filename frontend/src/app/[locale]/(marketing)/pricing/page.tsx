import { PricingSection } from "@/components/landing/pricing-section";
import { IndexingPricingSection } from "@/components/landing/indexing-pricing-section";
import { PricingFaqSection } from "@/components/landing/pricing-faq-section";

export default function PricingPage() {
  return (
    <>
      <PricingSection />
      <IndexingPricingSection />
      <PricingFaqSection />
    </>
  );
}
