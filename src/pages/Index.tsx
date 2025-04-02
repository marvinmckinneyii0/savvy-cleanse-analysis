
import React from 'react';
import Navbar from '@/components/layout/Navbar';
import Footer from '@/components/layout/Footer';
import Hero from '@/components/Hero';
import Features from '@/components/Features';
import AnalysisTypes from '@/components/AnalysisTypes';
import DataFlow from '@/components/DataFlow';
import Pricing from '@/components/Pricing';
import CTA from '@/components/CTA';
import BusinessIntelligence from '@/components/BusinessIntelligence';
import Feedback from '@/components/Feedback';
import { ThemeSwitcher } from '@/components/ThemeSwitcher';

const Index = () => {
  return (
    <div className="flex flex-col min-h-screen">
      <div className="fixed top-4 right-4 z-50">
        <ThemeSwitcher />
      </div>
      <Navbar />
      <main className="flex-grow">
        <Hero />
        <Features />
        <BusinessIntelligence />
        <AnalysisTypes />
        <DataFlow />
        <Pricing />
        <Feedback />
        <CTA />
      </main>
      <Footer />
    </div>
  );
};

export default Index;
