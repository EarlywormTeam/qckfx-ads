import React, { useState, useCallback } from 'react';
import { useToast } from "@/components/ui/use-toast";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { FixedSizeGrid as Grid, GridChildComponentProps } from 'react-window';
import AutoSizer from 'react-virtualized-auto-sizer';
import { useLocation } from 'react-router-dom';
import { Product } from '@/types/product';
import { useGenerateAPI } from '@/api/generate';

const ProductPage: React.FC = () => {
  const location = useLocation();
  const [product, /*setProduct*/] = useState<Product | null>(location.state?.product || null);
  const [loading, /*setLoading*/] = useState<boolean>(false);
  const [prompt, setPrompt] = useState<string>('');
  const [generatedImages, setGeneratedImages] = useState<{ url: string }[]>([]);
  const { toast } = useToast();
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const generateImageAPI = useGenerateAPI(); 

  const handleGenerateImages = useCallback(async () => {
    if (prompt.trim() === '') {
      toast({
        title: "Error",
        description: "Please enter a prompt before generating images.",
        variant: "destructive",
      });
      return;
    }

    setIsGenerating(true);
    try {
      const generationJobId = await generateImageAPI.generateProductImage(product!.id, prompt, 4);
      const result = await generateImageAPI.pollGenerationJob(generationJobId);
      
      if (result.status === 'completed' && result.images) {
        setGeneratedImages(result.images);
      } else {
        throw new Error('Image generation failed');
      }
    } catch (error) {
      console.error('Error generating images:', error);
      toast({
        title: "Error",
        description: "Failed to generate images. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsGenerating(false);
    }
  }, [product, prompt, toast, generateImageAPI]);

  const Cell: React.FC<GridChildComponentProps> = ({ columnIndex, rowIndex, style }) => {
    if (!product) return null;
    const index = rowIndex * 4 + columnIndex;
    if (index >= product.additionalImageUrls.length) return null;
    return (
      <div style={{...style, padding: '8px'}}>
        <img src={product.additionalImageUrls[index]} alt={`Recent ${index + 1}`} className="w-full h-full object-cover rounded-lg shadow-md" />
      </div>
    );
  };

  if (loading) {
    return <div className="p-8">Loading...</div>;
  }

  if (!product) {
    return <div className="p-8">Product not found</div>;
  }

  return (
    <div className="container mx-auto px-6 py-12">
      <h1 className="text-3xl font-bold mb-6">{product.name}</h1>
      
      <div className="mb-10">
        <img 
          src={product.primaryImageUrl} 
          alt={product.name} 
          className="w-56 h-56 object-contain rounded-lg shadow-lg"
        />
      </div>

      <div className="flex flex-col md:flex-row gap-10 mb-16">
        <div className="flex-1">
          <Textarea
            placeholder="Enter your prompt here..."
            value={prompt}
            onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setPrompt(e.target.value)}
            className="w-full h-40 mb-6 p-4"
          />
          <Button 
            onClick={handleGenerateImages}
            className="w-full bg-background-action text-text-white py-3"
            disabled={isGenerating}
          >
            {isGenerating ? 'Generating...' : 'Generate Images'}
          </Button>
        </div>
        <div className="flex-1">
          <h2 className="text-2xl font-semibold mb-4">Generated Images</h2>
          {isGenerating ? (
            <div className="flex items-center justify-center h-56">
              <p>Generating images...</p>
            </div>
          ) : generatedImages.length > 0 ? (
            <div className="grid grid-cols-2 gap-4">
              {generatedImages.map((img, index) => (
                <img 
                  key={index} 
                  src={img.url} 
                  alt={`Generated ${index + 1}`} 
                  className="w-full h-56 object-cover rounded-lg shadow-md"
                />
              ))}
            </div>
          ) : (
            <div className="flex items-center justify-center h-56 bg-gray-100 rounded-lg">
              <p className="text-gray-500">No generated images yet</p>
            </div>
          )}
        </div>
      </div>

      <h2 className="text-2xl font-semibold mb-6">Recently Created Images</h2>
      <div style={{ height: '450px' }}>
        <AutoSizer>
          {({ height, width }: { height: number; width: number }) => (
            <Grid
              columnCount={4}
              columnWidth={width / 4}
              height={height}
              rowCount={Math.ceil(product.additionalImageUrls.length / 4)}
              rowHeight={height / 3}
              width={width}
            >
              {Cell}
            </Grid>
          )}
        </AutoSizer>
      </div>
    </div>
  );
};

export default ProductPage;
