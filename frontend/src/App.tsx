import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import LandingPage from './pages/landing/LandingPage';
import HomePage from './pages/app/home/HomePage';
import ProductPage from './pages/app/product/ProductPage';
import ErrorBoundary from './pages/ErrorBoundary';
import NotFound from './pages/NotFound';
import CreateProductPage from './pages/app/createProduct/CreateProductPage';
import { Toaster } from "@/components/ui/toaster";
import RootLayout from './layouts/RootLayout';
import { useState, useEffect } from 'react';
import { useCookies } from 'react-cookie';
import { APIProvider } from './api/APIProvider';
import { API } from './api';

function App() {
  const [cookies] = useCookies(['session']);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [bypassAuth, setBypassAuth] = useState(false);
  const isDev = process.env.NODE_ENV === 'development';

  useEffect(() => {
    const checkLoginStatus = () => {
      if (cookies.session) {
        try {
          const sessionData = JSON.parse(cookies.session);
          setIsLoggedIn(!!sessionData.user_id);
        } catch (error) {
          console.error('Error parsing session cookie:', error);
          setIsLoggedIn(false);
        }
      } else {
        setIsLoggedIn(false);
      }
    };

    checkLoginStatus();
  }, [cookies.session]);

  const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
    if (isLoggedIn || bypassAuth) {
      return <>{children}</>;
    }
    return <Navigate to="/" replace />;
  };

  return (
    <ErrorBoundary>
      <APIProvider api={new API()}>
        <BrowserRouter>
          {isDev && (
            <button onClick={() => setBypassAuth(!bypassAuth)}>
              {bypassAuth ? 'Disable' : 'Enable'} Auth Bypass
            </button>
          )}
          <Routes>
            <Route element={<RootLayout isLoggedIn={isLoggedIn} bypassAuth={bypassAuth} />}>
              <Route path="/" element={<LandingPage />} />
              <Route path="/app" element={
                <ProtectedRoute>
                  <HomePage />
                </ProtectedRoute>
              } />
              <Route path="/app/product/:productName" element={
                <ProtectedRoute>
                  <ProductPage />
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
      </APIProvider>
    </ErrorBoundary>
  )
}

export default App
