
import React from 'react';
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { ThemeSwitcher } from '@/components/ThemeSwitcher';

const Navbar = () => {
  return (
    <header className="border-b bg-white dark:bg-savvy-dark sticky top-0 z-50">
      <div className="container flex items-center justify-between h-16 px-4 md:px-6">
        <Link to="/" className="flex items-center gap-2">
          <img 
            src="/lovable-uploads/savvy-logo.png" 
            alt="Savvy Analytics Logo" 
            className="w-8 h-8"
          />
          <span className="text-xl font-semibold tracking-tight">SavvyClean</span>
        </Link>
        
        <nav className="hidden md:flex items-center gap-6 text-sm">
          <Link to="/" className="font-medium transition-colors hover:text-savvy-gold">
            Home
          </Link>
          <Link to="/" className="font-medium transition-colors hover:text-savvy-gold">
            Features
          </Link>
          <Link to="/" className="font-medium transition-colors hover:text-savvy-gold">
            Pricing
          </Link>
          <Link to="/" className="font-medium transition-colors hover:text-savvy-gold">
            Documentation
          </Link>
        </nav>
        
        <div className="flex items-center gap-4">
          <ThemeSwitcher />
          <Link to="/dashboard">
            <Button variant="ghost" className="hidden md:inline-flex">
              Dashboard
            </Button>
          </Link>
          <Link to="/dashboard">
            <Button className="bg-savvy-gold hover:bg-savvy-gold/90 text-white">
              Try Now
            </Button>
          </Link>
        </div>
      </div>
    </header>
  );
};

export default Navbar;
