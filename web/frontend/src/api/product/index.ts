import { Product } from '@/types/product';
import { ImageGroup } from '@/types/generatedImage';
import CreateProductAPI from './createAPI';
import GetProductsAPI from './getAPI';
import ImageGroupAPI from './imageGroupAPI';
import { useAPI } from '@/api';
import { useMemo } from 'react';
export class ProductAPI {
  private createProductAPI: CreateProductAPI;
  private getProductsAPI: GetProductsAPI;
  private imageGroupAPI: ImageGroupAPI;

  constructor() {
    this.createProductAPI = new CreateProductAPI();
    this.getProductsAPI = new GetProductsAPI();
    this.imageGroupAPI = new ImageGroupAPI();
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

  async getProductImageGroups(productId: string): Promise<ImageGroup[]> {
    return this.imageGroupAPI.getProductImageGroups(productId);
  }

  async deleteImageGroup(productId: string, groupId: string): Promise<void> {
    return this.imageGroupAPI.deleteImageGroup(productId, groupId);
  }

  async downloadImage(imageId: string): Promise<Blob> {
    return this.imageGroupAPI.downloadImage(imageId);
  }
}

    // Start of Selection
    export function useProductAPI() {
      const api = useAPI();
      return useMemo(() => api.createProductAPI(), [api]);
    }
