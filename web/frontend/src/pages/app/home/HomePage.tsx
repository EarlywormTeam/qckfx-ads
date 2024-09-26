import React, { useState, useEffect } from 'react';
// import { useNavigate } from 'react-router-dom';
import ProductList from './ProductList';
// import { Button } from "@/components/ui/button";
import { useAPI } from '@/api';
import { Product } from '@/types/product';
import { Organization } from '@/types/organization';

// Remove the Organization type definition from here

interface HomePageProps {
  selectedOrg: Organization | null;
}

const HomePage: React.FC<HomePageProps> = ({ selectedOrg }) => {
  // const navigate = useNavigate();
  const api = useAPI();
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchProducts = async () => {
      if (!selectedOrg) {
        setProducts([]);
        setLoading(false);
        return;
      }

      setLoading(true);
      try {
        const productAPI = api.createProductAPI();
        const fetchedProducts = await productAPI.getProducts(selectedOrg.id);
        setProducts(fetchedProducts);
      } catch (error) {
        console.error('Error fetching products:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchProducts();
  }, [api, selectedOrg]); // Add selectedOrg to the dependency array

  // const handleCreateProduct = () => {
  //   navigate('/app/product/create');
  // };

  return (
    <div className="h-full w-full bg-background-white">
      <main className="max-w-6xl mx-auto p-6">
        <div className="flex flex-col mb-12">
          <div className="flex justify-center mb-8">
            {/* <Button 
              variant="secondary" 
              className="rounded-full items-center px-6 py-3 bg-background-action text-text-white hover:bg-background-dark"
              onClick={handleCreateProduct}
            >
              Create New Product
            </Button> */}
          </div>
          <h2 className="text-2xl font-bold text-text-darkPrimary mb-6">Products & Styles</h2>
        </div>
        {loading ? (
          <p>Loading products & styles...</p>
        ) : (
          <ProductList products={products} />
        )}
      </main>
    </div>
  );
};

export default HomePage;
