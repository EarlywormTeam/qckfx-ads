import { Image } from "@/types/image"
import { useState } from 'react'
import { Expand } from 'lucide-react'
import { cn } from "@/lib/utils"

interface ImageCardProps {
  image: Image
  onClick: (image: Image) => void
}

export default function ImageCard({ image, onClick }: ImageCardProps) {
  const [isHovered, setIsHovered] = useState(false)

  const getSourceDisplay = (source: string | undefined) => {
    if (!source) return null
    return source.charAt(0).toUpperCase() + source.slice(1)
  }

  return (
    // Prevent breaking inside columns and add margin
    <div
      className="mb-4 break-inside-avoid"
      onClick={() => onClick(image)}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <div 
        className="relative w-full overflow-hidden rounded-lg shadow-md transition-transform duration-300 ease-in-out hover:scale-105 hover:shadow-lg"
        style={{ paddingBottom: `${(1 / image.dimensions.aspectRatio) * 100}%` }}
      >
        <div className="absolute inset-0">
          <img
            src={image.url}
            alt={image.caption}
            className="h-full w-full object-cover"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent opacity-0 transition-opacity duration-300 ease-in-out group-hover:opacity-100" />
          <div className="absolute bottom-2 left-2 text-sm font-medium text-white">
            "Anonymous"
            {/* {creator} */}
          </div>
          {image.creationMethod === 'upload' && (
            <div className={cn(
              "absolute top-2 right-2 rounded px-2 py-1 text-xs font-medium",
              image.creationMethod === 'upload' ? 'bg-gray-200 text-gray-800' : 'bg-blue-500 text-white'
            )}>
              {getSourceDisplay(image.creationMethod)}
            </div>
          )}
          {isHovered && (
            <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-40 transition-opacity duration-300 ease-in-out">
              <Expand className="h-12 w-12 text-white opacity-75" />
            </div>
          )}
        </div>
      </div>
    </div>
  )
}