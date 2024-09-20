import { z } from 'zod';

export const GeneratedImageSchema = z.object({
  id: z.string(),
  url: z.string().nullable(),
  createdAt: z.string(),
  status: z.enum(['pending', 'generated', 'failed']),
});

export const ImageGroupSchema = z.object({
  id: z.string(),
  createdAt: z.string(),
  updatedAt: z.string(),
  defaultImageId: z.string().nullable(),
  images: z.array(GeneratedImageSchema),
});

export const GenerationJobSchema = z.object({
  id: z.string(),
  status: z.enum(['pending', 'in_progress', 'completed', 'error', 'failed']),
  // Add other relevant fields as needed
});

export const GenerationJobResponseSchema = z.object({
  generationJob: GenerationJobSchema,
  imageGroups: z.array(ImageGroupSchema).optional(),
});

export type GeneratedImage = z.infer<typeof GeneratedImageSchema>;
export type ImageGroup = z.infer<typeof ImageGroupSchema>;
export type GenerationJob = z.infer<typeof GenerationJobSchema>;
export type GenerationJobResponse = z.infer<typeof GenerationJobResponseSchema>;