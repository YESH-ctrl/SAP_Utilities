import { useState, useCallback } from 'react';
import { ChatMessage, Source, Citation, RetrievalMetadata } from '../types/chat';
import { sendChatMessage } from '../services/chatApi';

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [activeSources, setActiveSources] = useState<Source[]>([]);
  const [selectedSource, setSelectedSource] = useState<Source | null>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastMetadata, setLastMetadata] = useState<RetrievalMetadata | null>(null);
  const [loadingStage, setLoadingStage] = useState<string | null>(null);

  const sendMessage = useCallback(async (query: string) => {
    if (!query.trim() || isLoading) return;

    setError(null);
    setIsLoading(true);
    setLoadingStage('Searching SAP documentation...');

    const userMessage: ChatMessage = {
      id: `usr_${Date.now()}`,
      role: 'user',
      content: query,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMessage]);

    try {
      setTimeout(() => setLoadingStage('Analyzing retrieved sources...'), 600);
      setTimeout(() => setLoadingStage('Generating SAP response...'), 1200);

      const response = await sendChatMessage({ query });

      const assistantMessage: ChatMessage = {
        id: `asst_${Date.now()}`,
        role: 'assistant',
        content: response.answer,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        sources: response.sources,
        citations: response.citations,
        metadata: response.metadata,
      };

      setMessages((prev) => [...prev, assistantMessage]);
      setActiveSources(response.sources || []);
      if (response.metadata) {
        setLastMetadata(response.metadata);
      }
    } catch (err: any) {
      console.error('Chat error:', err);
      const errorMessage = err?.message || 'Failed to connect to SAP Utilities AI engine.';
      setError(errorMessage);
      
      // Add error message in chat UI
      setMessages((prev) => [
        ...prev,
        {
          id: `err_${Date.now()}`,
          role: 'assistant',
          content: `⚠️ **Connection Error**: ${errorMessage}\n\nPlease check if the FastAPI backend is running on \`http://localhost:8000\`.`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
      ]);
    } finally {
      setIsLoading(false);
      setLoadingStage(null);
    }
  }, [isLoading]);

  const clearChat = useCallback(() => {
    setMessages([]);
    setActiveSources([]);
    setSelectedSource(null);
    setLastMetadata(null);
    setError(null);
  }, []);

  const openSourceDetail = useCallback((source: Source) => {
    setSelectedSource(source);
    setIsDrawerOpen(true);
  }, []);

  const closeSourceDrawer = useCallback(() => {
    setIsDrawerOpen(false);
  }, []);

  return {
    messages,
    activeSources,
    selectedSource,
    isDrawerOpen,
    isLoading,
    loadingStage,
    error,
    lastMetadata,
    sendMessage,
    clearChat,
    openSourceDetail,
    closeSourceDrawer,
  };
}
