import { z } from 'zod';

export const APIErrorSchema = z.object({
  errorMessage: z.string(),
  statusCode: z.number().int().positive().optional()
});

export class APIError extends Error {
  constructor(public errorMessage: string, public statusCode: number | undefined) {
    super(errorMessage);
    this.name = 'APIError';
  }

  static fromSchema(data: z.infer<typeof APIErrorSchema>): APIError {
    return new APIError(data.errorMessage, data.statusCode);
  }
}