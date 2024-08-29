import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import LandingPage from './pages/landing/LandingPage';
import HomePage from './pages/app/home/HomePage';
import ErrorBoundary from './pages/ErrorBoundary';
import NotFound from './pages/NotFound';
import CreateProductPage from './pages/app/createProduct/CreateProductPage';
import { Toaster } from "@/components/ui/toaster";
import RootLayout from './layouts/RootLayout';
import { useState, useEffect } from 'react';

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(() => {
    return localStorage.getItem('isLoggedIn') === 'true';
  });
  const [bypassAuth, setBypassAuth] = useState(true);

  useEffect(() => {
    localStorage.setItem('isLoggedIn', isLoggedIn.toString());
  }, [isLoggedIn]);

  const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
    if (isLoggedIn || bypassAuth) {
      return <>{children}</>;
    }
    return <Navigate to="/" replace />;
  };

  return (
    <ErrorBoundary>
      <BrowserRouter>
        <button onClick={() => setBypassAuth(!bypassAuth)}>
          {bypassAuth ? 'Disable' : 'Enable'} Auth Bypass
        </button>
        <Routes>
          <Route element={<RootLayout isLoggedIn={isLoggedIn} />}>
            <Route path="/" element={<LandingPage />} />
            <Route path="/app" element={
              <ProtectedRoute>
                <HomePage />
              </ProtectedRoute>
            } />
            <Route path="/app/product/create" element={
              <ProtectedRoute>
                <CreateProductPage />
              </ProtectedRoute>
            } />
            <Route path="*" element={<NotFound />} />
          </Route>
        </Routes>
        <Toaster />
      </BrowserRouter>
    </ErrorBoundary>
  )
}

export default App
