import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Slider } from "@/components/ui/slider"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Download, Upload, Wand2, X } from 'lucide-react'
import { Image } from "@/types/image"
import { useAssetAPI } from "@/api/asset"

export default function ImageEditor() {
  const { imageId } = useParams<{ imageId: string }>()
  const navigate = useNavigate()
  const api = useAssetAPI()
  const [image, setImage] = useState<Image | null>(null)
  const [version, setVersion] = useState(1)
  const [whatToChange, setWhatToChange] = useState('')
  const [howToChange, setHowToChange] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!imageId) {
      setError("No image ID provided.")
      setLoading(false)
      return
    }

    const fetchImage = async () => {
      try {
        const fetchedImage = await api.getImageById(imageId)
        setImage(fetchedImage)
      } catch (err: unknown) {
        console.error("Failed to fetch image:", err)
        setError("Failed to load image.")
      } finally {
        setLoading(false)
      }
    }

    fetchImage()
  }, [api, imageId])

  const handleVersionChange = (newVersion: number[]) => {
    setVersion(newVersion[0])
  }

  const handleDownload = () => {
    if (!image?.url) return
    const link = document.createElement('a')
    link.href = image.url
    link.download = `${image.id}.${image.format || 'png'}`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  const handleGenerate = () => {
    console.log('Generating new version...')
    // Implement generate functionality
  }

  const handleClose = () => {
    navigate(-1) // Navigates back to the previous page
  }

  if (loading) {
    return <div>Loading image editor...</div>
  }

  if (error) {
    return <div className="text-red-500">{error}</div>
  }

  if (!image) {
    return <div>No image data available.</div>
  }

  return (
    <div className="relative flex h-full bg-background text-foreground px-4 md:px-6 pt-2">
      {/* X Button */}
      <button
        onClick={handleClose}
        className="absolute top-4 right-4 text-gray-500 hover:text-gray-700 focus:outline-none z-10"
        aria-label="Close"
      >
        <X className="w-6 h-6" />
      </button>

      {/* Left Side: Image and Controls */}
      <div className="w-2/3 pr-6 h-full min-h-0 grid grid-rows-[1fr_auto]">
        {/* Image Container */}
        <div className="bg-muted rounded-lg overflow-hidden max-h-full max-w-full flex items-center justify-center">
          <img
            src={image?.url || "/placeholder.svg?height=800&width=1200"}
            alt="Large preview image"
            className="max-w-full max-h-full object-contain"
          />
        </div>

        {/* Controls: Slider and Download Button */}
        <div className="mt-4 px-2 flex items-center space-x-4 md:space-x-8 lg:space-x-12 h-16 flex-shrink-0">
          {/* Version Slider */}
          <div className="flex-grow flex flex-col justify-center">
            <Slider
              value={[version]}
              min={1}
              max={10}
              step={1}
              onValueChange={handleVersionChange}
            />
            <p className="text-center mt-1 text-sm">Version: {version}</p>
          </div>
          
          {/* Download Button */}
          <Button onClick={handleDownload} className="whitespace-nowrap flex items-center space-x-2">
            <Download className="h-4 w-4" />
            <span>Download Image</span>
          </Button>
        </div>
      </div>

      {/* Right Side: Image Information and Edit Controls */}
      <div className="w-1/3 flex flex-col h-full pl-6 border-l">
        {/* Image Information */}
        <div className="flex-grow space-y-6">
          <div>
            <h2 className="text-2xl font-bold mb-2">Image Information</h2>
            <p><strong>Created by:</strong> John Doe</p>
            <p><strong>Created on:</strong> 2023-06-15</p>
            <p>
              <strong>Creation method:</strong>{' '}
              {image?.creationMethod === 'upload' ? (
                <Upload className="inline w-4 h-4 mr-1" />
              ) : (
                <Wand2 className="inline w-4 h-4 mr-1" />
              )}
              {image?.creationMethod === 'upload' ? 'Uploaded' : 'Generated'}
            </p>
          </div>
          
          <div>
            <h3 className="font-semibold mb-2">Caption</h3>
            <div className="max-h-[4.5em] overflow-y-auto">
              <p className="whitespace-pre-wrap">{image?.caption || "A beautiful landscape with mountains and a lake"}</p>
            </div>
          </div>
          
          <div>
            <h3 className="font-semibold mb-2">Tags</h3>
            <div className="flex flex-wrap gap-2 max-h-16 overflow-y-auto">
              <Badge>nature</Badge>
              <Badge>landscape</Badge>
              <Badge>mountains</Badge>
              <Badge>lake</Badge>
            </div>
          </div>
          
          <div>
            <p><strong>Dimensions:</strong> {image?.dimensions?.width}x{image?.dimensions?.height || "1200x800"}</p>
            <p><strong>Aspect ratio:</strong> {image?.dimensions?.aspectRatio || "3:2"}</p>
            <p><strong>Resolution:</strong> {image?.resolution || "72"} DPI</p>
            <p><strong>File size:</strong> 2.5 MB</p>
            <p><strong>Format:</strong> {image?.format || "PNG"}</p>
          </div>
        </div>
        
        {/* Edit Image Controls */}
        <div className="mt-4 mb-2 space-y-4 bg-slate-100 border border-slate-200 px-4 py-2 rounded-lg shadow-sm">
          <h3 className="font-semibold text-slate-800">Edit Image</h3>
          
          <div>
            <Label htmlFor="whatToChange" className="text-slate-700">What to replace</Label>
            <Input
              id="whatToChange"
              value={whatToChange}
              onChange={(e) => setWhatToChange(e.target.value)}
              placeholder="e.g., background"
              className="bg-white mt-1"
            />
          </div>
          
          <div>
            <Label htmlFor="howToChange" className="text-slate-700">How to change</Label>
            <Input
              id="howToChange"
              value={howToChange}
              onChange={(e) => setHowToChange(e.target.value)}
              placeholder="e.g., on the surface of the moon"
              className="bg-white mt-1"
            />
          </div>
          
          <Button
            onClick={handleGenerate}
            disabled={!whatToChange || !howToChange}
            className="w-full bg-blue-500 text-white hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
          >
            <Wand2 className="h-4 w-4" />
            <span>Generate New Version</span>
          </Button>
        </div>
      </div>
    </div>
  )
}
