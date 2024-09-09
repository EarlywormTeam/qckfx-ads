import { Outlet } from 'react-router-dom';
import Header from '../components/header/Header';

type Organization = {
  id: string;
  name: string;
};

interface RootLayoutProps {
  isLoggedIn: boolean;
  bypassAuth: boolean;
  organizations: Organization[];
  selectedOrg: Organization | null;
  setSelectedOrg: (org: Organization | null) => void;
}

const RootLayout: React.FC<RootLayoutProps> = ({ isLoggedIn, bypassAuth, organizations, selectedOrg, setSelectedOrg }) => {
  return (
    <div className="flex flex-col min-h-screen">
      <Header
        bypassAuth={bypassAuth}
        isLoggedIn={isLoggedIn}
        organizations={organizations}
        selectedOrg={selectedOrg}
        setSelectedOrg={setSelectedOrg}
      />
      <main className="flex-grow">
        <Outlet />
      </main>
    </div>
  );
};

export default RootLayout;
