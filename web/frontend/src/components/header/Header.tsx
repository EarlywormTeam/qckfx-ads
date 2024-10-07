import React, { useRef } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import Logo from './Logo';
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Organization } from '@/types/organization';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { Plus } from "lucide-react";
import { useAssetAPI } from '@/api/asset';
import { useAuth } from '@/hooks/useAuth';

interface HeaderProps {
  organizations: Organization[];
  selectedOrg: Organization | null;
  setSelectedOrg: (org: Organization | null) => void;
}

const Header: React.FC<HeaderProps> = ({ organizations, selectedOrg, setSelectedOrg }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const isLandingPage = location.pathname === '/';
  const fileInputRef = useRef<HTMLInputElement>(null);
  const folderInputRef = useRef<HTMLInputElement>(null);
  const assetAPI = useAssetAPI();
  const { isAuthenticated, isLoading, signIn, signOut } = useAuth();

  const handleSignIn = (event: React.MouseEvent) => {
    event.preventDefault();
    signIn();
  };

  const handleLogoClick = () => {
    navigate(isAuthenticated ? '/app' : '/');
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    console.log('uploading files', files, selectedOrg);
    if (files && selectedOrg) {
      try {
        await assetAPI.uploadFiles(Array.from(files), selectedOrg.id);
        console.log('Files uploaded successfully');
        // TODO: Handle successful upload (e.g., show a success message, refresh file list)
      } catch (error) {
        console.error('Error uploading files:', error);
        // TODO: Handle upload error (e.g., show an error message)
      }
    }
  };

  const handleUploadClick = (isFolder: boolean) => {
    console.log('clicked upload files', isFolder);
    const inputRef = isFolder ? folderInputRef : fileInputRef;
    inputRef.current?.click();
  };

  const handleSignOut = () => {
    signOut();
    navigate('/');
  };

  const handleOrganizationChange = (value: string) => {
    if (value === "sign-out") {
      handleSignOut();
    } else {
      setSelectedOrg(organizations.find(org => org.id === value) || null);
    }
  };

  return (
    <header className={`flex justify-between items-center p-6 ${isLandingPage ? 'bg-transparent' : 'bg-background-white'}`}>
      <div onClick={handleLogoClick} className="cursor-pointer">
        <Logo />
      </div>
      <div className="flex items-center space-x-4">
        {isAuthenticated && !isLandingPage && (
          <>
            <input
              type="file"
              ref={fileInputRef}
              style={{ display: 'none' }}
              onChange={handleFileUpload}
              multiple
            />
            <input
              type="file"
              ref={folderInputRef}
              style={{ display: 'none' }}
              onChange={handleFileUpload}
              {...{ webkitdirectory: "", directory: "" } as React.InputHTMLAttributes<HTMLInputElement>}
              multiple
            />
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" size="icon">
                  <Plus className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent>
                <DropdownMenuItem onClick={() => handleUploadClick(false)}>Upload File</DropdownMenuItem>
                <DropdownMenuItem onClick={() => handleUploadClick(true)}>Upload Folder</DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
            <Select 
              value={selectedOrg?.id} 
              onValueChange={handleOrganizationChange}
            >
              <SelectTrigger className="w-[200px]">
                <SelectValue placeholder="Select organization" />
              </SelectTrigger>
              <SelectContent>
                {organizations.map((org) => (
                  <SelectItem key={org.id} value={org.id}>{org.name}</SelectItem>
                ))}
                <SelectItem value="sign-out" className="text-red-500">
                  Sign Out
                </SelectItem>
              </SelectContent>
            </Select>
          </>
        )}
        {(isLandingPage || !isAuthenticated) && !isLoading ? (
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
