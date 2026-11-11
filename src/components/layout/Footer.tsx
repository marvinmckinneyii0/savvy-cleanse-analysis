
import React from 'react';
import { Link } from 'react-router-dom';

const Footer = () => {
  return (
    <footer className="border-t bg-white dark:bg-savvy-dark">
      <div className="container px-4 md:px-6 py-10">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div>
            <div className="flex items-center gap-2">
              <img 
                src="/lovable-uploads/1a5ff488-1ca2-4dda-8f25-3e165a31f539.png" 
                alt="Savvy Analytics Logo" 
                className="w-8 h-8"
              />
              <span className="text-xl font-semibold tracking-tight">SAINT</span>
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
            </ul>
          </div>
          
          <div>
            <h4 className="text-sm font-semibold mb-4">Company</h4>
            <ul className="space-y-2 text-sm">
              <li><Link to="/about" className="text-muted-foreground hover:text-savvy-gold transition-colors">About</Link></li>
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
            <Link to="/terms" className="text-muted-foreground hover:text-savvy-gold transition-colors">
              Terms
            </Link>
            <Link to="/privacy" className="text-muted-foreground hover:text-savvy-gold transition-colors">
              Privacy
            </Link>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
