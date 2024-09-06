import React from 'react';
import { ProductAPI } from './product';
import { GenerateAPI } from './generate';
import WaitlistAPI from './waitlistAPI';

export class API {
  createProductAPI(): ProductAPI {
    return new ProductAPI();
  }

  createGenerateAPI(): GenerateAPI {
    return new GenerateAPI();
  }

  createWaitlistAPI(): WaitlistAPI {
    return new WaitlistAPI();
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