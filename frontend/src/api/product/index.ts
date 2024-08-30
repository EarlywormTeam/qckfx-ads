import { Product } from '@/types/product';
import CreateProductAPI from './createAPI';
import { useAPI } from '@/api';

export class ProductAPI {
  private createProductAPI: CreateProductAPI;

  constructor() {
    this.createProductAPI = new CreateProductAPI();
  }

  async createProduct(
    name: string,
    primaryImageId: string,
    primaryImageUrl: string,
    additionalImageIds: string[] = [],
    additionalImageUrls: string[] = []
  ): Promise<Product> {
    return this.createProductAPI.createProduct(
      name,
      primaryImageId,
      primaryImageUrl,
      additionalImageIds,
      additionalImageUrls
    );
  }
}

export function useProductAPI() {
  const api = useAPI();
  return api.createProductAPI();
}
