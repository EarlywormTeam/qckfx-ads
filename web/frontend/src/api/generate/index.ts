import { useMemo } from 'react';
import GenerateImageAPI from './generateImageAPI';
import AvatarAPI from './avatarAPI';
import { useAPI } from '@/api';
import { GenerationJobResponse } from '@/types/generatedImage';
import { AvatarListResponse } from './avatarAPI';

export class GenerateAPI {
  private generateImageAPI: GenerateImageAPI;
  private avatarAPI: AvatarAPI;

  constructor() {
    this.generateImageAPI = new GenerateImageAPI();
    this.avatarAPI = new AvatarAPI();
  }

  async generateProductImage(productId: string, prompt: string, count: number): Promise<string> {
    return this.generateImageAPI.generateProductImage(productId, prompt, count);
  }


  async *pollGenerationJob(generationJobId: string, maxAttempts?: number, interval?: number): AsyncGenerator<GenerationJobResponse, GenerationJobResponse, undefined> {
    const generator = this.generateImageAPI.pollGenerationJob(generationJobId, maxAttempts, interval);
    for await (const response of generator) {
      yield response;
    }
    return (await generator.next()).value;
  }

  async refineImage(imageGroupId: string, imageId: string, prompt: string): Promise<{
    generationJobId: string;
    imageGroupId: string;
    imageId: string;
  }> {
    return this.generateImageAPI.refineImage(imageGroupId, imageId, prompt);
  }

  async getAvatars(organizationId: string): Promise<AvatarListResponse> {
    return this.avatarAPI.getAvatars(organizationId);
  }
}

export function useGenerateAPI() {
  const api = useAPI();
  return useMemo(() => api.createGenerateAPI(), [api]);
}
