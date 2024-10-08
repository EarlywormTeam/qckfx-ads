import { useAPI } from '@/api';
import UploadAPI from './uploadAPI';

export class AssetAPI {
  private uploadAPI: UploadAPI;

  constructor() {
    this.uploadAPI = new UploadAPI();
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
}

export function useAssetAPI() {
  const api = useAPI();
  return api.createAssetAPI();
}
