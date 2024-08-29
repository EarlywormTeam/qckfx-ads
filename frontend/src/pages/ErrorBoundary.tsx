import React, { ReactNode } from 'react';
import { Link } from 'react-router-dom';

interface ErrorBoundaryState {
  hasError: boolean;
}

interface ErrorBoundaryProps {
  children: ReactNode;
}

class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(): ErrorBoundaryState {
    // Update state so the next render will show the fallback UI.
    return { hasError: true };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo): void {
    // You can log the error to an error reporting service
    console.log('Error:', error);
    console.log('Error Info:', errorInfo);
  }

  render(): ReactNode {
    if (this.state.hasError) {
      // Custom fallback UI with specified styles
      return (
        <div className="w-full h-full flex flex-col items-center justify-center p-12 text-text-white bg-background-accent">
          <h1 className="text-4xl font-bold mb-4">Something went wrong.</h1>
          <Link to="/" className="mt-4 px-4 py-2 border border-text-darkPrimary text-text-darkPrimary hover:bg-text-darkPrimary hover:text-white transition-colors duration-300 rounded">
            Go back to homepage
          </Link>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;