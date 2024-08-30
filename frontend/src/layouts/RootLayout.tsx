import React from 'react';
import { Outlet } from 'react-router-dom';
import Header from '../pages/header/Header';

interface RootLayoutProps {
  isLoggedIn: boolean;
  bypassAuth: boolean;
}

const RootLayout: React.FC<RootLayoutProps> = ({ isLoggedIn, bypassAuth }) => {
  return (
    <div className="w-full h-full">
      <Header bypassAuth={bypassAuth} />
      <Outlet />
    </div>
  );
};

export default RootLayout;
