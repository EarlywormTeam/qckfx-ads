import { Outlet } from 'react-router-dom';
import Header from '../components/header/Header';
import { Organization } from '@/types/organization';

interface RootLayoutProps {
  organizations: Organization[];
}

const RootLayout: React.FC<RootLayoutProps> = ({ organizations }) => {
  return (
    <div className="flex flex-col h-full w-full">
      <Header
        organizations={organizations}
      />
      <div className="flex-grow overflow-hidden">
        <main className="h-full overflow-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default RootLayout;
