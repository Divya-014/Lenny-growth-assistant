import React, { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import { 
  Plus, 
  MessageSquare, 
  Send, 
  Sparkles, 
  Code, 
  Eye, 
  Download, 
  Layers, 
  BookOpen, 
  ChevronRight
} from 'lucide-react';



interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  model_used?: string;
  created_at?: string;
  retrieved_sources?: any[];
}

interface Session {
  id: string;
  title: string;
  created_at?: string;
}

interface Artifact {
  type: 'html' | 'markdown';
  title: string;
  content: string;
}

export default function App() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [provider, setProvider] = useState<'openai' | 'anthropic' | 'ollama'>('openai');
  const [loading, setLoading] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  // Artifact Viewer state
  const [activeArtifact, setActiveArtifact] = useState<Artifact | null>(null);
  const [artifactTab, setArtifactTab] = useState<'preview' | 'code'>('preview');

  // Loader state step transitions (ChatGPT/Claude style)
  const [loaderStep, setLoaderStep] = useState<'searching' | 'generating'>('searching');
  const loaderTimerRef = useRef<number | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);


  // Fetch all chat sessions on mount
  useEffect(() => {
    fetchSessions();
  }, []);

  // Fetch messages when active session changes
  useEffect(() => {
    if (activeSessionId) {
      fetchMessages(activeSessionId);
    } else {
      setMessages([]);
      setActiveArtifact(null);
    }
  }, [activeSessionId]);

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    detectArtifactInMessages();
  }, [messages]);

  const fetchSessions = async () => {
    try {
      const response = await fetch('/sessions');
      if (response.ok) {
        const data = await response.json();
        setSessions(data);
      }
    } catch (e) {
      console.error('Error fetching sessions:', e);
    }
  };

  const fetchMessages = async (sessionId: string) => {
    try {
      const response = await fetch(`/sessions/${sessionId}/messages`);
      if (response.ok) {
        const data = await response.json();
        // Backend returns database message objects: map to state messages
        const formatted = data.map((msg: any) => ({
          id: msg.id,
          role: msg.role as 'user' | 'assistant',
          content: msg.content,
          model_used: msg.model_used
        }));
        setMessages(formatted);
      }
    } catch (e) {
      console.error('Error fetching messages:', e);
    }
  };

  // Helper to detect and extract artifacts from the last message
  const detectArtifactInMessages = () => {
    if (messages.length === 0) {
      setActiveArtifact(null);
      return;
    }
    const lastMsg = messages[messages.length - 1];
    if (lastMsg.role === 'assistant') {
      const artifact = parseArtifact(lastMsg.content);
      if (artifact) {
        setActiveArtifact(artifact);
      } else {
        // If it's a normal chat message (no artifact in content), but we had one before,
        // let's keep showing the previous one or clear it?
        // Claude typically keeps the last rendered artifact active until a new session starts
        // or a new artifact is generated. But requirements say:
        // "If normal chat: Hide the Artifact Viewer."
        // So if the last message does NOT contain an artifact, we hide it!
        setActiveArtifact(null);
      }
    } else {
      // If user is typing or waiting, keep current artifact visible or hide?
      // Hide if there's no assistant output representing an artifact.
    }
  };

  const parseArtifact = (content: string): Artifact | null => {
    // 1. Detect custom XML-style artifact tag
    const xmlRegex = /<artifact\s+[^>]*?type=["'](text\/html|html|markdown|text\/markdown)["'][^>]*?title=["']([^"']+)["'][^>]*?>([\s\S]*?)<\/artifact>/i;
    const xmlMatch = content.match(xmlRegex);
    if (xmlMatch) {
      const rawType = xmlMatch[1].toLowerCase();
      const type = rawType.includes('html') ? 'html' : 'markdown';
      return {
        type,
        title: xmlMatch[2],
        content: xmlMatch[3].trim()
      };
    }

    // 2. Detect HTML code block
    const htmlBlockRegex = /```html\s*([\s\S]*?)```/i;
    const htmlMatch = content.match(htmlBlockRegex);
    if (htmlMatch) {
      return {
        type: 'html',
        title: 'HTML Preview',
        content: htmlMatch[1].trim()
      };
    }

    // 3. Detect Markdown code block
    const mdBlockRegex = /```markdown\s*([\s\S]*?)```/i;
    const mdMatch = content.match(mdBlockRegex);
    if (mdMatch) {
      return {
        type: 'markdown',
        title: 'Markdown Document',
        content: mdMatch[1].trim()
      };
    }

    // 4. Detect raw HTML structures (<!DOCTYPE html> or <html>)
    if (content.includes('<!DOCTYPE html>') || (content.includes('<html') && content.includes('</html>'))) {
      return {
        type: 'html',
        title: 'HTML Page Artifact',
        content: content.trim()
      };
    }

    return null;
  };

  const generateSessionId = () => {
    return 'session_' + Math.random().toString(36).substr(2, 9);
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim() || loading) return;

    const queryText = inputText;
    setInputText('');
    setLoading(true);

    // Resolve active session ID, or create one deterministically
    const targetSessionId = activeSessionId || generateSessionId();

    // Create user message model locally to append to UI immediately
    const userMessage: Message = {
      id: 'msg_' + Math.random().toString(36).substr(2, 9),
      role: 'user',
      content: queryText
    };

    setMessages(prev => [...prev, userMessage]);

    // If it's a new chat, temporarily activate the session locally
    if (!activeSessionId) {
      setActiveSessionId(targetSessionId);
    }

    // Set up step animations
    setLoaderStep('searching');
    if (loaderTimerRef.current) {
      window.clearTimeout(loaderTimerRef.current);
    }
    loaderTimerRef.current = window.setTimeout(() => {
      setLoaderStep('generating');
    }, 1500);

    try {
      const response = await fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: targetSessionId,
          message: queryText,
          provider: provider
        })
      });

      if (response.ok) {
        const data = await response.json();
        // Append LLM response to messages
        const assistantMessage: Message = {
          id: 'msg_' + Math.random().toString(36).substr(2, 9),
          role: 'assistant',
          content: data.response,
          model_used: provider,
          retrieved_sources: data.retrieved_sources
        };
        setMessages(prev => [...prev, assistantMessage]);

        // Refresh sessions sidebar list
        fetchSessions();
      } else {
        const errData = await response.json().catch(() => ({}));
        const errorMsg: Message = {
          id: 'msg_err_' + Date.now(),
          role: 'assistant',
          content: `⚠️ Failed to get response: ${errData.detail || 'Server error'}`
        };
        setMessages(prev => [...prev, errorMsg]);
      }
    } catch (e) {
      console.error('Error sending message:', e);
      const networkErrorMsg: Message = {
        id: 'msg_err_' + Date.now(),
        role: 'assistant',
        content: `⚠️ Network error: Could not reach the backend. Make sure the FastAPI server is running.`
      };
      setMessages(prev => [...prev, networkErrorMsg]);
    } finally {
      if (loaderTimerRef.current) {
        window.clearTimeout(loaderTimerRef.current);
        loaderTimerRef.current = null;
      }
      setLoading(false);
    }

  };

  const startNewChat = () => {
    setActiveSessionId(null);
    setMessages([]);
    setActiveArtifact(null);
  };

  const handleDownloadArtifact = () => {
    if (!activeArtifact) return;
    const element = document.createElement("a");
    const file = new Blob([activeArtifact.content], {type: 'text/plain'});
    element.href = URL.createObjectURL(file);
    element.download = `${activeArtifact.title.replace(/\s+/g, '_').toLowerCase()}.${activeArtifact.type === 'html' ? 'html' : 'md'}`;
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  return (
    <div className="flex h-screen w-screen bg-slate-950 overflow-hidden text-slate-100 font-sans">
      
      {/* 1. Sidebar - Chat History */}
      <div 
        className={`${
          sidebarOpen ? 'w-64' : 'w-0'
        } transition-all duration-300 ease-in-out border-r border-slate-800/80 bg-slate-900/60 backdrop-blur-md flex flex-col z-10 overflow-hidden`}
      >
        {/* Sidebar Header */}
        <div className="p-4 border-b border-slate-800/80 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-indigo-400" />
            <span className="font-bold text-sm bg-gradient-to-r from-indigo-400 to-emerald-400 bg-clip-text text-transparent">Lenny Growth</span>
          </div>
          <button 
            onClick={startNewChat}
            className="p-1.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-slate-100 transition-colors"
            title="New Chat"
          >
            <Plus className="w-4 h-4" />
          </button>
        </div>

        {/* New Chat Button */}
        <div className="p-3">
          <button
            onClick={startNewChat}
            className="w-full flex items-center justify-center gap-2 py-2 px-3 bg-gradient-to-r from-indigo-600 to-indigo-700 hover:from-indigo-500 hover:to-indigo-600 text-white text-xs font-semibold rounded-lg shadow-md shadow-indigo-900/30 transition-all duration-200"
          >
            <Plus className="w-4 h-4" />
            New Chat
          </button>
        </div>

        {/* Chat List */}
        <div className="flex-1 overflow-y-auto px-2 space-y-1">
          {sessions.length === 0 ? (
            <div className="text-center py-8 text-xs text-slate-500">No past conversations</div>
          ) : (
            sessions.map((session) => (
              <button
                key={session.id}
                onClick={() => setActiveSessionId(session.id)}
                className={`w-full text-left flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-xs transition-all duration-150 ${
                  activeSessionId === session.id 
                    ? 'bg-slate-800 text-slate-100 font-medium border-l-2 border-indigo-500' 
                    : 'text-slate-400 hover:bg-slate-900/60 hover:text-slate-200'
                }`}
              >
                <MessageSquare className="w-4 h-4 flex-shrink-0 opacity-60" />
                <span className="truncate">{session.title}</span>
              </button>
            ))
          )}
        </div>

        {/* Sidebar Footer */}
        <div className="p-3 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-500">
          <div className="flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 pulse-soft"></span>
            Connected
          </div>
          <span className="text-[10px] text-slate-600 font-mono">v1.0.0</span>
        </div>
      </div>

      {/* Toggle Sidebar Button (Floating) */}
      <button
        onClick={() => setSidebarOpen(!sidebarOpen)}
        className="fixed bottom-4 left-4 z-20 p-2 bg-slate-900 border border-slate-800 hover:bg-slate-800 rounded-lg text-slate-400 hover:text-slate-200 shadow-lg md:flex items-center justify-center transition-all duration-200"
        title="Toggle Sidebar"
      >
        <ChevronRight className={`w-4 h-4 transition-transform duration-200 ${sidebarOpen ? 'rotate-180' : ''}`} />
      </button>

      {/* 2. Main Layout Container: Splits Chat and Artifact Panel */}
      <div className="flex-1 flex overflow-hidden">
        
        {/* Left Panel: Chat Interface */}
        <div className="flex-1 flex flex-col h-full bg-slate-950 relative overflow-hidden">
          {/* Top Navbar */}
          <div className="h-14 border-b border-slate-900 flex items-center justify-between px-6 bg-slate-950/80 backdrop-blur-md">
            <div className="flex items-center gap-3">
              <BookOpen className="w-4 h-4 text-emerald-400" />
              <h1 className="text-xs font-semibold text-slate-200 uppercase tracking-wider">
                {activeSessionId ? 'Active Workspace' : 'New Session'}
              </h1>
            </div>
            
            {/* LLM Provider Switcher */}
            <div className="flex items-center gap-1.5 bg-slate-900/80 p-0.5 rounded-lg border border-slate-800/60">
              {(['openai', 'anthropic', 'ollama'] as const).map((prov) => (
                <button
                  key={prov}
                  onClick={() => setProvider(prov)}
                  className={`px-3 py-1 text-[10px] font-semibold rounded-md transition-all duration-150 uppercase tracking-wider ${
                    provider === prov
                      ? 'bg-indigo-600 text-white shadow-sm'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'
                  }`}
                >
                  {prov}
                </button>
              ))}
            </div>
          </div>

          {/* Chat Messages Log Scrollable Container */}
          <div className="flex-1 overflow-y-auto px-6 py-8 space-y-6">
            {messages.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-center px-4 max-w-lg mx-auto">
                <div className="w-12 h-12 rounded-2xl bg-indigo-500/10 flex items-center justify-center border border-indigo-500/20 mb-6">
                  <Sparkles className="w-6 h-6 text-indigo-400" />
                </div>
                <h2 className="text-lg font-bold text-slate-200 mb-2">Lenny Growth Assistant</h2>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Ask growth strategy questions, design onboarding experiments, or request formatted documents using indexed podcast transcripts.
                </p>
                <div className="grid grid-cols-2 gap-2 w-full mt-8">
                  <button 
                    onClick={() => setInputText("What is a growth loop and how do I build one?")}
                    className="p-3 text-left rounded-xl bg-slate-900/60 border border-slate-800/40 hover:border-slate-700/60 hover:bg-slate-900 transition-all text-xs text-slate-300"
                  >
                    💡 Growth loops overview
                  </button>
                  <button 
                    onClick={() => setInputText("Generate a markdown artifact comparing viral loops vs content loops.")}
                    className="p-3 text-left rounded-xl bg-slate-900/60 border border-slate-800/40 hover:border-slate-700/60 hover:bg-slate-900 transition-all text-xs text-slate-300"
                  >
                    📄 Markdown Loop comparisons
                  </button>
                  <button 
                    onClick={() => setInputText("Generate an HTML page with a sleek Conversion Onboarding Funnel calculator dashboard.")}
                    className="p-3 text-left rounded-xl bg-slate-900/60 border border-slate-800/40 hover:border-slate-700/60 hover:bg-slate-900 transition-all text-xs text-slate-300"
                  >
                    🛠️ HTML Calculator tool
                  </button>
                  <button 
                    onClick={() => setInputText("What are benchmark metrics for B2B SaaS retention?")}
                    className="p-3 text-left rounded-xl bg-slate-900/60 border border-slate-800/40 hover:border-slate-700/60 hover:bg-slate-900 transition-all text-xs text-slate-300"
                  >
                    📊 Retention benchmarks
                  </button>
                </div>
              </div>
            ) : (
              messages.map((msg) => (
                <div 
                  key={msg.id}
                  className={`flex flex-col max-w-3xl mx-auto ${
                    msg.role === 'user' ? 'items-end' : 'items-start'
                  }`}
                >
                  {/* Bubble wrapper */}
                  <div className={`p-4 rounded-2xl text-sm leading-relaxed ${
                    msg.role === 'user'
                      ? 'bg-indigo-600 text-white rounded-br-none max-w-[85%]'
                      : 'bg-slate-900/60 border border-slate-800/80 text-slate-200 rounded-bl-none w-full shadow-lg'
                  }`}>
                    {/* Render message contents */}
                    {msg.role === 'user' ? (
                      <p className="whitespace-pre-wrap">{msg.content}</p>
                    ) : (
                      <div className="prose prose-invert max-w-none text-slate-200 text-xs md:text-sm">
                        <ReactMarkdown>{msg.content}</ReactMarkdown>
                      </div>
                    )}

                    {/* Metadata tags */}
                    {msg.role === 'assistant' && msg.model_used && (
                      <div className="mt-3 flex items-center justify-between text-[10px] text-slate-500 border-t border-slate-850 pt-2 font-mono">
                        <span>Engine: {msg.model_used.toUpperCase()}</span>
                        {msg.retrieved_sources && msg.retrieved_sources.length > 0 && (
                          <span className="bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-1.5 py-0.5 rounded text-[9px]">
                            Cited: {msg.retrieved_sources.length} sources
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}
            
            {/* Typing Loader */}
            {loading && (
              <div className="flex flex-col max-w-3xl mx-auto items-start w-full">
                <div className="p-4 rounded-2xl rounded-bl-none bg-slate-900/60 border border-slate-800/80 text-slate-300 flex items-start gap-3.5 shadow-lg max-w-[85%]">
                  <div className="flex items-center justify-center w-5 h-5 mt-0.5 flex-shrink-0">
                    <span className="relative flex h-2.5 w-2.5">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
                      <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-indigo-500"></span>
                    </span>
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <p className={`text-xs transition-all duration-300 font-medium ${
                      loaderStep === 'searching' ? 'opacity-100 text-indigo-300' : 'opacity-40 text-slate-400'
                    }`}>
                      🔍 Searching Lenny's podcast knowledge base...
                    </p>
                    <p className={`text-xs transition-all duration-300 font-medium ${
                      loaderStep === 'generating' ? 'opacity-100 text-indigo-300' : 'opacity-0 h-0 overflow-hidden'
                    }`}>
                      🧠 Generating grounded response...
                    </p>
                  </div>
                </div>
              </div>
            )}

            
            <div ref={messagesEndRef} />
          </div>

          {/* Bottom Chat Input Form */}
          <div className="p-6 border-t border-slate-900 bg-slate-950/80 backdrop-blur-md">
            <form onSubmit={handleSendMessage} className="max-w-3xl mx-auto relative flex items-center">
              <input
                type="text"
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                placeholder="Ask Lenny Growth Assistant..."
                disabled={loading}
                className="w-full pl-5 pr-14 py-3 bg-slate-900/80 border border-slate-800/60 text-slate-100 rounded-xl text-xs md:text-sm focus:border-indigo-500/80 focus:ring-1 focus:ring-indigo-500/40 focus:outline-none transition-all disabled:opacity-60 placeholder:text-slate-500"
              />
              <button
                type="submit"
                disabled={!inputText.trim() || loading}
                className="absolute right-2 p-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg transition-all disabled:bg-slate-800 disabled:text-slate-500 cursor-pointer disabled:cursor-not-allowed"
              >
                <Send className="w-4 h-4" />
              </button>
            </form>
            <p className="text-[10px] text-slate-600 text-center mt-3">
              Uses RAG (vector similarity lookup over Lenny's Podcast transcripts). Answers are restricted exclusively to indexed sources.
            </p>
          </div>
        </div>

        {/* Right Panel: Artifact Viewer */}
        <div 
          className={`${
            activeArtifact ? 'w-[50%] opacity-100' : 'w-0 opacity-0 pointer-events-none'
          } transition-all duration-300 ease-in-out border-l border-slate-900 bg-slate-900/40 backdrop-blur-sm flex flex-col h-full overflow-hidden`}
        >
          {activeArtifact && (
            <>
              {/* Artifact Viewer Header */}
              <div className="h-14 border-b border-slate-900 flex items-center justify-between px-5 bg-slate-950/80 backdrop-blur-md">
                <div className="flex items-center gap-2.5">
                  <div className="p-1 rounded-md bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                    <Layers className="w-4 h-4" />
                  </div>
                  <div>
                    <h2 className="text-xs font-bold text-slate-200 truncate max-w-[200px]">
                      {activeArtifact.title}
                    </h2>
                    <p className="text-[9px] text-slate-500 uppercase tracking-wider">
                      Type: {activeArtifact.type.toUpperCase()}
                    </p>
                  </div>
                </div>

                {/* Tabs & Controls */}
                <div className="flex items-center gap-3">
                  {/* Switch Tab (Only relevant for HTML) */}
                  {activeArtifact.type === 'html' && (
                    <div className="flex bg-slate-900 p-0.5 rounded-lg border border-slate-800">
                      <button
                        onClick={() => setArtifactTab('preview')}
                        className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[10px] font-semibold transition-all ${
                          artifactTab === 'preview'
                            ? 'bg-slate-800 text-indigo-400 shadow-sm'
                            : 'text-slate-400 hover:text-slate-200'
                        }`}
                      >
                        <Eye className="w-3.5 h-3.5" />
                        Preview
                      </button>
                      <button
                        onClick={() => setArtifactTab('code')}
                        className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[10px] font-semibold transition-all ${
                          artifactTab === 'code'
                            ? 'bg-slate-800 text-indigo-400 shadow-sm'
                            : 'text-slate-400 hover:text-slate-200'
                        }`}
                      >
                        <Code className="w-3.5 h-3.5" />
                        Code
                      </button>
                    </div>
                  )}

                  {/* Action buttons */}
                  <button
                    onClick={handleDownloadArtifact}
                    className="p-1.5 rounded-lg border border-slate-800 hover:bg-slate-800 text-slate-400 hover:text-slate-200 transition-all"
                    title="Download Code File"
                  >
                    <Download className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {/* Artifact Viewer Body */}
              <div className="flex-1 overflow-auto bg-slate-950 relative">
                
                {/* 1. Preview Mode */}
                {artifactTab === 'preview' && (
                  <>
                    {activeArtifact.type === 'html' ? (
                      /* Sandboxed Web Preview Iframe */
                      <iframe
                        srcDoc={activeArtifact.content}
                        sandbox="allow-scripts"
                        className="w-full h-full border-none bg-white"
                        title={activeArtifact.title}
                      />
                    ) : (
                      /* Markdown Preview Pane */
                      <div className="p-8 max-w-none text-slate-300 prose prose-invert prose-headings:text-slate-100 prose-strong:text-slate-100 prose-a:text-indigo-400 prose-code:bg-slate-900 prose-code:p-0.5 prose-code:rounded">
                        <ReactMarkdown>{activeArtifact.content}</ReactMarkdown>
                      </div>
                    )}
                  </>
                )}

                {/* 2. Code Mode (Show source text code block) */}
                {artifactTab === 'code' && (
                  <pre className="p-6 text-xs text-indigo-300 font-mono overflow-auto h-full bg-slate-950/60 leading-relaxed">
                    <code>{activeArtifact.content}</code>
                  </pre>
                )}
              </div>
            </>
          )}
        </div>

      </div>
    </div>
  );
}
