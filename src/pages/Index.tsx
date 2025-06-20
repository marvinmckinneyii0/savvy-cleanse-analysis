
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
import SignupForm from '@/components/SignupForm';

const Index = () => {
  return (
    <div className="flex flex-col min-h-screen">
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
        <section className="py-16 bg-white dark:bg-savvy-dark">
          <div className="container px-4 md:px-6">
            <SignupForm />
          </div>
        </section>
      </main>
      <Footer />
    </div>
  );
};

export default Index;
