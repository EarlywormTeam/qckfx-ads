import React from 'react';
import { Outlet } from 'react-router-dom';
import Header from '../pages/header/Header';

interface RootLayoutProps {
  isLoggedIn: boolean;
}

const RootLayout: React.FC<RootLayoutProps> = ({ isLoggedIn }) => {
  return (
    <div className="flex flex-col h-full w-full">
      <Header />
      <main className="flex-grow">
        <Outlet context={{ isLoggedIn }} />
      </main>
    </div>
  );
};

export default RootLayout;
