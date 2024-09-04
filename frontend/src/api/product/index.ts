import { Product } from '@/types/product';
import CreateProductAPI from './createAPI';
import GetProductsAPI from './getAPI';
import { useAPI } from '@/api';

export class ProductAPI {
  private createProductAPI: CreateProductAPI;
  private getProductsAPI: GetProductsAPI;

  constructor() {
    this.createProductAPI = new CreateProductAPI();
    this.getProductsAPI = new GetProductsAPI();
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

  async getProducts(
    organizationId: string
  ): Promise<Array<Product>> {
    return this.getProductsAPI.getProducts(
      organizationId
    );
  }
}

export function useProductAPI() {
  const api = useAPI();
  return api.createProductAPI();
}
