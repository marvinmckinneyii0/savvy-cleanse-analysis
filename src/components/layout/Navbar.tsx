
import React from 'react';
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';

const Navbar = () => {
  return (
    <header className="border-b bg-white sticky top-0 z-50">
      <div className="container flex items-center justify-between h-16 px-4 md:px-6">
        <Link to="/" className="flex items-center gap-2">
          <div className="w-8 h-8 rounded bg-savvy-blue flex items-center justify-center text-white font-bold">S</div>
          <span className="text-xl font-semibold tracking-tight">SavvyClean</span>
        </Link>
        
        <nav className="hidden md:flex items-center gap-6 text-sm">
          <Link to="/" className="font-medium transition-colors hover:text-savvy-blue">
            Home
          </Link>
          <Link to="/" className="font-medium transition-colors hover:text-savvy-blue">
            Features
          </Link>
          <Link to="/" className="font-medium transition-colors hover:text-savvy-blue">
            Pricing
          </Link>
          <Link to="/" className="font-medium transition-colors hover:text-savvy-blue">
            Documentation
          </Link>
        </nav>
        
        <div className="flex items-center gap-4">
          <Link to="/dashboard">
            <Button variant="ghost" className="hidden md:inline-flex">
              Dashboard
            </Button>
          </Link>
          <Link to="/dashboard">
            <Button className="bg-savvy-blue hover:bg-savvy-blue/90">
              Try Now
            </Button>
          </Link>
        </div>
      </div>
    </header>
  );
};

export default Navbar;
