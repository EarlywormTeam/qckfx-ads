import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Loader2 } from "lucide-react"
import { AvatarResponse } from "@/api/generate/avatarAPI"
import { useGenerateAPI } from "@/api/generate"
import { useOrganization } from "@/hooks/organization/useOrganization"
import VideoPreview from "@/components/VideoPreview"

export default function Component() {
  const [avatars, setAvatars] = useState<AvatarResponse[]>([])
  const [selectedAvatar, setSelectedAvatar] = useState<AvatarResponse | null>(null)
  const [prompt, setPrompt] = useState("")
  const [filter, setFilter] = useState("all")
  const [isGenerating, setIsGenerating] = useState(false)
  const [videoReady, setVideoReady] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const generateAPI = useGenerateAPI()
  const { organization } = useOrganization()

  useEffect(() => {
    const fetchAvatars = async () => {
      if (!organization) {
        throw new Error("No organization selected");
      }
      try {
        const response = await generateAPI.getAvatars(organization.id);
        setAvatars(response.avatars);
      } catch (error) {
        console.error("Failed to fetch avatars:", error);
      } finally {
        setIsLoading(false);
      }
    }

    fetchAvatars()
  }, [organization, generateAPI])

  const handleGenerate = () => {
    if (selectedAvatar && prompt) {
      setIsGenerating(true)
      // Simulating video generation
      setTimeout(() => {
        setIsGenerating(false)
        setVideoReady(true)
      }, 3000)
    }
  }

  const getPreviewImage = (avatar: AvatarResponse, forceAspectRatio?: string) => {
    const ratio = forceAspectRatio || "1:1" 

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

  const getVisibilityClass = (avatar: AvatarResponse) => {
    return filter === "all" || avatar.gender.toLowerCase() === filter[0].toLowerCase() ? "" : "hidden";
  };

  return (
    <div className="flex max-h-full h-full w-full bg-gray-100 overflow-hidden">
      <div className="p-8 w-3/4 flex flex-col h-full">
        <div className="flex-grow overflow-hidden flex flex-col">
          <div className="flex-grow overflow-hidden">
            <VideoPreview
              selectedAvatar={selectedAvatar}
              isGenerating={isGenerating}
              videoReady={videoReady}
            />
          </div>
          <div className="mt-4 flex flex-col">
            <Label htmlFor="prompt">Enter prompt for the avatar:</Label>
            <Textarea
              id="prompt"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Type your prompt here..."
              className="mt-1 h-24 resize-none"
            />
          </div>
        </div>
        <Button 
          onClick={handleGenerate} 
          disabled={!selectedAvatar || !prompt || isGenerating}
          className="mt-4"
        >
          {isGenerating ? "Generating..." : "Generate Video"}
        </Button>
      </div>
      <div className="w-1/4 bg-white px-8 pt-8 shadow-lg overflow-hidden flex flex-col">
        <div className="mb-6">
          <h2 className="text-xl font-bold mb-4">Select Avatar</h2>
          <RadioGroup value={filter} onValueChange={setFilter} className="mb-4">
            <div className="flex space-x-2">
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="all" id="all" />
                <Label htmlFor="all">All</Label>
              </div>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="male" id="male" />
                <Label htmlFor="male">Male</Label>
              </div>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="female" id="female" />
                <Label htmlFor="female">Female</Label>
              </div>
            </div>
          </RadioGroup>
        </div>
        <ScrollArea className="flex-grow -mx-2 px-2">
          {isLoading ? (
            <div className="flex items-center justify-center h-full">
              <Loader2 className="h-10 w-10 animate-spin" />
            </div>
          ) : (
            <div className="grid grid-cols-2 gap-4">
              {avatars.map((avatar) => (
                <button
                  key={avatar.id}
                  className={`relative rounded-lg overflow-hidden transition-all duration-200 ${
                    selectedAvatar?.id === avatar.id
                      ? "ring-2 ring-primary bg-primary/10"
                      : "hover:bg-gray-100"
                  } ${getVisibilityClass(avatar)}`}
                  onClick={() => setSelectedAvatar(avatar)}
                >
                  <div className="aspect-square">
                    <img
                      src={getPreviewImage(avatar, "1:1")}
                      alt={avatar.name}
                      className="w-full h-full object-cover rounded-lg"
                    />
                  </div>
                  <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/60 to-transparent text-white p-2 text-sm">
                    {avatar.name}
                  </div>
                </button>
              ))}
            </div>
          )}
        </ScrollArea>
      </div>
    </div>
  )
}
