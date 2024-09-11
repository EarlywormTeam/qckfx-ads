import BaseAPI from '../base';
import { z } from 'zod';
import { GenerationJobResponseSchema, GenerationJobResponse } from '@/types/generatedImage';

export default class GenerateImageAPI extends BaseAPI {
  async generateProductImage(productId: string, prompt: string, count: number): Promise<string> {
    const response = await this.request('POST', `/product/${productId}/generate`, { prompt, count });

    const result = this.handleResponse(
      response,
      z.object({
        generationJobId: z.string(),
        imageGroupIds: z.array(z.string()),
      })
    );

    return result.generationJobId;
  }

  async *pollGenerationJob(generationJobId: string, maxAttempts = 150, interval = 2500): AsyncGenerator<GenerationJobResponse, GenerationJobResponse, undefined> {
    for (let attempt = 0; attempt < maxAttempts; attempt++) {
      const response = await this.request('GET', `/generation/${generationJobId}`);
      const result = this.handleResponse(response, GenerationJobResponseSchema);

      // Yield partial results
      if (result.imageGroups && result.imageGroups.length > 0) {
        yield result;
      }

      if (result.generationJob.status === 'completed' || result.generationJob.status === 'error') {
        return result;
      }

      await new Promise(resolve => setTimeout(resolve, interval));
    }

    throw new Error('Polling timed out');
  }

  async refineImage(imageGroupId: string, imageId: string, prompt: string, noiseStrength: number = 0, denoiseAmount: number = 0.9): Promise<{
    generationJobId: string;
    imageGroupId: string;
    imageId: string;
  }> {
    const response = await this.request('POST', `/image_group/${imageGroupId}/image/${imageId}/refine`, {
      prompt,
      noise_strength: noiseStrength,
      denoise_amount: denoiseAmount
    });

    const result = this.handleResponse(
      response,
      z.object({
        generationJobId: z.string(),
        imageGroupId: z.string(),
        imageId: z.string(),
      })
    );

    return {
      generationJobId: result.generationJobId,
      imageGroupId: result.imageGroupId,
      imageId: result.imageId,
    };
  }
}
