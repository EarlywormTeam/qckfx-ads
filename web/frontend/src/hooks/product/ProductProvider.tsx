import { useState, useEffect, ReactNode } from 'react';
import { Product } from '../../types/product';
import { useOrganization } from '../organization/useOrganization';
import { useProductAPI } from '../../api/product';
import { ProductContext } from './useProducts';

export const ProductProvider = ({ children }: { children: ReactNode }) => {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const productAPI = useProductAPI();
  const { organization } = useOrganization();
  
  useEffect(() => {
    if (!organization?.id) {
      console.log("[PRODUCT PROVIDER] No organization id");
      setProducts([]);
      return;
    }

    const fetchProducts = async () => {
      console.log("[PRODUCT PROVIDER] Fetching products for organization", organization.id);
      setLoading(true);
      setError(null);
      try {
        const fetchedProducts = await productAPI.getProducts(organization.id);
        setProducts(fetchedProducts);
      } catch (err) {
        setError('Failed to fetch products.');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchProducts();
  }, [organization?.id, productAPI]);

  return (
    <ProductContext.Provider value={{ products, loading, error }}>
      {children}
    </ProductContext.Provider>
  );
};