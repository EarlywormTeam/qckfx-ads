import { useAPI } from '@/api';
import { getUploadUrl, uploadFile, uploadFiles } from './uploadAPI';

export class AssetAPI {
  async getUploadUrl(organizationId: string): Promise<string> {
    return getUploadUrl(organizationId);
  }

  async uploadFile(file: File, uploadUrl: string, organizationId: string): Promise<void> {
    return uploadFile(file, uploadUrl, organizationId);
  }

  async uploadFiles(files: File[], organizationId: string): Promise<void> {
    return uploadFiles(files, organizationId);
  }
}

export function useAssetAPI() {
  const api = useAPI();
  return api.createAssetAPI();
}
