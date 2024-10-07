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
import { APIProvider } from './api/APIProvider';
import { API } from './api';
import { Organization } from '@/types/organization';
import { useAuth } from '@/hooks/useAuth';

function App() {
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [selectedOrg, setSelectedOrg] = useState<Organization | null>(null);
  const { isAuthenticated, isLoading } = useAuth();

  useEffect(() => {
    const fetchOrganizations = async () => {
      try {
        const response = await fetch('/api/user/organization', {
          credentials: 'include'
        });
        if (response.ok) {
          const data = await response.json();
          setOrganizations(data.organizations);
          if (!selectedOrg && data.organizations.length > 0) {
            setSelectedOrg(data.organizations[0]);
          }
        }
      } catch (error) {
        console.error('Error fetching organizations:', error);
      }
    };

    if (isAuthenticated) {
      fetchOrganizations();
    }
  }, [isAuthenticated]);

  const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
    if (isLoading) {
      return <div>Loading...</div>;
    }
    if (!isAuthenticated) {
      return <Navigate to="/" replace />;
    }
    return <>{children}</>;
  };

  return (
    <ErrorBoundary>
      <APIProvider api={new API()}>
        <BrowserRouter>
          <Routes>
            <Route element={
              <RootLayout
                organizations={organizations}
                selectedOrg={selectedOrg}
                setSelectedOrg={setSelectedOrg}
              />
            }>
              <Route path="/" element={isAuthenticated ? <Navigate to="/app" replace /> : <LandingPage />} />
              <Route path="/app" element={
                <ProtectedRoute>
                  <HomePage selectedOrg={selectedOrg} />
                </ProtectedRoute>
              } />
              <Route path="/app/product/:productName" element={
                <ProtectedRoute>
                  <ProductPage selectedOrg={selectedOrg} />
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
