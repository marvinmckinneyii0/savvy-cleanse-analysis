
import React from 'react';
import Navbar from '@/components/layout/Navbar';
import Footer from '@/components/layout/Footer';
import Hero from '@/components/Hero';
import Features from '@/components/Features';
import AnalysisTypes from '@/components/AnalysisTypes';
import DataFlow from '@/components/DataFlow';
import Pricing from '@/components/Pricing';
import CTA from '@/components/CTA';

const Index = () => {
  return (
    <div className="flex flex-col min-h-screen">
      <Navbar />
      <main className="flex-grow">
        <Hero />
        <Features />
        <AnalysisTypes />
        <DataFlow />
        <Pricing />
        <CTA />
      </main>
      <Footer />
    </div>
  );
};

export default Index;
