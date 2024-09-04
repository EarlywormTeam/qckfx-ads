import React, { useState, useCallback, useRef } from 'react';
import { useToast } from "@/components/ui/use-toast";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Slider } from "@/components/ui/slider";
import { useLocation } from 'react-router-dom';
import { Product } from '@/types/product';
import { useGenerateAPI } from '@/api/generate';
import { Trash2, RefreshCw, Maximize2, History, ArrowLeft, ChevronLeft, ChevronRight, Lightbulb, Infinity, Target, X, Loader2 } from 'lucide-react';

const ProductPage: React.FC = () => {
  const location = useLocation();
  const [product, /*setProduct*/] = useState<Product | null>(location.state?.product || null);
  const [loading, /*setLoading*/] = useState<boolean>(false);
  const [prompt, setPrompt] = useState<string>('');
  const [generatedImages, setGeneratedImages] = useState<{ url: string, isPlaceholder?: boolean }[]>([]);
  const { toast } = useToast();
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const generateImageAPI = useGenerateAPI(); 

  const [selectedImage, setSelectedImage] = useState<{ url: string, versions: string[] } | null>(null);
  const [currentVersion, setCurrentVersion] = useState(0);
  const [isVersionHistoryOpen, setIsVersionHistoryOpen] = useState(false);
  const [fullscreenImage, setFullscreenImage] = useState<number | null>(null);
  const [currentPage, setCurrentPage] = useState(0);
  const imagesPerPage = 4; // Keep this fixed at 4 images per page (2x2 grid)
  const gridRef = useRef<HTMLDivElement>(null);

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
    // Add placeholder images
    setGeneratedImages(prevImages => [
      ...prevImages,
      ...Array(4).fill({ url: '', isPlaceholder: true })
    ]);

    try {
      const generationJobId = await generateImageAPI.generateProductImage(product!.id, prompt, 4);
      const result = await generateImageAPI.pollGenerationJob(generationJobId);
      if (result.status === 'completed' && result.images) {
        setGeneratedImages(prevImages => [
          ...prevImages.filter(img => !img.isPlaceholder),
          ...(result.images || []).map(img => ({ ...img, isPlaceholder: false }))
        ]);
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
      // Remove placeholder images on error
      setGeneratedImages(prevImages => prevImages.filter(img => !img.isPlaceholder));
    } finally {
      setIsGenerating(false);
    }
  }, [product, prompt, toast, generateImageAPI]);

  const handleDelete = (index: number) => {
    setGeneratedImages(images => images.filter((_, i) => i !== index));
  };

  const handleRefine = (index: number) => {
    console.log('Refining image', index);
  };

  const handleFullScreen = (index: number) => {
    setFullscreenImage(index);
  };

  const handleCloseFullScreen = () => {
    setFullscreenImage(null);
  };

  const handleNavigateFullScreen = (direction: 'prev' | 'next') => {
    if (fullscreenImage === null) return;
    const newIndex = direction === 'prev' 
      ? (fullscreenImage - 1 + generatedImages.length) % generatedImages.length
      : (fullscreenImage + 1) % generatedImages.length;
    setFullscreenImage(newIndex);
  };

  const handleVersionHistoryOpen = (image: { url: string, versions: string[] }) => {
    setSelectedImage(image);
    setCurrentVersion(image.versions.length - 1);
    setIsVersionHistoryOpen(true);
  };

  const handleVersionChange = (value: number[]) => {
    setCurrentVersion(value[0]);
  };

  const handlePageChange = useCallback((direction: 'prev' | 'next') => {
    const newPage = direction === 'prev' ? Math.max(0, currentPage - 0.5) : currentPage + 0.5;
    setCurrentPage(newPage);
    
    if (gridRef.current) {
      const scrollWidth = gridRef.current.clientWidth; // the width of the grid
      gridRef.current.scrollTo({
        left: newPage * scrollWidth,
        behavior: 'smooth'
      });
    }
  }, [currentPage]);

  if (loading) return <div className="p-8">Loading...</div>;
  if (!product) return <div className="p-8">Product not found</div>;

  const samplePrompts = [
    "Sleek product on a minimalist white background",
    "Product in use by a happy customer",
    "Close-up of product features with text labels",
    "Product displayed in a lifestyle setting"
  ];

  return (
    <div className="p-4 max-w-6xl mx-auto">
      <div className="flex items-start mb-4">
        {/* Left Column: Product Image and Details */}
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
        
        {/* Right Column: Generated Images or Version History */}
        <div className="w-2/3">
          {!isVersionHistoryOpen ? (
            <div>
              {generatedImages.length > 0 ? (
                <div className="relative">
                  <div 
                    ref={gridRef}
                    className="grid gap-4 mb-4 overflow-hidden"
                    style={{ 
                      gridTemplateRows: 'repeat(2, 1fr)',
                      gridAutoFlow: 'column',
                      gridAutoColumns: 'min-content',
                      maxWidth: 'calc(600px + 1rem)', // 2 * 300px (max image width) + 1rem (gap)
                      maxHeight: 'calc(600px + 1rem)', // 2 * 300px (max image height) + 1rem (gap)
                      margin: '0 auto', // Center the grid
                      scrollSnapType: 'x mandatory'
                    }}
                  >
                    {generatedImages.map((image, index) => (
                      <div 
                        key={index} 
                        className="aspect-square w-[300px] h-[300px] scroll-snap-align-start"
                      >
                        {image.isPlaceholder ? (
                          <div className="w-full h-full bg-gradient-to-br from-gray-200 to-gray-300 rounded-lg flex items-center justify-center">
                            <Loader2 className="w-8 h-8 text-gray-400 animate-spin" />
                          </div>
                        ) : (
                          <div className="relative group w-full h-full">
                            <img 
                              src={image.url} 
                              alt={`Generated ${index + 1}`} 
                              className="w-full h-full object-contain rounded-lg shadow-md"
                            />
                            <div className="absolute inset-0 bg-black bg-opacity-50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center rounded-lg">
                              <Button variant="ghost" size="sm" onClick={() => handleDelete(index)} className="mr-2">
                                <Trash2 size={20} className="text-white" />
                              </Button>
                              <Button variant="ghost" size="sm" onClick={() => handleRefine(index)} className="mr-2">
                                <RefreshCw size={20} className="text-white" />
                              </Button>
                              <Button variant="ghost" size="sm" onClick={() => handleFullScreen(index)} className="mr-2">
                                <Maximize2 size={20} className="text-white" />
                              </Button>
                              <Button variant="ghost" size="sm" onClick={() => handleVersionHistoryOpen({ url: image.url, versions: [image.url] })}>
                                <History size={20} className="text-white" />
                              </Button>
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                  <div className="mt-4 flex justify-between">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handlePageChange('prev')}
                      disabled={currentPage === 0}
                    >
                      <ChevronLeft size={20} />
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handlePageChange('next')}
                      disabled={(currentPage + 1) * imagesPerPage >= generatedImages.length}
                    >
                      <ChevronRight size={20} />
                    </Button>
                  </div>
                </div>
              ) : isGenerating ? (
                <div className="flex flex-col items-center justify-center h-full">
                  <RefreshCw className="w-12 h-12 text-blue-500 animate-spin mb-4" />
                  <p className="text-lg font-semibold">Generating your images...</p>
                  <p className="text-sm text-gray-600 mt-2">This may take a few moments</p>
                </div>
              ) : (
                <div>
                  <h3 className="text-lg font-semibold mb-4">Sample Prompts to Get Started</h3>
                  <div className="grid grid-cols-2 gap-4 mb-6">
                    {samplePrompts.map((prompt, index) => (
                      <div key={index} className="bg-gray-100 p-4 rounded-lg">
                        <Lightbulb className="w-6 h-6 text-blue-500 mb-2" />
                        <p className="text-sm text-gray-700">{prompt}</p>
                      </div>
                    ))}
                  </div>
                  <div className="bg-blue-50 p-4 rounded-lg">
                    <h4 className="text-md font-semibold mb-2">Benefits of Generating Images with qckfx</h4>
                    <ul className="space-y-2">
                      <li className="flex items-center">
                        <RefreshCw className="w-5 h-5 text-blue-500 mr-2" />
                        <span className="text-sm">Refine your images to perfection</span>
                      </li>
                      <li className="flex items-center">
                        <Target className="w-5 h-5 text-blue-500 mr-2" />
                        <span className="text-sm">State-of-the-art precision on labels and logos</span>
                      </li>
                      <li className="flex items-center">
                        <Infinity className="w-5 h-5 text-blue-500 mr-2" />
                        <span className="text-sm">Unlimited image generations and refinements</span>
                      </li>
                    </ul>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="bg-white p-4 rounded-lg shadow-lg">
              <Button variant="ghost" onClick={() => setIsVersionHistoryOpen(false)} className="mb-4">
                <ArrowLeft size={20} className="mr-2" /> Back to All Images
              </Button>
              <div className="flex items-center justify-center mb-4">
                <Button onClick={() => setCurrentVersion(Math.max(0, currentVersion - 1))} disabled={currentVersion === 0}>
                  <ChevronLeft size={20} />
                </Button>
                <div className="relative w-96 h-96 mx-4">
                  {selectedImage?.versions.map((version, index) => (
                    <img
                      key={index}
                      src={version}
                      alt={`Version ${index + 1}`}
                      className={`absolute top-0 left-0 w-full h-full object-cover transition-opacity duration-300 ${
                        index === currentVersion ? 'opacity-100' : 'opacity-0'
                      }`}
                    />
                  ))}
                </div>
                <Button 
                  onClick={() => setCurrentVersion(Math.min((selectedImage?.versions.length ?? 0) - 1, currentVersion + 1))} 
                  disabled={currentVersion === (selectedImage?.versions.length ?? 0) - 1}
                >
                  <ChevronRight size={20} />
                </Button>
              </div>
              <div className="flex items-center mb-4">
                <span className="mr-2">Version: {currentVersion + 1}</span>
                <Slider
                  value={[currentVersion]}
                  max={(selectedImage?.versions.length || 0) - 1}
                  step={1}
                  className="flex-grow"
                  onValueChange={handleVersionChange}
                />
                <span className="ml-2">of {selectedImage?.versions.length || 0}</span>
              </div>
              <div className="flex justify-between">
                <Button variant="outline" onClick={() => handleRefine(currentVersion)}>
                  <RefreshCw size={20} className="mr-2" /> Refine This Version
                </Button>
                <Button>Use This Version</Button>
              </div>
            </div>
          )}
        </div>
      </div>
      
      {/* Recent Images */}
      <h3 className="text-lg font-semibold mb-2">Recent Images</h3>
      <div className="flex space-x-2 overflow-x-auto pb-4">
        {product.additionalImageUrls.slice(0, 5).map((url, index) => (
          <img key={index} src={url} alt={`Recent ${index + 1}`} className="w-24 h-24 object-cover rounded-lg shadow-md" />
        ))}
      </div>

      {fullscreenImage !== null && (
        <div className="fixed inset-0 bg-black bg-opacity-90 z-50 flex items-center justify-center">
          <button 
            className="absolute top-4 right-4 text-white"
            onClick={handleCloseFullScreen}
          >
            <X size={24} />
          </button>
          <button 
            className="absolute left-4 top-1/2 transform -translate-y-1/2 text-white"
            onClick={() => handleNavigateFullScreen('prev')}
          >
            <ChevronLeft size={36} />
          </button>
          <img 
            src={generatedImages[fullscreenImage].url} 
            alt={`Fullscreen ${fullscreenImage + 1}`} 
            className="max-h-[90vh] max-w-[90vw] object-contain"
          />
          <button 
            className="absolute right-4 top-1/2 transform -translate-y-1/2 text-white"
            onClick={() => handleNavigateFullScreen('next')}
          >
            <ChevronRight size={36} />
          </button>
        </div>
      )}
    </div>
  );
};

export default ProductPage;
