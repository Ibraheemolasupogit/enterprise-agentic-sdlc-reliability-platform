export class AppError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
  ) {
    super(message);
  }
}

export function badInput(message = "The request is not valid."): never {
  throw new AppError(400, "INVALID_INPUT", message);
}

export function notFound(): never {
  throw new AppError(404, "NOT_FOUND", "The requested resource was not found.");
}
