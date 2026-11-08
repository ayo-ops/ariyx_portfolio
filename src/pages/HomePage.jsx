import React from "react";
import Navbar from "../components/layout/Navbar";
import Footer from "../components/layout/Footer";
import HeroSection from "../components/home/HeroSection";
import VerifiedProofSection from "../components/home/VerifiedProofSection";
import ServicesSection from "../components/home/ServicesSection";
import SystemBlueprintSection from "../components/home/SystemBlueprintSection";
import PortfolioSection from "../components/home/PortfolioSection";
import FounderSection from "../components/home/FounderSection";
import MethodologySection from "../components/home/MethodologySection";
import TestimonialsSection from "../components/home/TestimonialsSection";
import ConversionSection from "../components/home/ConversionSection";

export default function HomePage() {
  return (
    <div className="min-h-screen bg-midnight text-soft-white font-sans antialiased selection:bg-electric/25 selection:text-white">
      <Navbar />
      <main>
        <HeroSection />
        <VerifiedProofSection />
        <ServicesSection />
        <SystemBlueprintSection />
        <PortfolioSection />
        <FounderSection />
        <MethodologySection />
        <TestimonialsSection />
        <ConversionSection />
      </main>
      <Footer />
    </div>
  );
}
