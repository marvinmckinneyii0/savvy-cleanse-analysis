
import React from 'react';

const Footer = () => {
  return (
    <footer className="border-t bg-white">
      <div className="container px-4 md:px-6 py-10">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          <div>
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded bg-savvy-blue flex items-center justify-center text-white font-bold">S</div>
              <span className="text-xl font-semibold tracking-tight">SavvyClean</span>
            </div>
            <p className="mt-2 text-sm text-muted-foreground">
              Turn chaos into clarity, one dataset at a time.
            </p>
          </div>
          
          <div>
            <h4 className="text-sm font-semibold mb-4">Product</h4>
            <ul className="space-y-2 text-sm">
              <li><a href="#" className="text-muted-foreground hover:text-savvy-blue transition-colors">Features</a></li>
              <li><a href="#" className="text-muted-foreground hover:text-savvy-blue transition-colors">Pricing</a></li>
              <li><a href="#" className="text-muted-foreground hover:text-savvy-blue transition-colors">Testimonials</a></li>
              <li><a href="#" className="text-muted-foreground hover:text-savvy-blue transition-colors">API</a></li>
            </ul>
          </div>
          
          <div>
            <h4 className="text-sm font-semibold mb-4">Resources</h4>
            <ul className="space-y-2 text-sm">
              <li><a href="#" className="text-muted-foreground hover:text-savvy-blue transition-colors">Documentation</a></li>
              <li><a href="#" className="text-muted-foreground hover:text-savvy-blue transition-colors">Guides</a></li>
              <li><a href="#" className="text-muted-foreground hover:text-savvy-blue transition-colors">API Reference</a></li>
              <li><a href="#" className="text-muted-foreground hover:text-savvy-blue transition-colors">Blog</a></li>
            </ul>
          </div>
          
          <div>
            <h4 className="text-sm font-semibold mb-4">Company</h4>
            <ul className="space-y-2 text-sm">
              <li><a href="#" className="text-muted-foreground hover:text-savvy-blue transition-colors">About</a></li>
              <li><a href="#" className="text-muted-foreground hover:text-savvy-blue transition-colors">Careers</a></li>
              <li><a href="#" className="text-muted-foreground hover:text-savvy-blue transition-colors">Contact</a></li>
              <li><a href="https://www.savvyanalytics.info" className="text-muted-foreground hover:text-savvy-blue transition-colors">Savvy Analytics</a></li>
            </ul>
          </div>
        </div>
        
        <div className="border-t mt-10 pt-6 flex flex-col md:flex-row justify-between items-center">
          <p className="text-sm text-muted-foreground">
            © {new Date().getFullYear()} Savvy Analytics. All rights reserved.
          </p>
          <div className="flex items-center gap-4 mt-4 md:mt-0">
            <a href="#" className="text-muted-foreground hover:text-savvy-blue transition-colors">
              Terms
            </a>
            <a href="#" className="text-muted-foreground hover:text-savvy-blue transition-colors">
              Privacy
            </a>
            <a href="#" className="text-muted-foreground hover:text-savvy-blue transition-colors">
              Cookies
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
