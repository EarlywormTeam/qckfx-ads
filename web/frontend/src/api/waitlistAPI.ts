import BaseAPI from './base';
import { z } from 'zod';

const WaitlistResponseSchema = z.object({
  message: z.string(),
});

export default class WaitlistAPI extends BaseAPI {
  async joinWaitlist(email: string): Promise<string> {
    const response = await this.request('POST', '/waitlist', { email });

    const result = this.handleResponse(
      response,
      WaitlistResponseSchema
    );

    return result.message;
  }
}