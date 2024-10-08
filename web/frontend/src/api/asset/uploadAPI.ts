import { BlockBlobClient } from '@azure/storage-blob';
import { v4 as uuidv4 } from 'uuid';
import { z } from 'zod';

import { convertFileToArrayBuffer } from './convertFileToArrayBuffer';
import BaseAPI from '../base';

export default class UploadAPI extends BaseAPI {
  async getUploadUrl(organizationId: string): Promise<string> {
    const response = await this.request('GET', `/organizations/${organizationId}/upload-urls`);
    const result = this.handleResponse(response, z.object({
      uploadUrl: z.string(),
    }));
    return result.uploadUrl;
  }

  /**
   * Uploads a single file with progress reporting.
   * 
   * @param file - The file to upload.
   * @param uploadUrl - The upload URL obtained from the server.
   * @param organizationId - The ID of the organization.
   * @param onProgress - Optional callback to receive progress updates.
   * @returns A promise that resolves with the uploaded file's name and final progress.
   */
  async uploadFile(
    file: File,
    uploadUrl: string,
    organizationId: string,
    onProgress?: (progress: number) => void
  ): Promise<{ fileName: string; progress: number }> {
    const fileExtension = file.name.split('.').pop() || '';
    const newFileName = `${organizationId}/${uuidv4()}.${fileExtension}`;

    const urlParts = uploadUrl.split('?');
    const modifiedUploadUrl = `${urlParts[0]}/${newFileName}?${urlParts[1]}`;

    console.log('modifiedUploadUrl', modifiedUploadUrl);
    const blobClient = new BlockBlobClient(modifiedUploadUrl);
    const arrayBuffer = await convertFileToArrayBuffer(file);
    if (!arrayBuffer || arrayBuffer.byteLength < 1) {
      throw new Error('Failed to convert file to array buffer.');
    } else if (arrayBuffer.byteLength > 10 * 1024 * 1024) {
      throw new Error('File size is too large.');
    }

    let progress = 0;
    const response = await blobClient.uploadData(arrayBuffer, {
      onProgress: (ev) => {
        progress = ev.loadedBytes / arrayBuffer.byteLength;
        if (onProgress) {
          onProgress(progress);
        }
      },
    });

    console.log('response', response);
    if (response.errorCode) {
      throw new Error(response.errorCode);
    }

    return { fileName: newFileName, progress: 1 };
  }

  /**
   * Uploads multiple files with individual progress reporting.
   * 
   * @param files - An array of files to upload.
   * @param organizationId - The ID of the organization.
   * @param onProgress - Optional array of callbacks for each file's progress.
   * @returns An array of promises that resolve with each file's upload result.
   */
  async uploadFiles(
    files: File[],
    organizationId: string,
    onProgress?: ((progress: number) => void)[]
  ): Promise<Promise<{ fileName: string; progress: number }>[]> {
    const uploadUrl = await this.getUploadUrl(organizationId);

    return files.map((file, index) =>
      this.uploadFile(file, uploadUrl, organizationId, onProgress ? onProgress[index] : undefined)
    );
  }
}
