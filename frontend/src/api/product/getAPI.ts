import BaseAPI from '../base';
import { z } from 'zod';
import { Product, ProductSchema } from '@/types/product';

export default class GetProductsAPI extends BaseAPI {
  async getProducts(organizationId: string): Promise<Array<Product>> {
    const response = await this.request('GET', `/product?organization_id=${organizationId}`);

    console.log(response);
    const result = this.handleResponse(
      response,
      z.object({
        products: z.array(ProductSchema),
      })
    );

    return result.products;
  }
}
