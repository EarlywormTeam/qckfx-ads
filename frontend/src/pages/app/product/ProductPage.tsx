import React, { useState } from 'react';
import { useToast } from "@/components/ui/use-toast";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { FixedSizeGrid as Grid, GridChildComponentProps } from 'react-window';
import AutoSizer from 'react-virtualized-auto-sizer';
import { useLocation } from 'react-router-dom';
import { z } from 'zod';

const ProductSchema = z.object({
  id: z.string(),
  name: z.string(),
  imagePath: z.string(),
  recentImages: z.array(z.string()).optional(),
});

type Product = z.infer<typeof ProductSchema>;

const ProductPage: React.FC = () => {
  const location = useLocation();
  // const { productName } = useParams<{ productName: string }>();
  const [product, /*setProduct*/] = useState<Product | null>(location.state?.product || null);
  const [loading, /*setLoading*/] = useState<boolean>(false);
  const [prompt, setPrompt] = useState<string>('');
  const [generatedImages, setGeneratedImages] = useState<string[]>([]);
  const { toast } = useToast();

  // useEffect(() => {
  //   const fetchProduct = async (name: string) => {
  //     setLoading(true);
  //     try {
  //       // Replace this with your actual API call
  //       const response = await fetch(`/api/products/name/${encodeURIComponent(name)}`);
  //       if (!response.ok) {
  //         throw new Error('Failed to fetch product');
  //       }
  //       const data = await response.json();
  //       setProduct(data);
  //     } catch (error) {
  //       console.error('Error fetching product:', error);
  //       toast({
  //         title: "Error",
  //         description: "Failed to load product details.",
  //         variant: "destructive",
  //       });
  //     } finally {
  //       setLoading(false);
  //     }
  //   };

  //   if (location.state && 'product' in location.state) {
  //     setProduct(location.state.product as Product);
  //   } else if (productName) {
  //     fetchProduct(productName);
  //   } else {
  //     toast({
  //       title: "Error",
  //       description: "No product information available.",
  //       variant: "destructive",
  //     });
  //   }
  // }, [location.state, productName, toast]);

  const handleGenerateImages = () => {
    if (prompt.trim() === '') {
      toast({
        title: "Error",
        description: "Please enter a prompt before generating images.",
        variant: "destructive",
      });
      return;
    }

    // TODO: Implement actual image generation logic here
    console.log("Generating images with prompt:", prompt);
    // For now, we'll just set some placeholder images
    setGeneratedImages(['/placeholder1.jpg', '/placeholder2.jpg', '/placeholder3.jpg', '/placeholder4.jpg']);
  };

  const Cell: React.FC<GridChildComponentProps> = ({ columnIndex, rowIndex, style }) => {
    if (!product) return null;
    const index = rowIndex * 4 + columnIndex;
    if (index >= (product.recentImages?.length ?? 0)) return null;
    return (
      <div style={{...style, padding: '8px'}}>
        <img src={product.recentImages?.[index]} alt={`Recent ${index + 1}`} className="w-full h-full object-cover rounded-lg shadow-md" />
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
          src={product.imagePath} 
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
          >
            Generate Images
          </Button>
        </div>
        <div className="flex-1">
          <div className="grid grid-cols-2 gap-6">
            {generatedImages.map((img, index) => (
              <img key={index} src={img} alt={`Generated ${index + 1}`} className="w-full rounded-lg shadow-md" />
            ))}
          </div>
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
              rowCount={Math.ceil((product.recentImages?.length ?? 0) / 4)}
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
