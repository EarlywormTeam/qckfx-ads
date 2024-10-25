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
import { useToast } from '@/components/ui/use-toast';
import SearchBar from './SearchBar';
import { useOrganization } from '@/hooks/organization/useOrganization';

interface HeaderProps {
  organizations: Organization[];
}

const Header: React.FC<HeaderProps> = ({ organizations }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const { organization, setOrganization } = useOrganization();
  const isLandingPage = location.pathname === '/';
  const fileInputRef = useRef<HTMLInputElement>(null);
  const folderInputRef = useRef<HTMLInputElement>(null);
  const assetAPI = useAssetAPI();
  const { isAuthenticated, isLoading, signIn, signOut } = useAuth();
  const { toast } = useToast();

  const handleSignIn = (event: React.MouseEvent) => {
    event.preventDefault();
    signIn();
  };

  const handleLogoClick = () => {
    navigate(isAuthenticated ? '/app' : '/');
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    console.log('Uploading files:', files, organization);
    if (files && organization) {
      const allowedFormats = ['image/png', 'image/jpeg', 'image/webp'];
      const filteredFiles = Array.from(files).filter(file => allowedFormats.includes(file.type));

      if (filteredFiles.length === 0) {
        console.error('No valid image files selected');
        toast({
          title: "Upload Error",
          description: "No valid image files selected. Please upload PNG, JPEG, or WEBP formats.",
          variant: "destructive",
        });
        return;
      }

      let uploadToastId: string | undefined;
      let uploadPromises: Promise<{ fileName: string; progress: number }>[] = [];
      try {
        const { id } = toast({
          title: "Uploading Files",
          description: (
            <div className="w-full">
              <div className="flex justify-between mb-1">
                <span className="text-sm font-medium text-gray-700">Progress</span>
                <span className="text-sm font-medium text-gray-700" id="progress-percentage">0%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2.5">
                <div
                  className="h-2.5 rounded-full bg-blue-500"
                  style={{ width: '0%' }}
                  id="upload-progress"
                ></div>
              </div>
            </div>
          ),
          variant: "default",
        });
        uploadToastId = id;

        const totalFiles = filteredFiles.length;
        let completedFiles = 0;
        let hasErrorOccurred = false;

        // Define a single progress callback to update overall progress
        const progressCallbacks = filteredFiles.map(() => (progress: number) => {
          const newProgress = ((completedFiles + progress) / totalFiles) * 100;
          const progressBar = document.getElementById('upload-progress');
          const progressPercentage = document.getElementById('progress-percentage');
          if (progressBar) {
            progressBar.style.width = `${Math.min(newProgress, 100)}%`;
          }
          if (progressPercentage) {
            progressPercentage.textContent = `${Math.round(newProgress)}%`;
          }
        });

        // Start uploading files with progress callbacks
        uploadPromises = await assetAPI.uploadFiles(filteredFiles, organization.id, progressCallbacks);

        // Handle upload results
        await Promise.all(uploadPromises.map(async (promise, index) => {
          try {
            await promise;
            completedFiles += 1;
            const newProgress = (completedFiles / totalFiles) * 100;
            const progressBar = document.getElementById('upload-progress');
            const progressPercentage = document.getElementById('progress-percentage');
            if (progressBar) {
              progressBar.style.width = `${Math.min(newProgress, 100)}%`;
            }
            if (progressPercentage) {
              progressPercentage.textContent = `${Math.round(newProgress)}%`;
            }
          } catch (error) {
            console.error(`Error uploading file ${filteredFiles[index].name}:`, error);
            hasErrorOccurred = true;
            toast({
              title: "Upload Error",
              description: `Failed to upload ${filteredFiles[index].name}`,
              variant: "destructive",
            });
          }
        }));

        if (hasErrorOccurred) {
          toast({
            title: "Upload Completed with Errors",
            description: "Some files failed to upload.",
            variant: "destructive",
          });
        } else {
          toast({
            title: "Upload Successful",
            description: "All files have been uploaded successfully.",
            variant: "default",
          });
        }

      } catch (error) {
        console.error('Error uploading files:', error);
        toast({
          title: "Upload Error",
          description: "An unexpected error occurred during file upload.",
          variant: "destructive",
        });
      } finally {
        if (uploadToastId) {
          // Optionally dismiss the upload progress toast after completion
          // Uncomment the line below if you want to dismiss it automatically
          // toast.dismiss(uploadToastId);
        }
        // Reset file inputs
        if (fileInputRef.current) {
          fileInputRef.current.value = '';
        }
        if (folderInputRef.current) {
          folderInputRef.current.value = '';
        }

        // Notify the server about the uploaded files
        try {
          const uploadedFileNames = await Promise.all(
            uploadPromises.map(async (promise) => {
              const result = await promise;
              return result.fileName;
            })
          );
          await assetAPI.notifyUploadedFiles(organization.id, uploadedFileNames);
        } catch (error) {
          console.error('Error notifying server about uploaded files:', error);
          toast({
            title: "Upload Error",
            description: "Failed to upload files.",
            variant: "destructive",
          });
        }
      }
    }
  };

  const handleUploadClick = (isFolder: boolean) => {
    console.log('Clicked upload:', isFolder ? 'Folder' : 'File');
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
      setOrganization(organizations.find(org => org.id === value) || null);
    }
  };

  const handleGenerateVideo = () => {
    navigate('/app/generate/video');
  };

  return (
    <header className={`flex justify-between items-start px-4 py-2 ${isLandingPage ? 'bg-transparent' : 'bg-background-white'}`}>
      <div onClick={handleLogoClick} className="cursor-pointer">
        <Logo />
      </div>
      {isAuthenticated && !isLandingPage && (
        <div className="flex-grow px-8 mt-1">
          <SearchBar />
        </div>
      )}
      <div className="flex items-start space-x-4 mt-1">
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
                <DropdownMenuItem onClick={handleGenerateVideo}>Generate Video</DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
            <div className="flex items-center space-x-4">
              <Select 
                value={organization?.id} 
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
            </div>
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
