import React, { useState, useEffect } from 'react';
import { 
  ChatService, 
  AIReasoningChatRequest,
  AIReasoningChatResponse
} from '../../services/chatService';

interface ChatInterfaceProps {
  newsletterId: string;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ newsletterId }) => {
  const [messages, setMessages] = useState<Array<{
    id: string;
    text: string;
    sender: 'user' | 'ai';
    timestamp: Date;
    functionCalls?: Array<any>;
    reasoning?: string;
  }>>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [conversationHistory, setConversationHistory] = useState<Array<{role: string; content: string}>>([]);

  const chatService = new ChatService();

  useEffect(() => {
    // Add welcome message
    setMessages([
      {
        id: '1',
        text: "Hi! I'm your AI newsletter assistant with GPT function calling! I can search the web, find events, customize newsletters, and much more. Try asking me something like 'find events in London' or 'search for AI news'.",
        sender: 'ai' as const,
        timestamp: new Date(),
      },
    ]);
  }, []);

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage = {
      id: Date.now().toString(),
      text: inputValue,
      sender: 'user' as const,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      // Use AI Chat with GPT Function Calling and Reasoning
      const aiRequest: AIReasoningChatRequest = {
        message: inputValue,
        newsletter_id: newsletterId,
        conversation_history: conversationHistory
      };

      const response: AIReasoningChatResponse = await chatService.aiChatWithReasoning(aiRequest);

      const aiMessage = {
        id: (Date.now() + 1).toString(),
        text: response.message,
        sender: 'ai' as const,
        timestamp: new Date(),
        functionCalls: response.function_calls,
        reasoning: response.reasoning
      };

      setMessages(prev => [...prev, aiMessage]);
      setConversationHistory(response.conversation_history);

    } catch (error) {
      console.error('Chat error:', error);
      const errorMessage = {
        id: (Date.now() + 1).toString(),
        text: `Error: ${error instanceof Error ? error.message : 'Unknown error occurred'}`,
        sender: 'ai' as const,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };



  const addResultMessage = (message: string) => {
    const resultMessage = {
      id: Date.now().toString(),
      text: message,
      sender: 'ai' as const,
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, resultMessage]);
  };

  const executeQuickAction = async (actionType: string) => {
    setIsLoading(true);
    
    try {
      let result;
      let message = '';
      
      switch (actionType) {
        case 'search_web':
          result = await chatService.searchWeb('best restaurants around Granary Square London');
          message = `Found ${result.length} restaurant recommendations`;
          break;
          
        case 'find_events':
          result = await chatService.searchEvents('TS13NE');
          message = `Found ${result.length} upcoming events`;
          break;
          
        case 'get_weather':
          result = await chatService.getRealTimeInfo('London weather today', 'weather');
          message = `Weather information for London`;
          break;
          
        case 'generate_content':
          result = await chatService.generateContent('article', 'community events', 'friendly');
          message = 'Generated newsletter content about community events';
          break;
          
        default:
          message = 'Unknown action';
      }
      
      addResultMessage(message);
    } catch (error) {
      addResultMessage('Quick action failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="chat-interface" style={{ maxWidth: '800px', margin: '0 auto', padding: '20px' }}>
      <div className="chat-header" style={{ marginBottom: '20px' }}>
        <h2>🤖 AI Assistant with GPT Function Calling</h2>
        <p>Ask me anything - I can search the web, find events, customize newsletters, and more!</p>
        <div className="quick-actions" style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', marginTop: '10px' }}>
          <button 
            onClick={() => executeQuickAction('search_web')}
            disabled={isLoading}
            style={{ padding: '8px 16px', backgroundColor: '#007bff', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
          >
            🔍 Search Web
          </button>
          <button 
            onClick={() => executeQuickAction('find_events')}
            disabled={isLoading}
            style={{ padding: '8px 16px', backgroundColor: '#28a745', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
          >
            📅 Find Events
          </button>
          <button 
            onClick={() => executeQuickAction('get_weather')}
            disabled={isLoading}
            style={{ padding: '8px 16px', backgroundColor: '#17a2b8', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
          >
            🌤️ Weather
          </button>
          <button 
            onClick={() => executeQuickAction('generate_content')}
            disabled={isLoading}
            style={{ padding: '8px 16px', backgroundColor: '#6f42c1', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
          >
            ✍️ Generate Content
          </button>
        </div>
      </div>

      <div className="chat-messages" style={{ height: '400px', overflowY: 'auto', border: '1px solid #dee2e6', borderRadius: '8px', padding: '15px', marginBottom: '15px', backgroundColor: '#f8f9fa' }}>
        {messages.map((message) => (
          <div key={message.id} className={`message ${message.sender}`} style={{ marginBottom: '15px' }}>
            <div className="message-content">
              <p>{message.text}</p>
              
              {/* Show function calls if any */}
              {message.functionCalls && message.functionCalls.length > 0 && (
                <div className="function-calls">
                  <h4>🔧 Tools Used:</h4>
                  {message.functionCalls.map((call, index) => (
                    <div key={index} className="function-call">
                      <strong>{call.function_name}</strong>
                      {call.result && (
                        <pre>{JSON.stringify(call.result, null, 2)}</pre>
                      )}
                    </div>
                  ))}
                </div>
              )}
              
              {/* Show reasoning if available */}
              {message.reasoning && (
                <div className="reasoning">
                  <h4>🧠 AI Reasoning:</h4>
                  <p>{message.reasoning}</p>
                </div>
              )}
            </div>
            <span className="timestamp">
              {message.timestamp.toLocaleTimeString()}
            </span>
          </div>
        ))}
        
        {isLoading && (
          <div className="message ai loading">
            <div className="message-content">
              <p>🤖 AI is thinking and using tools...</p>
            </div>
          </div>
        )}
      </div>

      <div className="chat-input" style={{ display: 'flex', gap: '10px' }}>
        <input
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
          placeholder="Ask me to search the web, find events, customize newsletters..."
          disabled={isLoading}
        />
        <button onClick={handleSendMessage} disabled={isLoading || !inputValue.trim()}>
          Send
        </button>
      </div>

      <div className="chat-examples">
        <h4>Try these examples:</h4>
        <div className="example-buttons" style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', marginTop: '10px' }}>
          <button onClick={() => setInputValue("Search for AI news")} style={{ padding: '6px 12px', backgroundColor: '#007bff', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
            🔍 Search Web
          </button>
          <button onClick={() => setInputValue("Find events in London SW1A 1AA")} style={{ padding: '6px 12px', backgroundColor: '#28a745', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
            📅 Find Events
          </button>
          <button onClick={() => setInputValue("Generate content about community events")} style={{ padding: '6px 12px', backgroundColor: '#6f42c1', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
            ✍️ Generate Content
          </button>
          <button onClick={() => setInputValue("Customize newsletter layout")} style={{ padding: '6px 12px', backgroundColor: '#fd7e14', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
            🎨 Customize Newsletter
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface; 