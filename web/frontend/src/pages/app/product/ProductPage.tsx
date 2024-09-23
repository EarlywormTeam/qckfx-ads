import React, { useState, useCallback, useRef, useEffect } from 'react';
import { useToast } from "@/components/ui/use-toast";
import { useLocation } from 'react-router-dom';
import { Product } from '@/types/product';
import { useGenerateAPI } from '@/api/generate';
import { GeneratedImage, ImageGroup } from '@/types/generatedImage';
import { useProductAPI } from '@/api/product';

import ProductDetails from './components/ProductDetails';
import GeneratedImages from './components/GeneratedImages';
import RecentImages from './components/RecentImages';
import FullScreenView from './components/FullScreenView';
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
  // const imageRef = useRef<HTMLImageElement>(null);
  const [currentGroupIndex, setCurrentGroupIndex] = useState(0);
  const [refiningGroupIds, setRefiningGroupIds] = useState<string[]>([]);
  const [refiningErrorGroupIds, setRefiningErrorGroupIds] = useState<string[]>([]);
  const [showPaginationTutorial, setShowPaginationTutorial] = useState(false);

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
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        images: [{ id: 'placeholder', url: null, createdAt: new Date().toISOString(), status: 'pending' }]
      } as ImageGroup),
      ...prevGroups
    ]);

    try {
      const generationJobId = await generateImageAPI.generateProductImage(product!.id, prompt, 4);
      const generator = generateImageAPI.pollGenerationJob(generationJobId);

      for await (const result of generator) {
        if (result.imageGroups) {
          setGeneratedImageGroups(prevGroups => {
            const newGroups = [...prevGroups];
            result.imageGroups!.forEach(group => {
              const existingIndex = newGroups.findIndex(g => g.id === group.id);
              if (existingIndex !== -1) {
                newGroups[existingIndex] = group as ImageGroup;
              } else {
                newGroups.unshift(group as ImageGroup);
              }
            });
            return newGroups.filter(group => group.id !== 'placeholder');
          });
        }

        if (result.generationJob.status === 'completed') {
          break;
        }
      }
    } catch (error) {
      console.error('Error generating images:', error);
      toast({
        title: "Error",
        description: "Failed to generate images. Please try again.",
        variant: "destructive",
      });
      // Remove placeholder image groups on error
      setGeneratedImageGroups(prevGroups => prevGroups.filter(group => 
        group.id !== 'placeholder' && group.images.some(image => image.status !== 'pending')
      ));
    } finally {
      setIsGenerating(false);
      // Remove any remaining placeholder groups
      setGeneratedImageGroups(prevGroups => prevGroups.filter(group => 
        group.id !== 'placeholder' && group.images.some(image => image.status !== 'pending')
      ));
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
    setRefiningGroupIds([...refiningGroupIds, group.id]);
    setRefiningErrorGroupIds(prevIds => prevIds.filter(id => id !== group.id));

    try {
      const result = await generateImageAPI.refineImage(
        group.id,
        currentImage.id,
        group.prompt,
      );

      // Poll for the refined image
      for await (const refinedResult of generateImageAPI.pollGenerationJob(result.generationJobId)) {
        if (refinedResult.generationJob.status === 'completed' && refinedResult.imageGroups) {
          const updatedGroup = refinedResult.imageGroups[0] as ImageGroup;
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
          break;
        } else if (refinedResult.generationJob.status === 'error') {
          throw new Error('Image refinement failed');
        }
      }
    } catch (error) {
      console.error('Error refining image:', error);
      toast({
        title: "Error",
        description: "Failed to refine image. Please try again.",
        variant: "destructive",
      });
      setRefiningErrorGroupIds([...refiningErrorGroupIds, group.id]);
    } finally {
      setRefiningGroupIds(prevIds => prevIds.filter(id => id !== group.id));
    }
  }, [generateImageAPI, toast, fullscreenGroup, currentVersion, prompt]);

  const handleFullScreenVersions = (group: ImageGroup, index: number) => {
    setFullscreenGroup(group);
    let currentVersionIndex = group.images.length - 1
    let defaultImage = getDefaultImage(group);
    if (defaultImage) {
      currentVersionIndex = group.images.indexOf(defaultImage);
    }
    setCurrentVersion(currentVersionIndex);
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

  // const handleFullScreenClick = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
  //   if (e.target === e.currentTarget) {
  //     handleCloseFullScreen();
  //   }
  // }, []);

  const handleFullScreenNavigation = (direction: 'prev' | 'next') => {
    const newIndex = direction === 'prev' 
      ? Math.max(0, currentGroupIndex - 1)
      : Math.min(generatedImageGroups.length - 1, currentGroupIndex + 1);
    
    setCurrentGroupIndex(newIndex);
    setFullscreenGroup(generatedImageGroups[newIndex]);
    let currentVersionIndex = generatedImageGroups[newIndex].images.length - 1
    let defaultImage = getDefaultImage(generatedImageGroups[newIndex]);
    if (defaultImage) {
      currentVersionIndex = generatedImageGroups[newIndex].images.indexOf(defaultImage);
    }
    setCurrentVersion(currentVersionIndex);
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

  const handleSetDefaultImage = useCallback(async () => {
    if (fullscreenGroup && fullscreenGroup.images[currentVersion]) {
      try {
        await productAPI.setDefaultImage(fullscreenGroup.id, fullscreenGroup.images[currentVersion].id);
        toast({
          title: "Success",
          description: "Default image set successfully",
        });
        // Optionally, update the local state to reflect the change
        setGeneratedImageGroups(prevGroups => 
          prevGroups.map(group => 
            group.id === fullscreenGroup.id 
              ? {...group, defaultImageId: fullscreenGroup.images[currentVersion].id} 
              : group
          )
        );
      } catch (error) {
        console.error('Error setting default image:', error);
        toast({
          title: "Error",
          description: "Failed to set default image. Please try again.",
          variant: "destructive",
        });
      }
    }
  }, [fullscreenGroup, currentVersion, productAPI, toast]);

  const handleDismissTutorial = () => {
    setShowPaginationTutorial(false);
    localStorage.setItem('hasSeenPaginationTutorial', 'true');
  };

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

  useEffect(() => {
    const hasSeenTutorial = localStorage.getItem('hasSeenPaginationTutorial');
    if (!hasSeenTutorial && generatedImageGroups.length > 4) {
      setShowPaginationTutorial(true);
    }
  }, [generatedImageGroups]);

  useEffect(() => {
    if (!fullscreenGroup) {
      return;
    }
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'ArrowLeft') {
        // Simulate clicking the previous page button (ChevronLeft)
        handleFullScreenNavigation('prev');
      } else if (event.key === 'ArrowRight') {
        // Simulate clicking the next page button (ChevronRight)
        handleFullScreenNavigation('next');
      }
    };

    // Attach event listener for keydown
    window.addEventListener('keydown', handleKeyDown);

    // Clean up event listener on unmount
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [fullscreenGroup, handleFullScreenNavigation, generatedImageGroups]);

  if (loading) return <div className="p-8">Loading...</div>;
  if (!product) return <div className="p-8">Product not found</div>;

  const getDefaultImage = (group: ImageGroup): GeneratedImage | undefined => {
    return group.images
    .filter(image => image.url && image.status === "generated" && image.id === group.defaultImageId)[0];
  }

  return (
    <div className="p-4 max-w-6xl mx-auto">
      <div className="flex items-start mb-4">
        <ProductDetails
          product={product!}
          prompt={prompt}
          setPrompt={setPrompt}
          handleGenerateImages={handleGenerateImages}
          isGenerating={isGenerating}
        />
        
        <GeneratedImages
          generatedImageGroups={generatedImageGroups}
          gridRef={gridRef}
          handleDelete={handleDelete}
          handleRefine={handleRefine}
          handleFullScreenVersions={handleFullScreenVersions}
          handleDownload={handleDownload}
          refiningGroupIds={refiningGroupIds}
          refiningErrorGroupIds={refiningErrorGroupIds}
          currentPage={currentPage}
          imagesPerPage={imagesPerPage}
          handlePageChange={handlePageChange}
          showPaginationTutorial={showPaginationTutorial}
          handleDismissTutorial={handleDismissTutorial}
          isGenerating={isGenerating}
        />
      </div>
      
      <RecentImages
        recentImageGroups={recentImageGroups}
        handleFullScreenVersions={handleFullScreenVersions}
      />

      {fullscreenGroup && (
        <FullScreenView
          fullscreenGroup={fullscreenGroup}
          currentVersion={currentVersion}
          currentGroupIndex={currentGroupIndex}
          totalGroups={generatedImageGroups.length}
          zoomLevel={zoomLevel}
          imagePosition={imagePosition}
          handleCloseFullScreen={handleCloseFullScreen}
          handleFullScreenNavigation={handleFullScreenNavigation}
          handleVersionChange={handleVersionChange}
          handleZoom={handleZoom}
          handleMouseDown={handleMouseDown}
          handleDownload={handleDownload}
          handleRefine={handleRefine}
          handleSetDefaultImage={handleSetDefaultImage}
          refiningGroupIds={refiningGroupIds}
          refiningErrorGroupIds={refiningErrorGroupIds}
        />
      )}
    </div>
  );
};

export default ProductPage;
