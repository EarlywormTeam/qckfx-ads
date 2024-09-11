import React, { useState, useCallback, useRef, useEffect } from 'react';
import { useToast } from "@/components/ui/use-toast";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Slider } from "@/components/ui/slider";
import { useLocation } from 'react-router-dom';
import { Product } from '@/types/product';
import { useGenerateAPI } from '@/api/generate';
import { Trash2, RefreshCw, Maximize2, ChevronLeft, ChevronRight, Lightbulb, Infinity, Target, X, Loader2, ZoomIn, ZoomOut, Download } from 'lucide-react';
import { ImageGroup } from '@/types/generatedImage';
import { useProductAPI } from '@/api/product';
import { saveAs } from 'file-saver';

const ProductPage: React.FC = () => {
  const location = useLocation();
  const [product, /*setProduct*/] = useState<Product | null>(location.state?.product || null);
  const [loading, /*setLoading*/] = useState<boolean>(false);
  const [prompt, setPrompt] = useState<string>('');
  const [generatedImageGroups, setGeneratedImageGroups] = useState<ImageGroup[]>([]);
  const [recentImageGroups, setRecentImageGroups] = useState<ImageGroup[]>([]);
  const { toast } = useToast();
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const generateImageAPI = useGenerateAPI(); 
  const productAPI = useProductAPI();

  const [fullscreenGroup, setFullscreenGroup] = useState<ImageGroup | null>(null);
  const [currentVersion, setCurrentVersion] = useState(0);
  const [currentPage, setCurrentPage] = useState(0);
  const imagesPerPage = 4; // Keep this fixed at 4 images per page (2x2 grid)
  const gridRef = useRef<HTMLDivElement>(null);
  const [zoomLevel, setZoomLevel] = useState(1);
  const [dragStart, setDragStart] = useState<{ x: number; y: number } | null>(null);
  const [imagePosition, setImagePosition] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const imageRef = useRef<HTMLImageElement>(null);
  const [currentGroupIndex, setCurrentGroupIndex] = useState(0);

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
    // Add placeholder image groups
    setGeneratedImageGroups(prevGroups => [
      ...Array(4).fill({
        id: 'placeholder',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        images: [{ url: '', created_at: new Date().toISOString() }]
      }),
      ...prevGroups
    ]);

    try {
      const generationJobId = await generateImageAPI.generateProductImage(product!.id, prompt, 4);
      const result = await generateImageAPI.pollGenerationJob(generationJobId);

      if (result.generationJob.status === 'completed' && result.imageGroups) {
        setGeneratedImageGroups(prevGroups => [
          ...result.imageGroups!,
          ...prevGroups.filter(group => group.id !== 'placeholder')
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
      // Remove placeholder image groups on error
      setGeneratedImageGroups(prevGroups => prevGroups.filter(group => group.id !== 'placeholder'));
    } finally {
      setIsGenerating(false);
    }
  }, [product, prompt, toast, generateImageAPI]);

  const handleDelete = useCallback(async (groupId: string) => {
    try {
      await productAPI.deleteImageGroup(product!.id, groupId);
      setGeneratedImageGroups(prevGroups => prevGroups.filter(group => group.id !== groupId));
      setRecentImageGroups(prevGroups => prevGroups.filter(group => group.id !== groupId));
    } catch (error) {
      console.error('Error deleting image group:', error);
      toast({
        title: "Error",
        description: "Failed to delete image group. Please try again.",
        variant: "destructive",
      });
    }
  }, [product, productAPI, toast]);

  const handleRefine = useCallback(async (group: ImageGroup) => {
    const currentImage = group.images[currentVersion];
    setIsGenerating(true);

    try {
      const result = await generateImageAPI.refineImage(
        group.id,
        currentImage.id,
        prompt,
      );

      // Poll for the refined image
      const refinedResult = await generateImageAPI.pollGenerationJob(result.generationJobId);

      if (refinedResult.generationJob.status === 'completed' && refinedResult.imageGroups) {
        const updatedGroup = refinedResult.imageGroups![0];
        setGeneratedImageGroups(prevGroups => 
          prevGroups.map(prevGroup => 
            prevGroup.id === group.id ? updatedGroup : prevGroup
          )
        );
        
        // Update fullscreenGroup if it's currently being viewed
        if (fullscreenGroup && fullscreenGroup.id === group.id) {
          setFullscreenGroup(updatedGroup);
          setCurrentVersion(updatedGroup.images.length - 1);
        }
      } else {
        throw new Error('Image refinement failed');
      }
    } catch (error) {
      console.error('Error refining image:', error);
      toast({
        title: "Error",
        description: "Failed to refine image. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsGenerating(false);
    }
  }, [generateImageAPI, toast, fullscreenGroup, currentVersion, prompt]);

  const handleFullScreenVersions = (group: ImageGroup, index: number) => {
    setFullscreenGroup(group);
    setCurrentVersion(group.images.length - 1);
    setCurrentGroupIndex(index);
  };

  const handleCloseFullScreen = () => {
    setFullscreenGroup(null);
    setCurrentVersion(0);
    setCurrentGroupIndex(0);
  };

  const handleVersionChange = (value: number[]) => {
    setCurrentVersion(value[0]);
  };

  const handlePageChange = useCallback((direction: 'prev' | 'next') => {
    const newPage = direction === 'prev' ? Math.max(0, currentPage - 0.5) : currentPage + 0.5;
    setCurrentPage(newPage);
    
    if (gridRef.current) {
      const scrollWidth = gridRef.current.clientWidth;
      gridRef.current.scrollTo({
        left: newPage * scrollWidth,
        behavior: 'smooth'
      });
    }
  }, [currentPage]);

  const handleZoom = (direction: 'in' | 'out') => {
    setZoomLevel(prevZoom => {
      if (direction === 'in') return Math.min(prevZoom + 0.25, 3);
      return Math.max(prevZoom - 0.25, 1);
    });
  };

  const handleMouseDown = (e: React.MouseEvent<HTMLImageElement>) => {
    e.preventDefault(); // Add this line to prevent default behavior
    setDragStart({ x: e.clientX - imagePosition.x, y: e.clientY - imagePosition.y });
  };

  const handleMouseMove = useCallback((e: MouseEvent) => {
    if (dragStart && zoomLevel > 1) {
      const newX = e.clientX - dragStart.x;
      const newY = e.clientY - dragStart.y;
      setImagePosition({ x: newX, y: newY });
    }
  }, [dragStart, zoomLevel]);

  const handleMouseUp = () => {
    setDragStart(null);
  };

  const handleFullScreenClick = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget) {
      handleCloseFullScreen();
    }
  }, []);

  const handleFullScreenNavigation = (direction: 'prev' | 'next') => {
    const newIndex = direction === 'prev' 
      ? Math.max(0, currentGroupIndex - 1)
      : Math.min(generatedImageGroups.length - 1, currentGroupIndex + 1);
    
    setCurrentGroupIndex(newIndex);
    setFullscreenGroup(generatedImageGroups[newIndex]);
    setCurrentVersion(generatedImageGroups[newIndex].images.length - 1);
  };

  const handleDownload = useCallback(async (imageId: string, filename: string) => {
    try {
      const blob = await productAPI.downloadImage(imageId);
      saveAs(blob, filename);
    } catch (error) {
      console.error('Error downloading image:', error);
      toast({
        title: "Error",
        description: "Failed to download image. Please try again.",
        variant: "destructive",
      });
    }
  }, [productAPI, toast]);

  useEffect(() => {
    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);
    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, [handleMouseMove]);

  useEffect(() => {
    if (zoomLevel === 1) {
      setImagePosition({ x: 0, y: 0 });
    }
  }, [zoomLevel]);

  // useEffect(() => {
  //   if (product) {
  //     setLoading(true);
  //     productAPI.getProductImageGroups(product.id)
  //       .then((groups: ImageGroup[]) => {
  //         setRecentImageGroups(groups);
  //         setLoading(false);
  //       })
  //       .catch((error: Error) => {
  //         console.error('Error fetching image groups:', error);
  //         toast({
  //           title: "Error",
  //           description: "Failed to fetch image groups. Please try again.",
  //           variant: "destructive",
  //         });
  //         setLoading(false);
  //       });
  //   }
  // }, [product, productAPI, toast]);

  if (loading) return <div className="p-8">Loading...</div>;
  if (!product) return <div className="p-8">Product not found</div>;

  const samplePrompts = [
    "A woman on the beach holding a can of Calm Crunchy sparkling water.",
    "A can of Calm Crunchy sparkling water at a picnic.",
    "A can of Calm Crunchy sparkling water on a table with a plant.",
    "A can of Calm Crunchy sparkling water on an iceberg floating in the ocean."
  ];

  const getMostRecentImage = (group: ImageGroup) => {
    return group.images.reduce((latest, current) => 
      new Date(current.createdAt) > new Date(latest.createdAt) ? current : latest
    );
  };

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
          <div>
            {generatedImageGroups.length > 0 ? (
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
                  {generatedImageGroups.map((group, index) => (
                    <div 
                      key={index} 
                      className="aspect-square w-[300px] h-[300px] scroll-snap-align-start"
                    >
                      {group.id === 'placeholder' ? (
                        <div className="w-full h-full bg-gradient-to-br from-gray-200 to-gray-300 rounded-lg flex items-center justify-center">
                          <Loader2 className="w-8 h-8 text-gray-400 animate-spin" />
                        </div>
                      ) : (
                        <div className="relative group w-full h-full">
                          <img 
                            src={getMostRecentImage(group).url} 
                            alt={`Generated ${index + 1}`} 
                            className="w-full h-full object-contain rounded-lg shadow-md"
                          />
                          <div className="absolute inset-0 bg-black bg-opacity-50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center rounded-lg">
                            <Button variant="ghost" size="sm" onClick={() => handleDelete(group.id)} className="mr-2">
                              <Trash2 size={20} className="text-white" />
                            </Button>
                            <Button variant="ghost" size="sm" onClick={() => handleRefine(group)} className="mr-2">
                              <RefreshCw size={20} className="text-white" />
                            </Button>
                            <Button variant="ghost" size="sm" onClick={() => handleFullScreenVersions(group, index)} className="mr-2">
                              <Maximize2 size={20} className="text-white" />
                            </Button>
                            <Button variant="ghost" size="sm" onClick={() => handleDownload(getMostRecentImage(group).id, `image_${group.id}.jpg`)}>
                              <Download size={20} className="text-white" />
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
                    disabled={(currentPage + 1) * imagesPerPage >= generatedImageGroups.length}
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
        </div>
      </div>
      
      {/* Recent Images */}
      <h3 className="text-lg font-semibold mb-2">Recent Images</h3>
      <div className="flex space-x-2 overflow-x-auto pb-4">
        {recentImageGroups.slice(0, 5).map((group) => {
          const mostRecentImage = getMostRecentImage(group);
          return (
            <img 
              key={group.id} 
              src={mostRecentImage.url} 
              alt={`Recent ${group.id}`} 
              className="w-24 h-24 object-cover rounded-lg shadow-md cursor-pointer"
              onClick={() => handleFullScreenVersions(group, recentImageGroups.indexOf(group))}
            />
          );
        })}
      </div>

      {/* Full-screen version history */}
      {fullscreenGroup && (
        <div 
          className="fixed inset-0 bg-background-black bg-opacity-90 z-50 flex items-center justify-center"
          onClick={handleFullScreenClick}
        >
          <div className="max-w-4xl w-full" onClick={(e) => e.stopPropagation()}>
            <Button 
              variant="ghost" 
              onClick={handleCloseFullScreen} 
              className="absolute top-4 right-4 text-text-white hover:bg-background-dark/20"
            >
              <X size={24} />
            </Button>
            <div className="flex items-center justify-center mb-4">
              <Button 
                onClick={() => handleFullScreenNavigation('prev')} 
                disabled={currentGroupIndex === 0}
                className="text-text-black bg-background-white hover:bg-background-accent/20"
              >
                <ChevronLeft size={20} />
              </Button>
              <div className="relative w-[80vw] h-[80vh] mx-4 overflow-hidden">
                {fullscreenGroup.images.map((image, index) => (
                  <img
                    key={index}
                    ref={index === currentVersion ? imageRef : null}
                    src={image.url}
                    alt={`Version ${index + 1}`}
                    className={`absolute top-0 left-0 w-full h-full object-contain transition-opacity duration-300 ${
                      index === currentVersion ? 'opacity-100' : 'opacity-0'
                    }`}
                    style={{
                      transform: `scale(${zoomLevel}) translate(${imagePosition.x}px, ${imagePosition.y}px)`,
                      transformOrigin: 'center',
                      transition: 'transform 0.3s ease-out',
                      cursor: zoomLevel > 1 ? 'move' : 'default',
                    }}
                    onMouseDown={handleMouseDown}
                    draggable="false"
                  />
                ))}
              </div>
              <Button 
                onClick={() => handleFullScreenNavigation('next')} 
                disabled={currentGroupIndex === generatedImageGroups.length - 1}
                className="text-text-black bg-background-white hover:bg-background-accent/20"
              >
                <ChevronRight size={20} />
              </Button>
            </div>
            <div className="flex flex-col space-y-4 text-text-white">
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <span className="mr-2">Version: {currentVersion + 1}</span>
                  <Slider
                    value={[currentVersion]}
                    max={fullscreenGroup.images.length - 1}
                    step={1}
                    className="w-48"
                    onValueChange={handleVersionChange}
                  />
                  <span className="ml-2">of {fullscreenGroup.images.length}</span>
                </div>
                <div className="flex items-center">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleZoom('out')}
                    disabled={zoomLevel === 1}
                    className="mr-2 text-text-white border-text-white bg-background-dark/50 hover:bg-background-dark/70"
                  >
                    <ZoomOut size={20} />
                  </Button>
                  <span className="mx-2">{Math.round(zoomLevel * 100)}%</span>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleZoom('in')}
                    disabled={zoomLevel === 3}
                    className="ml-2 text-text-white border-text-white bg-background-dark/50 hover:bg-background-dark/70"
                  >
                    <ZoomIn size={20} />
                  </Button>
                </div>
              </div>
              
              <div className="flex justify-between">
                <Button 
                  variant="outline" 
                  onClick={() => handleDownload(fullscreenGroup.images[currentVersion].id, `image_${fullscreenGroup.id}_v${currentVersion + 1}.jpg`)}
                  className="text-text-white border-text-white bg-background-dark/50 hover:bg-background-dark/70"
                >
                  <Download size={20} className="mr-2" /> Download This Version
                </Button>
                <Button 
                  variant="outline" 
                  onClick={() => handleRefine(fullscreenGroup)}
                  className="text-text-white border-text-white bg-background-dark/50 hover:bg-background-dark/70"
                  disabled={isGenerating}
                >
                  {isGenerating ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <RefreshCw size={20} className="mr-2" />}
                  {isGenerating ? 'Refining...' : 'Refine'}
                </Button>
                <Button className="bg-background-action text-text-black hover:bg-background-action/80">Use This Version</Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProductPage;
