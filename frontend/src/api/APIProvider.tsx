import { API, APIContext } from '.';

export const APIProvider: React.FC<React.PropsWithChildren<{ api: API }>> = ({ children, api }) => {
  return <APIContext.Provider value={api}>{children}</APIContext.Provider>;
};