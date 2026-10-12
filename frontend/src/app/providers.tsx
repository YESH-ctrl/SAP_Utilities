import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AgenticWorkflowProvider } from '../context/AgenticWorkflowContext';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

interface ProvidersProps {
  children: React.ReactNode;
}

export const Providers: React.FC<ProvidersProps> = ({ children }) => {
  return (
    <QueryClientProvider client={queryClient}>
      <AgenticWorkflowProvider>
        {children}
      </AgenticWorkflowProvider>
    </QueryClientProvider>
  );
};
