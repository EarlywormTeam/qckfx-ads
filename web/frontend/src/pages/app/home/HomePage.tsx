import React from 'react';
import ProductList from './ProductList';
import { useProducts } from '@/hooks/product/useProducts';

const HomePage: React.FC = () => {
  const { products, loading } = useProducts();

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
