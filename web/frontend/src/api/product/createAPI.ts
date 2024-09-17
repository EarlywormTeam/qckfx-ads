import BaseAPI from '../base';
import { z } from 'zod';
import { Product, ProductSchema } from '@/types/product';

export default class CreateProductAPI extends BaseAPI {
  async createProduct(
    name: string,
    primaryImageId: string,
    primaryImageUrl: string,
    additionalImageIds: string[] = [],
    additionalImageUrls: string[] = []
  ): Promise<Product> {
    const response = await this.request('POST', '/api/product', {
      name,
      primaryImageId,
      primaryImageUrl,
      additionalImageIds,
      additionalImageUrls,
    });

    const result = this.handleResponse(
      response,
      z.object({
        product: ProductSchema,
      })
    );

    return result.product;
  }
}
