import { z } from 'zod';

const DimensionsSchema = z.object({
  width: z.number().int(),
  height: z.number().int(),
  aspectRatio: z.number(),
});

export const ImageSchema = z.object({
  id: z.string(),
  creationMethod: z.string(),
  url: z.string().url(),
  dimensions: DimensionsSchema,
  resolution: z.number().int(),
  format: z.string(),
  caption: z.string().optional(),
  // createdAt: z.string().datetime(),
  // updatedAt: z.string().datetime(),
});

export type Image = z.infer<typeof ImageSchema>;
export type Dimensions = z.infer<typeof DimensionsSchema>;
