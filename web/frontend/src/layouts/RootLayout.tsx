import { Outlet } from 'react-router-dom';
import Header from '../components/header/Header';

type Organization = {
  id: string;
  name: string;
};

interface RootLayoutProps {
  organizations: Organization[];
  selectedOrg: Organization | null;
  setSelectedOrg: (org: Organization | null) => void;
}

const RootLayout: React.FC<RootLayoutProps> = ({ organizations, selectedOrg, setSelectedOrg }) => {
  return (
    <div className="flex flex-col h-full w-full">
      <Header
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
