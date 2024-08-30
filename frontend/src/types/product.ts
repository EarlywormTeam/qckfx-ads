import { z } from 'zod';

export const ProductSchema = z.object({
  id: z.string(),
  name: z.string(),
  organizationId: z.string(),
  createdByUserId: z.string(),
  primaryImageId: z.string(),
  primaryImageUrl: z.string(),
  additionalImageIds: z.array(z.string()),
  additionalImageUrls: z.array(z.string()),
  stage: z.enum(['queued', 'in_progress', 'completed', 'error']),
  log: z.string(),
  createdAt: z.string().datetime(),
  updatedAt: z.string().datetime(),
  backgroundRemovedImageId: z.string().nullable(),
  backgroundRemovedImageUrl: z.string().nullable(),
  description: z.string().nullable(),
});

export type Product = z.infer<typeof ProductSchema>;
