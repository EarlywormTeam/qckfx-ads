import { z } from 'zod';
import { ImageSchema } from './image';

export const ImageSearchRequestSchema = z.object({
  text: z.string().optional(),
  dominant_colors: z.array(z.string()).optional(),
  faces: z.array(z.string()).optional(),
  products: z.array(z.string()).optional(),
  page: z.number().int().positive().optional().default(1),
  page_size: z.number().int().positive().optional().default(20),
});

export type ImageSearchRequest = z.infer<typeof ImageSearchRequestSchema>;

export const ImageSearchResponseSchema = z.object({
  images: z.array(ImageSchema),
  total: z.number(),
  page: z.number(),
  pageSize: z.number(),
  totalPages: z.number(),
});

export type ImageSearchResponse = z.infer<typeof ImageSearchResponseSchema>;
