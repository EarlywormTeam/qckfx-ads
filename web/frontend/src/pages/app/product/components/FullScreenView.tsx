import React from 'react';
import { ImageGroup } from '@/types/generatedImage';
import { Button } from "@/components/ui/button";
import { X, ChevronLeft, ChevronRight, Loader2, XCircle, Download, RefreshCw, ZoomIn, ZoomOut } from 'lucide-react';
import { Slider } from "@/components/ui/slider";

interface FullScreenViewProps {
  fullscreenGroup: ImageGroup;
  currentVersion: number;
  currentGroupIndex: number;
  totalGroups: number;
  zoomLevel: number;
  imagePosition: { x: number; y: number };
  handleCloseFullScreen: () => void;
  handleFullScreenNavigation: (direction: 'prev' | 'next') => void;
  handleVersionChange: (value: number[]) => void;
  handleZoom: (direction: 'in' | 'out') => void;
  handleMouseDown: (e: React.MouseEvent<HTMLImageElement>) => void;
  handleDownload: (imageId: string, filename: string) => void;
  handleRefine: (group: ImageGroup) => void;
  handleSetDefaultImage: () => void;
  refiningGroupIds: string[];
  refiningErrorGroupIds: string[];
}

const FullScreenView: React.FC<FullScreenViewProps> = ({
  fullscreenGroup,
  currentVersion,
  currentGroupIndex,
  totalGroups,
  zoomLevel,
  imagePosition,
  handleCloseFullScreen,
  handleFullScreenNavigation,
  handleVersionChange,
  handleZoom,
  handleMouseDown,
  handleDownload,
  handleRefine,
  handleSetDefaultImage,
  refiningGroupIds,
  refiningErrorGroupIds,
}) => {
  return (
    <div 
      className="fixed inset-0 bg-background-black bg-opacity-90 z-50 flex items-center justify-center"
      onClick={handleCloseFullScreen}
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
                src={image.url ?? ''}
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
            {refiningGroupIds.includes(fullscreenGroup.id) && (
              <div className="absolute top-4 right-20">
                <Loader2 className="w-6 h-6 text-white animate-spin" />
              </div>
            )}
            {refiningErrorGroupIds.includes(fullscreenGroup.id) && (
              <div className="absolute top-2 right-20">
                <XCircle className="w-6 h-6 text-red-500" />
              </div>
            )}
          </div>
          <Button 
            onClick={() => handleFullScreenNavigation('next')} 
            disabled={currentGroupIndex === totalGroups - 1}
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
              disabled={refiningGroupIds.includes(fullscreenGroup.id)}
            >
              {refiningGroupIds.includes(fullscreenGroup.id) ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <RefreshCw size={20} className="mr-2" />}
              {refiningGroupIds.includes(fullscreenGroup.id) ? 'Refining...' : 'Refine'}
            </Button>
            <Button 
              className="bg-background-action text-text-black hover:bg-background-action/80"
              onClick={handleSetDefaultImage}
            >
              Use This Version
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FullScreenView;