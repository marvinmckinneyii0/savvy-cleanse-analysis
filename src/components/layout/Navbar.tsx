
import React from 'react';
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { ThemeSwitcher } from '@/components/ThemeSwitcher';

const Navbar = () => {
  const handleSignupClick = () => {
    const signupForm = document.getElementById('signup-form');
    if (signupForm) {
      signupForm.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <header className="border-b bg-white dark:bg-savvy-dark sticky top-0 z-50">
      <div className="container flex items-center justify-between h-16 px-4 md:px-6">
        <Link to="/" className="flex items-center gap-2">
          <img 
            src="/lovable-uploads/1a5ff488-1ca2-4dda-8f25-3e165a31f539.png" 
            alt="Savvy Analytics Logo" 
            className="w-8 h-8"
          />
          <span className="text-xl font-semibold tracking-tight">SavvyClean</span>
        </Link>
        
        <nav className="hidden md:flex items-center gap-6 text-sm">
          <a href="#features" className="font-medium transition-colors hover:text-savvy-gold">
            Features
          </a>
          <a href="#pricing" className="font-medium transition-colors hover:text-savvy-gold">
            Pricing
          </a>
        </nav>
        
        <div className="flex items-center gap-4">
          <ThemeSwitcher />
          <Button 
            onClick={handleSignupClick}
            className="bg-savvy-gold hover:bg-savvy-gold/90 text-white"
          >
            Sign Up
          </Button>
        </div>
      </div>
    </header>
  );
};

export default Navbar;
