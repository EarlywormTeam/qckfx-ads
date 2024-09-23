import React from 'react';
import { ImageGroup } from '@/types/generatedImage';

interface RecentImagesProps {
  recentImageGroups: ImageGroup[];
  handleFullScreenVersions: (group: ImageGroup, index: number) => void;
}

const RecentImages: React.FC<RecentImagesProps> = ({ recentImageGroups, handleFullScreenVersions }) => {
  const getMostRecentImage = (group: ImageGroup) => {
    return group.images
      .filter(image => image.url && image.status === "generated")
      .reduce((latest, current) => 
        !latest || new Date(current.createdAt) > new Date(latest.createdAt) ? current : latest
      , { id: '', createdAt: '', status: 'generated', url: '' });
  };

  return (
    <div>
      <h3 className="text-lg font-semibold mb-2">Recent Images</h3>
      <div className="flex space-x-2 overflow-x-auto pb-4">
        {recentImageGroups.slice(0, 5).map((group) => {
          const mostRecentImage = getMostRecentImage(group);
          return (
            <img 
              key={group.id} 
              src={mostRecentImage?.url ?? ''} 
              alt={`Recent ${group.id}`} 
              className="w-24 h-24 object-cover rounded-lg shadow-md cursor-pointer"
              onClick={() => handleFullScreenVersions(group, recentImageGroups.indexOf(group))}
            />
          );
        })}
      </div>
    </div>
  );
};

export default RecentImages;