import { z } from 'zod';

export const ProductSchema = z.object({
  id: z.string(),
  name: z.string(),
  organizationId: z.string(),
  createdBy: z.object({
    id: z.string(),
    name: z.string()
  }),
  primaryImageUrl: z.string(),
  additionalImageUrls: z.array(z.string()),
  stage: z.enum(['queued', 'in_progress', 'completed', 'error']),
  log: z.string(),
  createdAt: z.string(),
  updatedAt: z.string(),
  backgroundRemovedImageUrl: z.string().nullable(),
  description: z.string().nullable(),
});

export type Product = z.infer<typeof ProductSchema>;
