import React, { useRef, useEffect } from 'react';
import { useChat } from '../hooks/useChat';
import { ChatMessageComponent } from '../components/chat/ChatMessage';
import { ChatInput } from '../components/chat/ChatInput';
import { ExamplePrompts } from '../components/chat/ExamplePrompts';
import { SourcesPanel } from '../components/sources/SourcesPanel';
import { SourceDrawer } from '../components/sources/SourceDrawer';
import { Bot, MessageSquare } from 'lucide-react';

interface ChatPageProps {
  isDevMode: boolean;
}

export const ChatPage: React.FC<ChatPageProps> = ({ isDevMode }) => {
  const {
    messages,
    activeSources,
    selectedSource,
    isDrawerOpen,
    isLoading,
    loadingStage,
    error,
    sendMessage,
    clearChat,
    openSourceDetail,
    closeSourceDrawer,
  } = useChat();

  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  return (
    <div className="flex h-full w-full overflow-hidden">
      {/* Left/Center: Chat Interface */}
      <div className="flex-1 flex flex-col h-full overflow-hidden bg-slate-50/50 dark:bg-slate-950">
        {/* Messages List Area */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-4">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col justify-center items-center">
              <ExamplePrompts onSelectPrompt={(prompt) => sendMessage(prompt)} />
            </div>
          ) : (
            <div className="max-w-4xl mx-auto space-y-4">
              {messages.map((msg) => (
                <ChatMessageComponent
                  key={msg.id}
                  message={msg}
                  isDevMode={isDevMode}
                  onOpenSource={openSourceDetail}
                  onRegenerate={(query) => sendMessage(query)}
                />
              ))}

              {/* Autoscroll anchor */}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Chat Input */}
        <ChatInput
          onSendMessage={sendMessage}
          onClearChat={clearChat}
          isLoading={isLoading}
          loadingStage={loadingStage}
        />
      </div>

      {/* Right: Sources Sidebar */}
      <SourcesPanel
        sources={activeSources}
        onOpenDetail={openSourceDetail}
      />

      {/* Source Detail Drawer Modal */}
      <SourceDrawer
        source={selectedSource}
        isOpen={isDrawerOpen}
        onClose={closeSourceDrawer}
      />
    </div>
  );
};
