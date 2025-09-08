
import React from 'react';
import { Link } from 'react-router-dom';

const Footer = () => {
  return (
    <footer className="border-t bg-white dark:bg-savvy-dark">
      <div className="container px-4 md:px-6 py-10">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          <div>
            <div className="flex items-center gap-2">
              <img 
                src="/lovable-uploads/bce4ab85-e6f8-4810-9883-f33ee1cfb90d.png" 
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
              <li><Link to="/features" className="text-muted-foreground hover:text-savvy-gold transition-colors">Features</Link></li>
              <li><Link to="/pricing" className="text-muted-foreground hover:text-savvy-gold transition-colors">Pricing</Link></li>
              <li><Link to="/testimonials" className="text-muted-foreground hover:text-savvy-gold transition-colors">Testimonials</Link></li>
              <li><Link to="/api" className="text-muted-foreground hover:text-savvy-gold transition-colors">API</Link></li>
            </ul>
          </div>
          
          <div>
            <h4 className="text-sm font-semibold mb-4">Resources</h4>
            <ul className="space-y-2 text-sm">
              <li><Link to="/documentation" className="text-muted-foreground hover:text-savvy-gold transition-colors">Documentation</Link></li>
              <li><Link to="/guides" className="text-muted-foreground hover:text-savvy-gold transition-colors">Guides</Link></li>
              <li><Link to="/api-reference" className="text-muted-foreground hover:text-savvy-gold transition-colors">API Reference</Link></li>
              <li><Link to="/blog" className="text-muted-foreground hover:text-savvy-gold transition-colors">Blog</Link></li>
            </ul>
          </div>
          
          <div>
            <h4 className="text-sm font-semibold mb-4">Company</h4>
            <ul className="space-y-2 text-sm">
              <li><Link to="/about" className="text-muted-foreground hover:text-savvy-gold transition-colors">About</Link></li>
              <li><Link to="/careers" className="text-muted-foreground hover:text-savvy-gold transition-colors">Careers</Link></li>
              <li><Link to="/contact" className="text-muted-foreground hover:text-savvy-gold transition-colors">Contact</Link></li>
              <li><Link to="/savvy-analytics" className="text-muted-foreground hover:text-savvy-gold transition-colors">Savvy Analytics</Link></li>
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
