import React, { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import Logo from './Logo';
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

// Add Organization type
type Organization = {
  id: string;
  name: string;
};

interface HeaderProps {
  bypassAuth: boolean;
}

const Header: React.FC<HeaderProps> = ({ bypassAuth }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const isLandingPage = location.pathname === '/';
  const isLoggedIn = localStorage.getItem('isLoggedIn') === 'true';
  const [selectedOrg, setSelectedOrg] = useState<string>('');

  // Mock data for organizations - replace with actual data fetching logic
  const organizations: Organization[] = [
    { id: '1', name: 'Org 1' },
    { id: '2', name: 'Org 2' },
    { id: '3', name: 'Org 3' },
  ];

  const handleSignIn = (event: React.MouseEvent) => {
    event.preventDefault();
    if (bypassAuth) {
      // If bypass auth is enabled, set isLoggedIn to true in localStorage
      localStorage.setItem('isLoggedIn', 'true');
      // Redirect to the app page
      window.location.href = '/app';
    } else {
      // If bypass auth is not enabled, proceed with normal authentication
      window.location.href = '/auth';
    }
  };

  const handleLogoClick = () => {
    navigate(isLoggedIn ? '/app' : '/');
  };

  return (
    <header className={`flex justify-between items-center p-6 ${isLandingPage ? 'bg-transparent' : 'bg-background-white'}`}>
      <div onClick={handleLogoClick} className="cursor-pointer">
        <Logo />
      </div>
      <div className="flex items-center space-x-4">
        {isLoggedIn && !isLandingPage && (
          <Select 
            value={selectedOrg} 
            onValueChange={setSelectedOrg}
          >
            <SelectTrigger className="w-[200px]">
              <SelectValue placeholder="Select organization" />
            </SelectTrigger>
            <SelectContent>
              {organizations.map((org) => (
                <SelectItem key={org.id} value={org.id}>{org.name}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}
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
      </div>
    </header>
  );
};

export default Header;
