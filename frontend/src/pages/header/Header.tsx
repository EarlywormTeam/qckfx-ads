import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import Logo from './Logo';
import { Button } from "@/components/ui/button";

const Header: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const isLandingPage = location.pathname === '/';
  const isLoggedIn = localStorage.getItem('isLoggedIn') === 'true';

  const handleSignIn = (event: React.MouseEvent) => {
    event.preventDefault();
    window.location.href = '/auth';
  };

  const handleLogoClick = () => {
    navigate(isLoggedIn ? '/app' : '/');
  };

  return (
    <header className={`flex justify-between items-center p-6 ${isLandingPage ? 'bg-transparent' : 'bg-background-white'}`}>
      <div onClick={handleLogoClick} className="cursor-pointer">
        <Logo />
      </div>
      {isLandingPage || !isLoggedIn ? (
        <Button 
          variant="ghost" 
          className={`font-bold text-md ${isLandingPage ? 'text-text-black' : 'text-text-darkPrimary'}`}
          onClick={handleSignIn}
        >
          Sign In
        </Button>
      ) : (
        <Button 
          variant="ghost" 
          className="text-text-darkPrimary font-bold text-md"
        >
          Account
        </Button>
      )}
    </header>
  );
};

export default Header;
