
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Navigate, Routes, Route } from "react-router-dom";
import Index from "./pages/Index";
import NotFound from "./pages/NotFound";
import Features from "./pages/features";
import Pricing from "./pages/pricing";
import About from "./pages/about";
import Contact from "./pages/contact";
import SavvyAnalytics from "./pages/savvy-analytics";
import { ThemeProvider } from "./components/ThemeProvider";

const queryClient = new QueryClient();

const App = () => (
  <ThemeProvider defaultTheme="dark">
    <QueryClientProvider client={queryClient}>
        <TooltipProvider>
        <Toaster />
        <Sonner />
        <Routes>
          <Route path="/" element={<Index />} />
          {/* Concierge beta (decision D8): the dashboard, API, API reference, testimonials,
              careers, blog, documentation and guides pages are not routed. Old /dashboard
              links land on the contact form instead of a 404. */}
          <Route path="/dashboard" element={<Navigate to="/contact" replace />} />
          {/* Product Pages */}
          <Route path="/features" element={<Features />} />
          <Route path="/pricing" element={<Pricing />} />
          {/* Company Pages */}
          <Route path="/about" element={<About />} />
          <Route path="/contact" element={<Contact />} />
          <Route path="/savvy-analytics" element={<SavvyAnalytics />} />
          {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </TooltipProvider>
    </QueryClientProvider>
  </ThemeProvider>
);

export default App;
