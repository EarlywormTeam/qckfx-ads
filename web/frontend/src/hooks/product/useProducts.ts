import { createContext, useContext } from 'react';
import { Product } from '../../types/product';

interface ProductContextType {
  products: Product[];
  loading: boolean;
  error: string | null;
}

export const ProductContext = createContext<ProductContextType>({
  products: [],
  loading: false,
  error: null,
});

export const useProducts = () => useContext(ProductContext);
