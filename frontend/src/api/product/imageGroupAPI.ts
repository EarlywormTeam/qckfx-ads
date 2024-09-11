import BaseAPI from '../base';
import { z } from 'zod';
import { ImageGroup, ImageGroupSchema } from '@/types/generatedImage'; // Assuming these types exist

export default class ImageGroupAPI extends BaseAPI {
  async getProductImageGroups(productId: string): Promise<ImageGroup[]> {
    const response = await this.request('GET', `/product/${productId}/image-groups`);
    const result = this.handleResponse(
      response,
      z.object({
        imageGroups: z.array(ImageGroupSchema),
      })
    );
    return result.imageGroups;
  }

  async deleteImageGroup(productId: string, groupId: string): Promise<void> {
    await this.request('DELETE', `/product/${productId}/image-group/${groupId}`);
  }

  async downloadImage(imageId: string): Promise<Blob> {
    const response = await this.request('GET', `/image/${imageId}/download`, undefined, 'blob');
    return response as Blob;
  }
}