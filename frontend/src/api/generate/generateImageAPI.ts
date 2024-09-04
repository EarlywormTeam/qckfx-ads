import BaseAPI from '../base';
import { z } from 'zod';

export default class GenerateImageAPI extends BaseAPI {
  async generateProductImage(productId: string, prompt: string, count: number): Promise<string> {
    const response = await this.request('POST', `/product/${productId}/generate`, { prompt, count });

    const result = this.handleResponse(
      response,
      z.object({
        generationJobId: z.string(),
      })
    );

    return result.generationJobId;
  }

  async pollGenerationJob(generationJobId: string, maxAttempts = 150, interval = 2000): Promise<{ status: string, images?: { url: string }[] }> {
    const schema = z.object({
      generationJob: z.object({
        status: z.enum(['pending', 'in_progress', 'completed', 'error']),
      }),
      generatedImages: z.array(z.object({ url: z.string() })).optional(),
    });

    for (let attempt = 0; attempt < maxAttempts; attempt++) {
      const response = await this.request('GET', `/generation/${generationJobId}`);
      const result = this.handleResponse(response, schema);

      if (result.generationJob.status === 'completed' || result.generationJob.status === 'error') {
        return {
          status: result.generationJob.status,
          images: result.generatedImages,
        };
      }

      await new Promise(resolve => setTimeout(resolve, interval));
    }

    throw new Error('Polling timed out');
  }
}
