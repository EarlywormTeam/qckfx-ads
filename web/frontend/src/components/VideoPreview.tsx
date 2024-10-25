import { useState } from "react"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Loader2 } from "lucide-react"
import { AvatarResponse } from "@/api/generate/avatarAPI"

const aspectRatios = {
  "9:16": { class: "aspect-[9/16] h-auto w-auto max-h-full max-w-full", container: "items-center justify-center" },
  "1:1": { class: "aspect-square h-auto w-auto max-w-full max-h-full", container: "items-center justify-center" },
  "16:9": { class: "aspect-[16/9] w-auto h-auto max-w-full max-h-full", container: "items-center justify-center" },
}

interface VideoPreviewProps {
  selectedAvatar: AvatarResponse | null
  isGenerating: boolean
  videoReady: boolean
}

export default function VideoPreview({ selectedAvatar, isGenerating, videoReady }: VideoPreviewProps) {
  const [aspectRatio, setAspectRatio] = useState("16:9")

  const getPreviewImage = (avatar: AvatarResponse, forceAspectRatio?: string) => {
    const ratio = forceAspectRatio || aspectRatio

    switch (ratio) {
      case "9:16":
        return avatar.previewImages.previewImage916;
      case "1:1":
        return avatar.previewImages.previewImage11;
      case "16:9":
      default:
        return avatar.previewImages.previewImage169;
    }
  }

  return (
    <div className="flex flex-col max-h-full max-w-full h-full space-y-4 p-4">
      <div className="mb-4 flex-shrink-0">
        <Label htmlFor="aspect-ratio">Select aspect ratio:</Label>
        <Select value={aspectRatio} onValueChange={setAspectRatio}>
          <SelectTrigger id="aspect-ratio" className="mt-1">
            <SelectValue placeholder="Select aspect ratio" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="9:16">9:16 (Vertical)</SelectItem>
            <SelectItem value="1:1">1:1 (Square)</SelectItem>
            <SelectItem value="16:9">16:9 (Horizontal)</SelectItem>
          </SelectContent>
        </Select>
      </div>
      <div className="flex-grow flex justify-center min-h-0">
        <div className="relative overflow-hidden flex flex-grow justify-center w-full max-h-full">
          <div className={`w-full h-0 pb-[56.25%] relative ${aspectRatios[aspectRatio as keyof typeof aspectRatios].class}`}>
            {isGenerating ? (
              <div className="absolute inset-0 flex flex-col items-center justify-center bg-gray-200">
                <Loader2 className="h-10 w-10 rounded-lg animate-spin" />
                <p className="mt-2">Generating video...</p>
              </div>
            ) : videoReady ? (
              <video controls className="absolute top-0 left-0 w-full h-full object-contain rounded-lg">
                <source src="/placeholder.mp4" type="video/mp4" />
                Your browser does not support the video tag.
              </video>
            ) : selectedAvatar ? (
              <img
                src={getPreviewImage(selectedAvatar, aspectRatio)}
                alt={selectedAvatar.name}
                className="absolute top-0 left-0 w-full h-full object-contain rounded-lg"
              />
            ) : (
              <div className="absolute inset-0 flex items-center justify-center bg-gray-200 rounded-lg">
                <p className="text-gray-600">Select an avatar to preview</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
