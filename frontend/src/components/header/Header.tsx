import React, { useState, useEffect } from 'react';
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
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const isLandingPage = location.pathname === '/';
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [selectedOrg, setSelectedOrg] = useState<Organization | null>(null);

  const isDev = process.env.ENV === 'development';

  useEffect(() => {
    const checkLoginStatus = async () => {
      try {
        const response = await fetch('/api/auth/status', {
          credentials: 'include' // This is important to include cookies in the request
        });
        if (response.ok) {
          const data = await response.json();
          setOrganizations(data.organizations);
          setSelectedOrg(data.organizations[0]);
          setIsLoggedIn(true);
        } else {
          setIsLoggedIn(false);
        }
      } catch {
        setIsLoggedIn(false);
      }
    };

    checkLoginStatus();
  }, []); // Remove cookies.session from the dependency array

  const handleSignIn = (event: React.MouseEvent) => {
    event.preventDefault();
    if (bypassAuth) {
      // If bypass auth is enabled, redirect to the app page
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
            value={selectedOrg?.id} 
            onValueChange={(value) => setSelectedOrg(organizations.find(org => org.id === value) || null)}
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
        {!isDev && bypassAuth && (
          <Button
            variant="ghost"
            className="text-text-darkPrimary font-bold text-md"
            onClick={() => {
              // Add logic to disable auth bypass
            }}
          >
            Disable auth bypass
          </Button>
        )}
      </div>
    </header>
  );
};

export default Header;
