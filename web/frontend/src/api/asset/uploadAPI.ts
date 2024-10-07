import axios from 'axios';
import { v4 as uuidv4 } from 'uuid';

export const getUploadUrl = async (organizationId: string): Promise<string> => {
  const response = await axios.get(`/api/organizations/${organizationId}/upload-urls`);
  return response.data.upload_url;
};

export const uploadFile = async (file: File, uploadUrl: string, organizationId: string): Promise<void> => {
  const fileExtension = file.name.split('.').pop() || '';
  const newFileName = `${organizationId}/${uuidv4()}.${fileExtension}`;
  
  const formData = new FormData();
  formData.append('file', file, newFileName);

  await axios.put(uploadUrl, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
};

export const uploadFiles = async (files: File[], organizationId: string): Promise<void> => {
  const uploadUrl = await getUploadUrl(organizationId);

  for (const file of files) {
    await uploadFile(file, uploadUrl, organizationId);
  }
};
