import BaseAPI from '../base';
import { z } from 'zod';

const AvatarPreviewImageSchema = z.object({
  previewImage169: z.string().optional(),
  previewImage11: z.string().optional(),
  previewImage916: z.string().optional(),
});

const AvatarResponseSchema = z.object({
  id: z.string(),
  name: z.string(),
  gender: z.string(),
  previewImages: AvatarPreviewImageSchema,
});

const AvatarListResponseSchema = z.object({
  avatars: z.array(AvatarResponseSchema),
});

export type AvatarResponse = z.infer<typeof AvatarResponseSchema>;
export type AvatarListResponse = z.infer<typeof AvatarListResponseSchema>;

export default class AvatarAPI extends BaseAPI {
  async getAvatars(organizationId: string): Promise<AvatarListResponse> {
    const response = await this.request('GET', `/organization/${organizationId}/avatar`);
    return this.handleResponse(response, AvatarListResponseSchema);
  }
}
