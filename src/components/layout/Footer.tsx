
import React from 'react';

const Footer = () => {
  return (
    <footer className="border-t bg-white dark:bg-savvy-dark">
      <div className="container px-4 md:px-6 py-10">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          <div>
            <div className="flex items-center gap-2">
              <img 
                src="/lovable-uploads/savvy-logo.png" 
                alt="Savvy Analytics Logo" 
                className="w-8 h-8"
              />
              <span className="text-xl font-semibold tracking-tight">SavvyClean</span>
            </div>
            <p className="mt-2 text-sm text-muted-foreground">
              Turn chaos into clarity, one dataset at a time.
            </p>
          </div>
          
          <div>
            <h4 className="text-sm font-semibold mb-4">Product</h4>
            <ul className="space-y-2 text-sm">
              <li><a href="#" className="text-muted-foreground hover:text-savvy-gold transition-colors">Features</a></li>
              <li><a href="#" className="text-muted-foreground hover:text-savvy-gold transition-colors">Pricing</a></li>
              <li><a href="#" className="text-muted-foreground hover:text-savvy-gold transition-colors">Testimonials</a></li>
              <li><a href="#" className="text-muted-foreground hover:text-savvy-gold transition-colors">API</a></li>
            </ul>
          </div>
          
          <div>
            <h4 className="text-sm font-semibold mb-4">Resources</h4>
            <ul className="space-y-2 text-sm">
              <li><a href="#" className="text-muted-foreground hover:text-savvy-gold transition-colors">Documentation</a></li>
              <li><a href="#" className="text-muted-foreground hover:text-savvy-gold transition-colors">Guides</a></li>
              <li><a href="#" className="text-muted-foreground hover:text-savvy-gold transition-colors">API Reference</a></li>
              <li><a href="#" className="text-muted-foreground hover:text-savvy-gold transition-colors">Blog</a></li>
            </ul>
          </div>
          
          <div>
            <h4 className="text-sm font-semibold mb-4">Company</h4>
            <ul className="space-y-2 text-sm">
              <li><a href="#" className="text-muted-foreground hover:text-savvy-gold transition-colors">About</a></li>
              <li><a href="#" className="text-muted-foreground hover:text-savvy-gold transition-colors">Careers</a></li>
              <li><a href="#" className="text-muted-foreground hover:text-savvy-gold transition-colors">Contact</a></li>
              <li><a href="https://www.savvyanalytics.info" className="text-muted-foreground hover:text-savvy-gold transition-colors">Savvy Analytics</a></li>
            </ul>
          </div>
        </div>
        
        <div className="border-t mt-10 pt-6 flex flex-col md:flex-row justify-between items-center">
          <p className="text-sm text-muted-foreground">
            © {new Date().getFullYear()} Savvy Analytics. All rights reserved.
          </p>
          <div className="flex items-center gap-4 mt-4 md:mt-0">
            <a href="#" className="text-muted-foreground hover:text-savvy-gold transition-colors">
              Terms
            </a>
            <a href="#" className="text-muted-foreground hover:text-savvy-gold transition-colors">
              Privacy
            </a>
            <a href="#" className="text-muted-foreground hover:text-savvy-gold transition-colors">
              Cookies
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
