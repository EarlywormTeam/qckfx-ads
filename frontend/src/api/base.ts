import axios from 'axios';
import { z } from 'zod';
import { camelizeKeys, decamelizeKeys } from 'humps';
import { APIError, APIErrorSchema } from '@/types/apiError';

export default class BaseAPI {
  protected baseURL: string;

  constructor() {
    this.baseURL = import.meta.env.VITE_API_URL || '/api';
  }

  protected async request(method: string, endpoint: string, data?: Record<string, unknown>): Promise<unknown> {
    try {
      const response = await axios({
        method,
        url: `${this.baseURL}${endpoint}`,
        data: data ? decamelizeKeys(data) : undefined,
        headers: {
          'Content-Type': 'application/json',
        },
        validateStatus: (status) => status >= 200 && status < 300,
      });
      return camelizeKeys(response.data);
    } catch (error) {
      console.log(error)
      if (axios.isAxiosError(error)) {
        throw new APIError(
          error.response?.data?.message || `Request failed with status ${error.response?.status}`,
          error.response?.status
        );
      }
      throw error;
    }
  }

  protected async fileRequest<T>(method: string, endpoint: string, file: File): Promise<T> {
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await axios({
        method,
        url: `${this.baseURL}${endpoint}`,
        data: formData,
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        validateStatus: (status) => status >= 200 && status < 300,
      });
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        throw new APIError(
          error.response?.data?.message || `File request failed with status ${error.response?.status}`,
          error.response?.status
        );
      }
      throw error;
    }
  }

  protected handleResponse<T>(response: unknown, schema: z.ZodType<T>): T {
    const camelizedResponse = camelizeKeys(response);
    const result = schema.safeParse(camelizedResponse);
    if (result.success) {
      return result.data;
    }
    console.log(result.error)

    const errorResult = APIErrorSchema.safeParse(camelizedResponse);
    if (errorResult.success) {
      throw APIError.fromSchema(errorResult.data);
    }

    throw new Error('Unexpected response format');
  }
}