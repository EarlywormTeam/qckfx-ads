import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import Logo from './Logo';
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Organization } from '@/types/organization';

// Remove the Organization type definition from here

interface HeaderProps {
  bypassAuth: boolean;
  isLoggedIn: boolean;
  organizations: Organization[];
  selectedOrg: Organization | null;
  setSelectedOrg: (org: Organization | null) => void;
}

const Header: React.FC<HeaderProps> = ({ bypassAuth, isLoggedIn, organizations, selectedOrg, setSelectedOrg }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const isLandingPage = location.pathname === '/';

  const handleSignIn = (event: React.MouseEvent) => {
    event.preventDefault();
    if (bypassAuth) {
      window.location.href = '/app';
    } else {
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
      </div>
    </header>
  );
};

export default Header;
