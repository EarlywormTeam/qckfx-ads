import GenerateImageAPI from './generateImageAPI';
import { useAPI } from '@/api';
import { GenerationJobResponse } from '@/types/generatedImage';

export class GenerateAPI {
  private generateImageAPI: GenerateImageAPI;

  constructor() {
    this.generateImageAPI = new GenerateImageAPI();
  }

  async generateProductImage(productId: string, prompt: string, count: number): Promise<string> {
    return this.generateImageAPI.generateProductImage(productId, prompt, count);
  }

  async pollGenerationJob(generationJobId: string, maxAttempts?: number, interval?: number): Promise<GenerationJobResponse> {
    return this.generateImageAPI.pollGenerationJob(generationJobId, maxAttempts, interval);
  }

  async refineImage(imageGroupId: string, imageId: string, prompt: string, noiseStrength: number = 0, denoiseAmount: number = 0.9): Promise<{
    generationJobId: string;
    imageGroupId: string;
    imageId: string;
  }> {
    return this.generateImageAPI.refineImage(imageGroupId, imageId, prompt, noiseStrength, denoiseAmount);
  }
}

export function useGenerateAPI() {
  const api = useAPI();
  return api.createGenerateAPI();
}
