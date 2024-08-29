import React from 'react';
import { Link } from 'react-router-dom';

const NotFound: React.FC = () => {
  return (
    <div className="w-full h-full text-center p-12 text-text-white bg-background-accent">
      <h1 className="text-4xl font-bold mb-4">404 - Page Not Found</h1>
      <p className="text-lg mb-6">Sorry, the page you are looking for does not exist.</p>
      <Link to="/" className="mt-4 px-4 py-2 border border-text-darkPrimary text-text-darkPrimary hover:bg-text-darkPrimary hover:text-white transition-colors duration-300 rounded">
            Go back to homepage
          </Link>
    </div>
  );
};

export default NotFound;
