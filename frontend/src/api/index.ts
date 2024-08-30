import React from 'react';
import { ProductAPI } from './product';

export class API {

  createProductAPI(): ProductAPI {
    return new ProductAPI();
  }
}

export const api = new API();

// Create a React context for the API
export const APIContext = React.createContext<API | null>(null);

// Create a custom hook to use the API
export const useAPI = (): API => {
  const context = React.useContext(APIContext);
  if (context === null) {
    throw new Error('useAPI must be used within an APIProvider');
  }
  return context;
};