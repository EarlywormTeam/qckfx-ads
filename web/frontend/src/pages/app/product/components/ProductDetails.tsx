import React from 'react';
import { Product } from '@/types/product';
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";

interface ProductDetailsProps {
  product: Product;
  prompt: string;
  setPrompt: (prompt: string) => void;
  handleGenerateImages: () => void;
  isGenerating: boolean;
}

const ProductDetails: React.FC<ProductDetailsProps> = ({ 
  product, 
  prompt, 
  setPrompt, 
  handleGenerateImages, 
  isGenerating 
}) => {
  return (
    <div className="w-1/3 pr-4">
      <div className="relative mb-2" style={{ paddingBottom: '100%' }}>
        <img 
          src={product.primaryImageUrl} 
          alt={product.name} 
          className="absolute inset-0 w-full h-full object-contain rounded-lg shadow-lg"
        />
      </div>
      <h2 className="text-xl font-semibold">{product.name}</h2>
      <Textarea
        placeholder="Enter your prompt (multiple lines supported)"
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        className="w-full p-2 border rounded my-4 flex-grow"
        rows={4}
      />
      <Button 
        onClick={handleGenerateImages}
        className="w-full mb-12"
        disabled={isGenerating}
      >
        {isGenerating ? 'Generating...' : 'Generate Images'}
      </Button>
    </div>
  );
};

export default ProductDetails;