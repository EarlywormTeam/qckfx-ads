import { ImageSearchRequest, ImageSearchResponse, ImageSearchResponseSchema } from "@/types/search";
import BaseAPI from "@/api/base";
import { Image, ImageSchema } from "@/types/image";

export default class ImageSearchAPI extends BaseAPI {
  async searchImages(organizationId: string, search: ImageSearchRequest, signal?: AbortSignal): Promise<ImageSearchResponse> {
    const response = await this.request("POST", `/${organizationId}/image/search`, search, { signal });
    return this.handleResponse(response, ImageSearchResponseSchema);  
  }

  async getImageById(imageId: string): Promise<Image> {
    const response = await this.request("GET", `/image/${imageId}`);
    return this.handleResponse(response, ImageSchema);
  }
}
