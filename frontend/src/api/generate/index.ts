import GenerateImageAPI from './generateImageAPI';
import { useAPI } from '@/api';

export class GenerateAPI {
  private generateImageAPI: GenerateImageAPI;

  constructor() {
    this.generateImageAPI = new GenerateImageAPI();
  }

  async generateProductImage(productId: string, prompt: string, count: number): Promise<string> {
    return this.generateImageAPI.generateProductImage(productId, prompt, count);
  }

  async pollGenerationJob(generationJobId: string, maxAttempts?: number, interval?: number): Promise<{ status: string, images?: { url: string }[] }> {
    return this.generateImageAPI.pollGenerationJob(generationJobId, maxAttempts, interval);
  }
}

export function useGenerateAPI() {
  const api = useAPI();
  return api.createGenerateAPI();
}
