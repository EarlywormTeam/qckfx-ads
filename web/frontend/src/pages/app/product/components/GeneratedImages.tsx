import React from 'react';
import { GeneratedImage, ImageGroup } from '@/types/generatedImage';
import { Button } from "@/components/ui/button";
import { Trash2, RefreshCw, Maximize2, Download, Loader2, XCircle, ChevronLeft, ChevronRight, Lightbulb, Target, Infinity } from 'lucide-react';

interface GeneratedImagesProps {
  generatedImageGroups: ImageGroup[];
  gridRef: React.RefObject<HTMLDivElement>;
  handleDelete: (groupId: string) => void;
  handleRefine: (group: ImageGroup) => void;
  handleFullScreenVersions: (group: ImageGroup, index: number) => void;
  handleDownload: (imageId: string, filename: string) => void;
  refiningGroupIds: string[];
  refiningErrorGroupIds: string[];
  currentPage: number;
  imagesPerPage: number;
  handlePageChange: (direction: 'prev' | 'next') => void;
  showPaginationTutorial: boolean;
  handleDismissTutorial: () => void;
  isGenerating: boolean;
}

const GeneratedImages: React.FC<GeneratedImagesProps> = ({
  generatedImageGroups,
  gridRef,
  handleDelete,
  handleRefine,
  handleFullScreenVersions,
  handleDownload,
  refiningGroupIds,
  refiningErrorGroupIds,
  currentPage,
  imagesPerPage,
  handlePageChange,
  showPaginationTutorial,
  handleDismissTutorial,
  isGenerating,
}) => {
    const getMostRecentImage = (group: ImageGroup): GeneratedImage | undefined => {
        return group.images
            .filter(image => image.url && image.status === "generated")
            .reduce<GeneratedImage | undefined>((latest, current) => 
            !latest || new Date(current.createdAt) > new Date(latest.createdAt) ? current : latest
            , undefined);
    };

  const getDefaultImage = (group: ImageGroup) => {
    return group.images
      .filter(image => image.url && image.status === "generated" && image.id === group.defaultImageId)[0];
  };

  const samplePrompts = [
    "A woman on the beach holding a can of Calm Crunchy sparkling water.",
    "A can of Calm Crunchy sparkling water at a picnic.",
    "A can of Calm Crunchy sparkling water on a table with a plant.",
    "A can of Calm Crunchy sparkling water on an iceberg floating in the ocean."
  ];

  if (generatedImageGroups.length === 0 && !isGenerating) {
    return (
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
    );
  }

  if (isGenerating && generatedImageGroups.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full">
        <RefreshCw className="w-12 h-12 text-blue-500 animate-spin mb-4" />
        <p className="text-lg font-semibold">Generating your images...</p>
        <p className="text-sm text-gray-600 mt-2">This may take a few moments</p>
      </div>
    );
  }

  return (
    <div className="w-2/3">
      <div className="relative">
        <div 
          ref={gridRef}
          className="grid gap-4 mb-4 overflow-hidden"
          style={{ 
            gridTemplateRows: 'repeat(2, 1fr)',
            gridAutoFlow: 'column',
            gridAutoColumns: 'min-content',
            maxWidth: 'calc(600px + 1rem)',
            maxHeight: 'calc(600px + 1rem)',
            margin: '0 auto',
            scrollSnapType: 'x mandatory'
          }}
        >
          {generatedImageGroups.map((group, index) => (
            <div 
              key={index} 
              className="aspect-square w-[300px] h-[300px] scroll-snap-align-start"
            >
              {group.images.length === 0 ? (
                <div className="w-full h-full bg-gradient-to-br from-gray-200 to-gray-300 rounded-lg flex items-center justify-center">
                  <Loader2 className="w-8 h-8 text-gray-400 animate-spin" />
                </div>
              ) : group.images[0].status === 'pending' ? (
                <div className="w-full h-full bg-gradient-to-br from-gray-200 to-gray-300 rounded-lg flex items-center justify-center">
                  <Loader2 className="w-8 h-8 text-gray-400 animate-spin" />
                </div>
              ) : group.images[0].status === 'generated' ? (
                <div className="relative group w-full h-full">
                  <img 
                    src={group.defaultImageId ? getDefaultImage(group)?.url ?? '' : getMostRecentImage(group)?.url ?? ''} 
                    alt={`Generated ${index + 1}`} 
                    className="w-full h-full object-contain rounded-lg shadow-md"
                  />

                  {refiningGroupIds.includes(group.id) && (
                    <div className="absolute top-2 right-2">
                      <Loader2 className="w-6 h-6 text-white animate-spin" />
                    </div>
                  )}
                  {refiningErrorGroupIds.includes(group.id) && (
                    <div className="absolute top-2 right-2">
                      <XCircle className="w-6 h-6 text-red-500" />
                    </div>
                  )}

                  <div className="absolute inset-0 bg-black bg-opacity-50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center rounded-lg">
                    <Button variant="ghost" size="sm" onClick={() => handleDelete(group.id)} className="mr-2 hover:bg-gray-400">
                      <Trash2 size={20} className="text-white hover:text-black" />
                    </Button>
                    <Button variant="ghost" size="sm" onClick={() => handleRefine(group)} className="mr-2 hover:bg-gray-400">
                      <RefreshCw size={20} className="text-white hover:text-black" />
                    </Button>
                    <Button variant="ghost" size="sm" onClick={() => handleFullScreenVersions(group, index)} className="mr-2 hover:bg-gray-400">
                      <Maximize2 size={20} className="text-white hover:text-black" />
                    </Button>
                    <Button variant="ghost" size="sm" onClick={() => handleDownload(group.defaultImageId ? getDefaultImage(group)?.id ?? '' : getMostRecentImage(group)?.id ?? '', `image_${group.id}.jpg`)} className="mr-2 hover:bg-gray-400">
                      <Download size={20} className="text-white hover:text-black" />
                    </Button>
                  </div>
                </div>
              ) : (
                <div className="relative w-full h-full bg-red-100 rounded-lg flex flex-col items-center justify-center">
                  <XCircle className="w-8 h-8 text-red-500 mb-2" />
                  <span className="text-red-500 mb-2">Generation failed</span>
                  <Button variant="ghost" size="sm" onClick={() => handleDelete(group.id)} className="mt-2">
                    <Trash2 size={20} className="text-red-500" />
                  </Button>
                </div>
              )}
            </div>
          ))}
        </div>
        <div className="mt-4 flex justify-between items-center relative">
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

          {showPaginationTutorial && (
            <div className="absolute right-0 top-full mt-2 bg-white p-3 rounded-lg shadow-lg z-10 w-64">
              <div className="absolute -top-2 right-4 w-0 h-0 border-l-8 border-r-8 border-b-8 border-l-transparent border-r-transparent border-b-white"></div>
              <p className="text-sm mb-2">
                Click this arrow to see more generated images.
              </p>
              <Button size="sm" onClick={handleDismissTutorial} className="w-full">
                Got it!
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default GeneratedImages;