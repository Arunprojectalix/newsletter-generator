import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, FileText, Plus, Trash2, Edit3, Search, Globe, History, RefreshCw } from 'lucide-react';

interface ChatMessage {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  action_taken?: string;
  target?: string;
  reasoning?: string;
  confidence?: number;
  result?: any;
}

interface NewsletterState {
  content: any;
  events: any[];
  parameters: any;
  created_at: string;
}

interface ContextChatResponse {
  success: boolean;
  action_taken: string;
  target: string;
  reasoning: string;
  result: any;
  confidence: number;
  conversation_history: any[];
  newsletter_state?: NewsletterState;
  error?: string;
}

const ContextAwareChatInterface: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [newsletterState, setNewsletterState] = useState<NewsletterState | null>(null);
  const [showNewsletterPreview, setShowNewsletterPreview] = useState(false);
  const [conversationHistory, setConversationHistory] = useState<any[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      type: 'user',
      content: inputMessage,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      const response = await fetch('/api/v1/context-chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: inputMessage,
          context: {
            postcode: 'TS1 3BA', // Default postcode, can be made dynamic
            region: 'UK'
          }
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: ContextChatResponse = await response.json();

      // Update newsletter state if provided
      if (data.newsletter_state) {
        setNewsletterState(data.newsletter_state);
      }

      // Update conversation history
      if (data.conversation_history) {
        setConversationHistory(data.conversation_history);
      }

      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: data.success ? 
          (data.result.response || data.result.message || JSON.stringify(data.result, null, 2)) :
          (data.error || 'An error occurred'),
        timestamp: new Date(),
        action_taken: data.action_taken,
        target: data.target,
        reasoning: data.reasoning,
        confidence: data.confidence,
        result: data.result
      };

      setMessages(prev => [...prev, assistantMessage]);

    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: `Error: ${error instanceof Error ? error.message : 'Unknown error occurred'}`,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const resetContext = async () => {
    try {
      await fetch('/api/v1/reset-context', { method: 'POST' });
      setMessages([]);
      setNewsletterState(null);
      setConversationHistory([]);
    } catch (error) {
      console.error('Error resetting context:', error);
    }
  };

  const getActionIcon = (action: string) => {
    switch (action) {
      case 'generate_newsletter': return <FileText className="w-4 h-4" />;
      case 'add_events': return <Plus className="w-4 h-4" />;
      case 'delete_events': return <Trash2 className="w-4 h-4" />;
      case 'change_tone': return <Edit3 className="w-4 h-4" />;
      case 'search_events': return <Search className="w-4 h-4" />;
      case 'search_web': return <Globe className="w-4 h-4" />;
      default: return <Bot className="w-4 h-4" />;
    }
  };

  const getTargetColor = (target: string) => {
    switch (target) {
      case 'newsletter': return 'bg-green-100 text-green-800';
      case 'chat': return 'bg-blue-100 text-blue-800';
      case 'system': return 'bg-purple-100 text-purple-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const quickActions = [
    { label: 'Generate Newsletter', message: 'Generate a weekly newsletter for families with children in social housing in TS1 3BA' },
    { label: 'Add More Events', message: 'Add more events to the newsletter' },
    { label: 'Change Tone to Casual', message: 'Change the newsletter tone to casual and friendly' },
    { label: 'Change Tone to Professional', message: 'Change the newsletter tone to professional and informative' },
    { label: 'Delete Expensive Events', message: 'Delete any events that cost more than £5' },
    { label: 'Search for Indoor Activities', message: 'Search for indoor family activities for rainy days' },
  ];

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="bg-white border-b border-gray-200 p-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-xl font-semibold text-gray-900">Context-Aware AI Assistant</h1>
              <p className="text-sm text-gray-600">
                Generate newsletters, customize content, and manage events with intelligent reasoning
              </p>
            </div>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setShowNewsletterPreview(!showNewsletterPreview)}
                className="px-3 py-2 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700 flex items-center space-x-1"
                disabled={!newsletterState}
              >
                <FileText className="w-4 h-4" />
                <span>Newsletter</span>
              </button>
              <button
                onClick={resetContext}
                className="px-3 py-2 text-sm bg-gray-600 text-white rounded-md hover:bg-gray-700 flex items-center space-x-1"
              >
                <RefreshCw className="w-4 h-4" />
                <span>Reset</span>
              </button>
            </div>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 && (
            <div className="text-center py-8">
              <Bot className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">Welcome to Context-Aware AI</h3>
              <p className="text-gray-600 mb-6">
                I can help you generate newsletters, manage events, and customize content with intelligent reasoning.
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2 max-w-2xl mx-auto">
                {quickActions.map((action, index) => (
                  <button
                    key={index}
                    onClick={() => setInputMessage(action.message)}
                    className="p-3 text-left bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    <span className="text-sm font-medium text-gray-900">{action.label}</span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-3xl rounded-lg p-4 ${
                  message.type === 'user'
                    ? 'bg-blue-600 text-white'
                    : 'bg-white border border-gray-200'
                }`}
              >
                <div className="flex items-start space-x-3">
                  <div className="flex-shrink-0">
                    {message.type === 'user' ? (
                      <User className="w-6 h-6" />
                    ) : (
                      <Bot className="w-6 h-6 text-blue-600" />
                    )}
                  </div>
                  <div className="flex-1">
                    <div className="prose prose-sm max-w-none">
                      <pre className="whitespace-pre-wrap font-sans">{message.content}</pre>
                    </div>
                    
                    {/* AI Action Details */}
                    {message.type === 'assistant' && message.action_taken && (
                      <div className="mt-3 pt-3 border-t border-gray-100">
                        <div className="flex items-center space-x-2 mb-2">
                          {getActionIcon(message.action_taken)}
                          <span className="text-sm font-medium text-gray-700">
                            Action: {message.action_taken.replace('_', ' ')}
                          </span>
                          <span className={`px-2 py-1 text-xs rounded-full ${getTargetColor(message.target || '')}`}>
                            {message.target}
                          </span>
                          {message.confidence && (
                            <span className="text-xs text-gray-500">
                              {Math.round(message.confidence * 100)}% confidence
                            </span>
                          )}
                        </div>
                        {message.reasoning && (
                          <p className="text-sm text-gray-600 italic">
                            Reasoning: {message.reasoning}
                          </p>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-white border border-gray-200 rounded-lg p-4">
                <div className="flex items-center space-x-3">
                  <Bot className="w-6 h-6 text-blue-600" />
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                    <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                  </div>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="bg-white border-t border-gray-200 p-4">
          <div className="flex space-x-4">
            <div className="flex-1">
              <textarea
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ask me to generate newsletters, add events, change tone, or anything else..."
                className="w-full p-3 border border-gray-300 rounded-lg resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                rows={2}
                disabled={isLoading}
              />
            </div>
            <button
              onClick={sendMessage}
              disabled={!inputMessage.trim() || isLoading}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
            >
              <Send className="w-4 h-4" />
              <span>Send</span>
            </button>
          </div>
        </div>
      </div>

      {/* Newsletter Preview Sidebar */}
      {showNewsletterPreview && newsletterState && (
        <div className="w-96 bg-white border-l border-gray-200 overflow-y-auto">
          <div className="p-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">Newsletter Preview</h2>
            <p className="text-sm text-gray-600">
              {newsletterState.events.length} events • Created {new Date(newsletterState.created_at).toLocaleDateString()}
            </p>
          </div>
          <div className="p-4">
            <div className="prose prose-sm max-w-none">
              <pre className="whitespace-pre-wrap text-sm">
                {JSON.stringify(newsletterState.content, null, 2)}
              </pre>
            </div>
          </div>
        </div>
      )}

      {/* Conversation History Sidebar */}
      {conversationHistory.length > 0 && (
        <div className="w-80 bg-gray-50 border-l border-gray-200 overflow-y-auto">
          <div className="p-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900 flex items-center space-x-2">
              <History className="w-5 h-5" />
              <span>History</span>
            </h2>
          </div>
          <div className="p-4 space-y-3">
            {conversationHistory.map((item, index) => (
              <div key={index} className="bg-white p-3 rounded-lg border border-gray-200">
                <div className="flex items-center space-x-2 mb-1">
                  {getActionIcon(item.action_taken)}
                  <span className="text-sm font-medium text-gray-700">
                    {item.action_taken.replace('_', ' ')}
                  </span>
                </div>
                <p className="text-xs text-gray-600 truncate">
                  {item.user_message}
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  {new Date(item.timestamp).toLocaleTimeString()}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default ContextAwareChatInterface; 