import React, { ErrorInfo } from 'react';
import { Button } from '@mui/material';
import { Alert, AlertTitle } from '@mui/material';
import { RefreshRounded, BugReportRounded } from '@mui/icons-material';

interface ErrorFallbackProps {
  error: Error | null;
  errorInfo: ErrorInfo | null;
  resetError: () => void;
}

export const ErrorFallback: React.FC<ErrorFallbackProps> = ({
  error,
  errorInfo,
  resetError,
}) => {
  const isDevelopment = process.env.NODE_ENV === 'development';

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <Alert
          severity="error"
          className="mb-4"
          action={
            <Button
              color="inherit"
              size="small"
              onClick={resetError}
              startIcon={<RefreshRounded />}
            >
              Try Again
            </Button>
          }
        >
          <AlertTitle>Something went wrong</AlertTitle>
          <p className="text-sm text-gray-600">
            We're sorry, but something unexpected happened. Our team has been
            notified and is working on the issue.
          </p>
        </Alert>

        {isDevelopment && error && (
          <div className="mt-4 p-4 bg-gray-100 rounded-md">
            <div className="flex items-center mb-2">
              <BugReportRounded className="mr-2" />
              <h3 className="text-lg font-medium">Debug Information</h3>
            </div>
            <div className="text-sm font-mono overflow-auto">
              <p className="text-red-600">{error.toString()}</p>
              {errorInfo && (
                <pre className="mt-2 text-gray-700">
                  {errorInfo.componentStack}
                </pre>
              )}
            </div>
          </div>
        )}

        <div className="mt-4 text-center">
          <Button
            variant="contained"
            color="primary"
            onClick={() => window.location.href = '/'}
          >
            Return to Home
          </Button>
        </div>
      </div>
    </div>
  );
};
