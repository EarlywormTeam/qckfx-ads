import { useState, ReactNode, useEffect } from 'react';
import { OrganizationContext } from './useOrganization';
import { Organization } from '../../types/organization';
import { useAuth } from '../useAuth';

export const OrganizationProvider = ({ children }: { children: ReactNode }) => {
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [organization, setOrganization] = useState<Organization | null>(null);
  const { isAuthenticated } = useAuth();

  const fetchOrganizations = async () => {
    try {
      const response = await fetch('/api/user/organization', {
        credentials: 'include',
      });
      if (response.ok) {
        const data = await response.json();
        setOrganizations(data.organizations);
        if (!organization && data.organizations.length > 0) {
          setOrganization(data.organizations[0]);
        }
      } else {
        console.error('Failed to fetch organizations:', response.statusText);
      }
    } catch (error) {
      console.error('Error fetching organizations:', error);
    }
  };

  useEffect(() => {
    if (isAuthenticated) {
      fetchOrganizations();
    }
  }, [isAuthenticated]);

  return (
    <OrganizationContext.Provider
      value={{
        organizations,
        organization,
        setOrganization,
        fetchOrganizations,
      }}
    >
      {children}
    </OrganizationContext.Provider>
  );
};