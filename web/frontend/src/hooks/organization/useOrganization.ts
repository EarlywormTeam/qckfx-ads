import { createContext, useContext } from 'react';
import { Organization } from '../../types/organization';

interface OrganizationContextType {
  organizations: Organization[];
  organization: Organization | null;
  setOrganization: (org: Organization | null) => void;
  fetchOrganizations: () => Promise<void>;
}

export const OrganizationContext = createContext<OrganizationContextType>({
  organizations: [],
  organization: null,
  setOrganization: () => {},
  fetchOrganizations: async () => {},
});

export const useOrganization = () => useContext(OrganizationContext);
