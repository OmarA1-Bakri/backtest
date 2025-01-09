import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { ErrorBoundary } from '../ErrorBoundary';
import '@testing-library/jest-dom';

const ErrorComponent = () => {
  throw new Error('Test error');
};

describe('ErrorBoundary', () => {
  beforeEach(() => {
    // Suppress console.error for cleaner test output
    jest.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('renders children when there is no error', () => {
    const { getByText } = render(
      <ErrorBoundary>
        <div>Test Content</div>
      </ErrorBoundary>
    );

    expect(getByText('Test Content')).toBeInTheDocument();
  });

  it('renders error fallback when there is an error', () => {
    render(
      <ErrorBoundary>
        <ErrorComponent />
      </ErrorBoundary>
    );

    expect(screen.getByText(/something went wrong/i)).toBeInTheDocument();
    expect(screen.getByText(/try again/i)).toBeInTheDocument();
  });

  it('renders custom fallback when provided', () => {
    const CustomFallback = () => <div>Custom Error View</div>;

    render(
      <ErrorBoundary fallback={<CustomFallback />}>
        <ErrorComponent />
      </ErrorBoundary>
    );

    expect(screen.getByText('Custom Error View')).toBeInTheDocument();
  });

  it('resets error state when try again is clicked', () => {
    const TestComponent = ({ shouldError }: { shouldError: boolean }) => {
      if (shouldError) throw new Error('Test error');
      return <div>Normal Content</div>;
    };

    const { rerender } = render(
      <ErrorBoundary>
        <TestComponent shouldError={true} />
      </ErrorBoundary>
    );

    expect(screen.getByText(/something went wrong/i)).toBeInTheDocument();

    // Click try again button
    fireEvent.click(screen.getByText(/try again/i));

    // Update props to not throw error
    rerender(
      <ErrorBoundary>
        <TestComponent shouldError={false} />
      </ErrorBoundary>
    );

    expect(screen.getByText('Normal Content')).toBeInTheDocument();
  });

  it('shows debug information in development mode', () => {
    const originalEnv = process.env.NODE_ENV;
    process.env.NODE_ENV = 'development';

    render(
      <ErrorBoundary>
        <ErrorComponent />
      </ErrorBoundary>
    );

    expect(screen.getByText(/debug information/i)).toBeInTheDocument();
    expect(screen.getByText(/test error/i)).toBeInTheDocument();

    process.env.NODE_ENV = originalEnv;
  });
});
