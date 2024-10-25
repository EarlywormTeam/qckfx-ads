import { useAPI } from '@/api';
import UploadAPI from './uploadAPI';
import ImageSearchAPI from './searchAPI';
import { ImageSearchRequest, ImageSearchResponse } from '@/types/search';
import { useMemo } from 'react';
import { Image } from '@/types/image';

export class AssetAPI {
  private uploadAPI: UploadAPI;
  private imageSearchAPI: ImageSearchAPI;
  constructor() {
    this.uploadAPI = new UploadAPI();
    this.imageSearchAPI = new ImageSearchAPI();
  }

  async getUploadUrl(organizationId: string): Promise<string> {
    return this.uploadAPI.getUploadUrl(organizationId);
  }

  async uploadFile(file: File, uploadUrl: string, organizationId: string, progressCallback: (progress: number) => void): Promise<{
    fileName: string;
    progress: number;
  }> {
    return this.uploadAPI.uploadFile(file, uploadUrl, organizationId, progressCallback);
  }

  async uploadFiles(files: File[], organizationId: string, progressCallbacks: ((progress: number) => void)[]): Promise<Promise<{
    fileName: string;
    progress: number;
  }>[]> {
    return this.uploadAPI.uploadFiles(files, organizationId, progressCallbacks);
  }

  async notifyUploadedFiles(organizationId: string, fileNames: string[]): Promise<void> {
    return this.uploadAPI.notifyUploadedFiles(organizationId, fileNames);
  }

  async searchImages(organizationId: string, search: ImageSearchRequest, signal?: AbortSignal): Promise<ImageSearchResponse> {
    return this.imageSearchAPI.searchImages(organizationId, search, signal);
  }

  async getImageById(imageId: string): Promise<Image> {
    return this.imageSearchAPI.getImageById(imageId);
  }
}

export function useAssetAPI() {
  const api = useAPI();
  return useMemo(() => api.createAssetAPI(), [api]);
}
