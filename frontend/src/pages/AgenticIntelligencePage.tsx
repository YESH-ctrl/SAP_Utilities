import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {
  Sparkles,
  Send,
  User,
  Bot,
  Clock,
  CheckCircle2,
  AlertTriangle,
  ExternalLink,
  BookOpen,
  ArrowRight,
  RotateCcw,
  Network,
  ShieldCheck,
  Loader2,
  ChevronRight,
  X,
  StopCircle,
} from 'lucide-react';
import { useAgenticWorkflow } from '../context/AgenticWorkflowContext';
import { EvidenceItem, CitationItem } from '../types/agentic';

export const AgenticIntelligencePage: React.FC = () => {
  const navigate = useNavigate();
  const {
    messages,
    sendMessage,
    clearChat,
    isExecuting,
    cancelCurrentRun,
    selectedEvidence,
    isEvidenceDrawerOpen,
    openEvidenceDetail,
    closeEvidenceDrawer,
  } = useAgenticWorkflow();

  const [inputQuery, setInputQuery] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // References to individual message containers by ID for smart scrolling
  const messageElementsRef = useRef<Map<string, HTMLDivElement>>(new Map());
  const prevMsgCountRef = useRef(messages.length);
  const prevIsExecutingRef = useRef(isExecuting);

  // Smart Auto-scroll:
  // 1. When a user sends a query, smoothly scroll to that user message and loader.
  // 2. When assistant completes response, scroll smoothly to the START of the assistant message,
  //    so the user sees "Direct Answer" and steps from the top rather than being cut off at the bottom!
  useEffect(() => {
    const isNewMessage = messages.length > prevMsgCountRef.current;
    const justFinished = prevIsExecutingRef.current && !isExecuting;

    if (isNewMessage) {
      const latestMsg = messages[messages.length - 1];
      if (latestMsg.role === 'user') {
        setTimeout(() => {
          const el = messageElementsRef.current.get(latestMsg.id);
          el?.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 50);
      } else if (latestMsg.isLoading) {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
      }
      prevMsgCountRef.current = messages.length;
    }

    if (justFinished) {
      // Find the latest completed assistant message
      const lastAssistantMsg = [...messages].reverse().find((m) => m.role === 'assistant');
      if (lastAssistantMsg) {
        setTimeout(() => {
          const el = messageElementsRef.current.get(lastAssistantMsg.id);
          if (el) {
            el.scrollIntoView({ behavior: 'smooth', block: 'start' });
          }
        }, 80);
      }
    }

    prevIsExecutingRef.current = isExecuting;
  }, [messages, isExecuting]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputQuery.trim() || isExecuting) return;
    sendMessage(inputQuery.trim());
    setInputQuery('');
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const samplePrompts = [
    'What is the procedure to reverse a contract in SAP Utilities integration?',
    'How do I perform a move-in reversal in SAP Utilities?',
    'How is installment plan interest calculated in FI-CA?',
    'Explain meter reading estimation rules and plausibility checks in SAP IS-U',
  ];

  const handleSelectPrompt = (prompt: string) => {
    if (isExecuting) return;
    sendMessage(prompt);
  };

  return (
    <div className="flex h-full w-full bg-slate-950 text-slate-100 font-sans overflow-hidden">
      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col h-full min-w-0 relative">
        {/* Streamlined Sub-Header Toolbar (No redundant duplicate title) */}
        <div className="border-b border-slate-800 bg-slate-900/60 backdrop-blur px-4 sm:px-6 py-2.5 flex items-center justify-between shrink-0 z-10">
          <div className="flex items-center gap-2.5">
            <span className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-md text-[11px] font-semibold bg-cyan-950/60 text-cyan-300 border border-cyan-800/50">
              <Sparkles className="w-3 h-3 text-sap-gold" />
              <span>CrewAI v2 Engine</span>
            </span>
            <span className="hidden sm:inline-flex items-center gap-1.5 text-[11px] text-slate-400">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
              <span>Deterministic Retrieval • Disambiguated Procedural Synthesis</span>
            </span>
          </div>

          <div className="flex items-center gap-2">
            {/* Live Canvas Link Button */}
            <button
              onClick={() => navigate('/workflow-canvas')}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-all shadow-sm ${
                isExecuting
                  ? 'bg-cyan-950/80 text-cyan-300 border border-cyan-500/50 hover:bg-cyan-900/80 animate-pulse'
                  : 'bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700'
              }`}
              title="Inspect live agent execution graph, stages, and intermediate artifacts"
            >
              <Network className="w-3.5 h-3.5 text-sap-blue" />
              <span>Live Execution Canvas</span>
              <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
            </button>

            {messages.length > 0 && (
              <button
                onClick={clearChat}
                className="px-2.5 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-slate-200 transition-colors text-xs flex items-center gap-1.5 border border-slate-700"
                title="Start New Conversation"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">New Chat</span>
              </button>
            )}
          </div>
        </div>

        {/* Message Thread Scroll Container */}
        <div
          ref={scrollContainerRef}
          className="flex-1 overflow-y-auto px-4 sm:px-6 py-6 space-y-6"
        >
          {messages.length === 0 ? (
            /* Empty Chat State with Prompt Suggestions */
            <div className="min-h-[60vh] flex flex-col justify-center items-center max-w-2xl mx-auto text-center px-4">
              <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-sap-blue/20 to-cyan-500/20 border border-sap-blue/30 flex items-center justify-center mb-4 shadow-xl">
                <Bot className="w-7 h-7 text-cyan-400" />
              </div>
              <h3 className="text-lg font-bold text-slate-100 mb-1.5">
                How can I assist your SAP Utilities investigation?
              </h3>
              <p className="text-xs text-slate-400 max-w-md mb-8 leading-relaxed">
                Submit procedural, configuration, or architectural questions. An autonomous team of
                specialist agents will investigate the documentation, verify citations, and draft a
                grounded answer.
              </p>

              {/* Sample Prompt Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 w-full text-left">
                {samplePrompts.map((prompt, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSelectPrompt(prompt)}
                    className="p-3 rounded-xl bg-slate-900/80 hover:bg-slate-850 hover:bg-slate-800 border border-slate-800 hover:border-slate-700 text-slate-300 hover:text-white transition-all text-xs flex items-start gap-2.5 group shadow-xs"
                  >
                    <Sparkles className="w-3.5 h-3.5 text-sap-gold shrink-0 mt-0.5 group-hover:scale-110 transition-transform" />
                    <span className="line-clamp-2 leading-relaxed">{prompt}</span>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            /* Chat Message List */
            <div className="max-w-4xl mx-auto space-y-6">
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  ref={(el) => {
                    if (el) messageElementsRef.current.set(msg.id, el);
                    else messageElementsRef.current.delete(msg.id);
                  }}
                  className={`flex items-start gap-3.5 ${
                    msg.role === 'user' ? 'justify-end' : 'justify-start'
                  }`}
                >
                  {/* Assistant Avatar */}
                  {msg.role === 'assistant' && (
                    <div className="w-8 h-8 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-center shrink-0 mt-1 shadow-sm">
                      <Sparkles className="w-4 h-4 text-sap-gold" />
                    </div>
                  )}

                  {/* User Bubble */}
                  {msg.role === 'user' && (
                    <div className="max-w-[85%] sm:max-w-[75%] rounded-2xl rounded-tr-xs p-4 sm:p-5 shadow-sm bg-sap-blue text-white">
                      <div className="text-sm leading-relaxed whitespace-pre-wrap font-sans font-medium">
                        {msg.content}
                      </div>
                    </div>
                  )}

                  {/* Assistant Message Container (Full Width for Readability) */}
                  {msg.role === 'assistant' && (
                    <div className="flex-1 min-w-0 bg-slate-900/90 border border-slate-800/90 text-slate-100 rounded-2xl rounded-tl-xs p-5 sm:p-6 shadow-sm">
                      {/* Loading / Execution State */}
                      {msg.isLoading ? (
                        <div className="space-y-3 py-1">
                          <div className="flex items-center gap-2.5">
                            <Loader2 className="w-4 h-4 text-cyan-400 animate-spin" />
                            <span className="text-xs font-semibold text-cyan-300">
                              {msg.loadingStage || 'Agents orchestrating workflow...'}
                            </span>
                          </div>

                          <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800 text-[11px] text-slate-400 flex items-center justify-between gap-3">
                            <div className="flex items-center gap-2 truncate">
                              <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping"></span>
                              <span className="truncate font-mono">
                                {msg.runId ? `RUN: ${msg.runId}` : 'Initializing run...'}
                              </span>
                            </div>
                            <button
                              onClick={() => navigate('/workflow-canvas')}
                              className="text-xs text-cyan-400 hover:text-cyan-300 font-semibold flex items-center gap-1 shrink-0 transition-colors"
                            >
                              <span>Inspect Live Canvas</span>
                              <ArrowRight className="w-3 h-3" />
                            </button>
                          </div>
                        </div>
                      ) : (
                        <div className="space-y-4">
                          {/* Evidence-Only Warning (HTTP 429 quota mode) */}
                          {msg.response?.response_mode === 'evidence_only' && (
                            <div className="p-3.5 rounded-xl bg-amber-950/40 border border-amber-500/40 text-amber-200 text-xs flex items-start gap-2.5">
                              <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                              <div className="space-y-1">
                                <div className="font-semibold text-amber-300">
                                  Provider Quota Constrained (Gemini HTTP 429)
                                </div>
                                <p className="text-[11px] text-amber-200/90 leading-relaxed">
                                  Multi-agent LLM synthesis was blocked due to provider quota
                                  exhaustion. Verified documentation passages were retrieved
                                  deterministically and preserved below without fabrication.
                                </p>
                              </div>
                            </div>
                          )}

                          {/* Markdown Rendered Answer with Proper Visual Hierarchy */}
                          <div className="text-slate-200 leading-relaxed">
                            <ReactMarkdown
                              remarkPlugins={[remarkGfm]}
                              components={{
                                h1: ({ children }) => (
                                  <h1 className="text-lg sm:text-xl font-bold text-white mt-5 mb-2.5 pb-2 border-b border-slate-800">
                                    {children}
                                  </h1>
                                ),
                                h2: ({ children }) => (
                                  <h2 className="text-base sm:text-lg font-bold text-cyan-300 mt-5 mb-2.5 pb-1.5 border-b border-slate-800/80 flex items-center gap-2 tracking-tight">
                                    {children}
                                  </h2>
                                ),
                                h3: ({ children }) => {
                                  const text = String(children);
                                  const isSources = text.toLowerCase().includes('sources');
                                  return (
                                    <h3
                                      className={`text-sm sm:text-base font-bold text-sky-200 mt-4 mb-2 flex items-center gap-2 tracking-tight ${
                                        isSources ? 'text-teal-300 pt-3 border-t border-slate-800/80' : ''
                                      }`}
                                    >
                                      <span className="w-1.5 h-3.5 rounded-full bg-gradient-to-b from-cyan-400 to-sap-blue shrink-0"></span>
                                      <span>{children}</span>
                                    </h3>
                                  );
                                },
                                p: ({ children }) => (
                                  <p className="text-xs sm:text-sm text-slate-200 leading-relaxed my-2">
                                    {children}
                                  </p>
                                ),
                                ul: ({ children }) => (
                                  <ul className="list-disc pl-5 my-2.5 space-y-1.5 text-xs sm:text-sm text-slate-200 leading-relaxed marker:text-cyan-500">
                                    {children}
                                  </ul>
                                ),
                                ol: ({ children }) => (
                                  <ol className="list-decimal pl-5 my-2.5 space-y-2 text-xs sm:text-sm text-slate-200 leading-relaxed marker:text-cyan-400 marker:font-semibold">
                                    {children}
                                  </ol>
                                ),
                                li: ({ children }) => (
                                  <li className="leading-relaxed pl-1 text-slate-200">
                                    {children}
                                  </li>
                                ),
                                strong: ({ children }) => (
                                  <strong className="font-semibold text-white">
                                    {children}
                                  </strong>
                                ),
                                blockquote: ({ children }) => (
                                  <blockquote className="border-l-2 border-cyan-500/60 pl-3.5 py-1 text-slate-300 italic bg-slate-950/50 rounded-r-lg my-2.5">
                                    {children}
                                  </blockquote>
                                ),
                                code: ({ inline, className, children, ...props }: any) => {
                                  if (inline) {
                                    return (
                                      <code
                                        className="bg-slate-950 px-1.5 py-0.5 rounded font-mono text-xs text-cyan-300 border border-slate-800"
                                        {...props}
                                      >
                                        {children}
                                      </code>
                                    );
                                  }
                                  return (
                                    <pre className="bg-slate-950 p-3.5 rounded-xl border border-slate-800 font-mono text-xs overflow-x-auto text-slate-200 my-3">
                                      <code className={className} {...props}>
                                        {children}
                                      </code>
                                    </pre>
                                  );
                                },
                                a: ({ href, children, ...props }: any) => {
                                  const hrefStr = href || '';
                                  const textStr = String(children);
                                  const isUrlText = textStr.startsWith('http://') || textStr.startsWith('https://');

                                  if (isUrlText) {
                                    let hostAndPath = hrefStr;
                                    try {
                                      const u = new URL(hrefStr);
                                      hostAndPath = `${u.hostname}${
                                        u.pathname.length > 30 ? u.pathname.slice(0, 30) + '...' : u.pathname
                                      }`;
                                    } catch {
                                      // fallback
                                    }

                                    return (
                                      <a
                                        href={href}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="inline-flex items-center gap-1.5 my-0.5 px-2.5 py-0.5 rounded-md bg-slate-950/90 hover:bg-slate-800 border border-slate-800 hover:border-cyan-500/50 text-cyan-300 font-mono text-xs transition-all max-w-full group"
                                        title={hrefStr}
                                        {...props}
                                      >
                                        <BookOpen className="w-3 h-3 text-cyan-400 shrink-0 group-hover:text-cyan-300" />
                                        <span className="truncate max-w-[280px] sm:max-w-[420px]">{hostAndPath}</span>
                                        <ExternalLink className="w-2.5 h-2.5 text-slate-500 group-hover:text-cyan-400 shrink-0 ml-0.5" />
                                      </a>
                                    );
                                  }

                                  return (
                                    <a
                                      href={href}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="inline-flex items-center gap-1 text-cyan-400 hover:text-cyan-300 font-medium underline underline-offset-2 decoration-cyan-500/30 hover:decoration-cyan-300 transition-colors"
                                      {...props}
                                    >
                                      <span>{children}</span>
                                      <ExternalLink className="w-3 h-3 inline shrink-0 opacity-70" />
                                    </a>
                                  );
                                },
                              }}
                            >
                              {msg.content}
                            </ReactMarkdown>
                          </div>

                          {/* Grounded Documentation Passages Card */}
                          {msg.response?.citations && msg.response.citations.length > 0 && (
                            <div className="mt-5 pt-3.5 border-t border-slate-800/80">
                              <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800/85 space-y-2.5">
                                <div className="flex items-center justify-between">
                                  <div className="text-[11px] font-mono text-cyan-400 uppercase tracking-wider flex items-center gap-1.5 font-semibold">
                                    <BookOpen className="w-3.5 h-3.5 text-cyan-400" />
                                    <span>Grounded Documentation Passages ({msg.response.citations.length})</span>
                                  </div>
                                  <span className="text-[10px] text-slate-500 font-mono hidden sm:inline">
                                    Click passage to inspect verified text
                                  </span>
                                </div>

                                <div className="flex flex-wrap gap-2">
                                  {msg.response.citations.map((cit: CitationItem) => {
                                    const matchingEvidence = msg.response?.evidence_payload?.find(
                                      (ev) => ev.evidence_id === cit.evidence_id
                                    );
                                    return (
                                      <button
                                        key={cit.citation_id}
                                        onClick={() =>
                                          matchingEvidence && openEvidenceDetail(matchingEvidence)
                                        }
                                        className="group px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-700/80 hover:border-cyan-500/60 text-xs text-slate-200 transition-all flex items-center gap-2 shadow-sm text-left"
                                        title={`View verified excerpt for [${cit.citation_id}]: ${cit.title}`}
                                      >
                                        <span className="font-mono font-bold text-cyan-400 group-hover:text-cyan-300">
                                          [{cit.citation_id}]
                                        </span>
                                        <span className="truncate max-w-[200px] sm:max-w-[280px] text-slate-300 group-hover:text-white font-medium">
                                          {cit.title || matchingEvidence?.title || cit.evidence_id}
                                        </span>
                                        <ChevronRight className="w-3 h-3 text-slate-500 group-hover:text-cyan-400 shrink-0" />
                                      </button>
                                    );
                                  })}
                                </div>
                              </div>
                            </div>
                          )}

                          {/* Telemetry & Action Bar */}
                          <div className="mt-3 pt-2.5 border-t border-slate-800/60 flex flex-wrap items-center justify-between gap-3 text-xs">
                            <div className="flex items-center gap-2.5">
                              {typeof msg.response?.validation_report?.citation_integrity_ratio ===
                                'number' && (
                                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-emerald-950/60 border border-emerald-500/40 text-emerald-300 text-[11px] font-mono font-medium">
                                  <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                                  <span>
                                    {Math.round(
                                      msg.response.validation_report.citation_integrity_ratio * 100
                                    )}
                                    % Verified
                                  </span>
                                </span>
                              )}

                              {typeof msg.response?.total_latency_ms === 'number' && (
                                <span className="inline-flex items-center gap-1.5 px-2 py-1 rounded-md bg-slate-950/80 border border-slate-800 text-slate-400 text-[11px] font-mono">
                                  <Clock className="w-3 h-3 text-slate-500" />
                                  <span>{(msg.response.total_latency_ms / 1000).toFixed(1)}s</span>
                                </span>
                              )}

                              {msg.response?.answer_status && (
                                <span className="hidden md:inline-flex items-center gap-1 text-[11px] font-mono text-slate-500">
                                  • {msg.response.answer_status.replace(/_/g, ' ')}
                                </span>
                              )}
                            </div>

                            <button
                              onClick={() => navigate('/workflow-canvas')}
                              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-cyan-950/40 hover:bg-cyan-900/60 border border-cyan-800/50 hover:border-cyan-500/60 text-cyan-300 hover:text-cyan-200 text-xs font-medium transition-all group shadow-sm"
                            >
                              <Network className="w-3.5 h-3.5 text-cyan-400 group-hover:scale-110 transition-transform" />
                              <span>Inspect Workflow in Canvas</span>
                              <ArrowRight className="w-3 h-3 text-cyan-400 group-hover:translate-x-0.5 transition-transform" />
                            </button>
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {/* User Avatar */}
                  {msg.role === 'user' && (
                    <div className="w-8 h-8 rounded-xl bg-sap-blue flex items-center justify-center text-white shrink-0 mt-1 shadow-sm">
                      <User className="w-4 h-4" />
                    </div>
                  )}
                </div>
              ))}

              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Floating Chat Input Bar */}
        <div className="border-t border-slate-800/90 bg-slate-900/95 backdrop-blur p-3 sm:p-4 shrink-0 shadow-xl">
          <form onSubmit={handleSubmit} className="max-w-4xl mx-auto flex items-end gap-2.5">
            <div className="relative flex-1 bg-slate-950 border border-slate-800 rounded-2xl shadow-inner focus-within:border-cyan-500/80 focus-within:ring-1 focus-within:ring-cyan-500/30 transition-all">
              <textarea
                ref={inputRef}
                value={inputQuery}
                onChange={(e) => setInputQuery(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask procedural or architectural SAP Utilities question... (e.g. reverse contract, move-in reversal)"
                rows={1}
                disabled={isExecuting}
                className="w-full pl-4 pr-14 py-3 bg-transparent text-xs sm:text-sm text-slate-100 placeholder-slate-500 focus:outline-none resize-none max-h-36 min-h-[46px]"
              />
              <div className="absolute right-3.5 bottom-3 text-[10px] text-slate-600 font-mono hidden sm:block pointer-events-none">
                ↵ Enter
              </div>
            </div>

            {isExecuting ? (
              <button
                type="button"
                onClick={cancelCurrentRun}
                className="p-3 bg-rose-950/80 hover:bg-rose-900 border border-rose-500/50 text-rose-300 rounded-2xl flex items-center justify-center transition-colors shadow-sm"
                title="Cancel ongoing execution"
              >
                <StopCircle className="w-4 h-4" />
              </button>
            ) : (
              <button
                type="submit"
                disabled={!inputQuery.trim()}
                className="p-3 bg-gradient-to-tr from-sap-blue to-cyan-600 hover:from-sap-accent hover:to-cyan-500 disabled:opacity-40 disabled:hover:from-sap-blue disabled:hover:to-cyan-600 text-white rounded-2xl flex items-center justify-center transition-all shadow-md shadow-sap-blue/20"
                title="Send query to agentic workflow"
              >
                <Send className="w-4 h-4" />
              </button>
            )}
          </form>
          <div className="max-w-4xl mx-auto mt-1.5 flex items-center justify-between text-[11px] text-slate-500 px-1">
            <span>Shift + Enter for new line</span>
            <span className="font-mono">Independent Semantic Retrieval • CrewAI v2</span>
          </div>
        </div>
      </div>

      {/* Right Slide-over Evidence / Citation Inspector Drawer */}
      {isEvidenceDrawerOpen && selectedEvidence && (
        <div className="w-80 sm:w-96 md:w-[440px] bg-slate-900 border-l border-slate-800 flex flex-col h-full shadow-2xl z-20 shrink-0">
          <div className="p-4 border-b border-slate-800 flex items-start justify-between bg-slate-950/80 shrink-0">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <span className="text-[10px] font-mono text-cyan-400 font-bold px-1.5 py-0.5 rounded bg-cyan-950/60 border border-cyan-500/40">
                  {selectedEvidence.evidence_id || `CHUNK #${selectedEvidence.chunk_id}`}
                </span>
                <span className="text-[10px] font-mono text-slate-400">
                  Doc #{selectedEvidence.document_id}
                </span>
              </div>
              <h3 className="text-sm font-bold text-slate-100 line-clamp-2">
                {selectedEvidence.title}
              </h3>
            </div>
            <button
              onClick={closeEvidenceDrawer}
              className="p-1 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-slate-200 transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto p-4 space-y-4 text-xs">
            {/* Breadcrumb & Section */}
            {selectedEvidence.breadcrumb && (
              <div className="space-y-1">
                <span className="text-[10px] font-mono text-slate-500 uppercase block">
                  Documentation Breadcrumb
                </span>
                <p className="text-[11px] text-slate-400 font-mono bg-slate-950 p-2.5 rounded-lg border border-slate-800 leading-relaxed">
                  {selectedEvidence.breadcrumb}
                </p>
              </div>
            )}

            {/* Canonical Link */}
            {selectedEvidence.canonical_url && (
              <div>
                <a
                  href={selectedEvidence.canonical_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 text-xs text-cyan-400 hover:text-cyan-300 font-medium transition-colors"
                >
                  <ExternalLink className="w-3.5 h-3.5" />
                  <span>Open SAP Documentation Source</span>
                </a>
              </div>
            )}

            {/* Excerpt Passage */}
            <div className="space-y-1">
              <span className="text-[10px] font-mono text-slate-500 uppercase block">
                Verified Passage Content
              </span>
              <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 text-xs leading-relaxed whitespace-pre-wrap font-sans">
                {selectedEvidence.clean_body ||
                  selectedEvidence.clean_excerpt ||
                  selectedEvidence.content}
              </div>
            </div>

            {/* Retrieval Telemetry */}
            <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 grid grid-cols-2 gap-2 text-[10px] font-mono text-slate-400">
              <div>
                <span className="block text-slate-500">Cosine Distance:</span>
                <span className="text-slate-200 font-bold">
                  {selectedEvidence.cosine_distance.toFixed(4)}
                </span>
              </div>
              <div>
                <span className="block text-slate-500">Similarity:</span>
                <span className="text-cyan-400 font-bold">
                  {(selectedEvidence.similarity_score * 100).toFixed(1)}%
                </span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
