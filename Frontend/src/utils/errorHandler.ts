import axios, { AxiosError } from 'axios';

export interface ApiError {
  message: string;
  code?: string;
  details?: any;
}

export class BacktestApiError extends Error {
  public readonly code?: string;
  public readonly details?: any;

  constructor(message: string, code?: string, details?: any) {
    super(message);
    this.name = 'BacktestApiError';
    this.code = code;
    this.details = details;
  }
}

export const handleApiError = (error: unknown): ApiError => {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<any>;
    
    // Handle specific HTTP status codes
    switch (axiosError.response?.status) {
      case 401:
        return {
          message: 'Authentication required. Please log in again.',
          code: 'AUTH_REQUIRED',
        };
      case 403:
        return {
          message: 'You do not have permission to perform this action.',
          code: 'FORBIDDEN',
        };
      case 404:
        return {
          message: 'The requested resource was not found.',
          code: 'NOT_FOUND',
        };
      case 422:
        return {
          message: 'Invalid input data.',
          code: 'VALIDATION_ERROR',
          details: axiosError.response?.data?.errors,
        };
      case 429:
        return {
          message: 'Too many requests. Please try again later.',
          code: 'RATE_LIMIT',
        };
      case 500:
        return {
          message: 'An unexpected error occurred. Please try again later.',
          code: 'SERVER_ERROR',
        };
      default:
        return {
          message: axiosError.response?.data?.message || 'An unexpected error occurred.',
          code: axiosError.response?.data?.code || 'UNKNOWN_ERROR',
          details: axiosError.response?.data?.details,
        };
    }
  }

  if (error instanceof Error) {
    return {
      message: error.message,
      code: 'CLIENT_ERROR',
    };
  }

  return {
    message: 'An unexpected error occurred.',
    code: 'UNKNOWN_ERROR',
  };
};

export const createErrorMessage = (error: ApiError): string => {
  let message = error.message;

  if (error.details) {
    if (typeof error.details === 'object') {
      const details = Object.entries(error.details)
        .map(([key, value]) => `${key}: ${value}`)
        .join(', ');
      message += ` (${details})`;
    } else {
      message += ` (${error.details})`;
    }
  }

  return message;
};
