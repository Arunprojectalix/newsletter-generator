import api from './api';

export interface ChatMessage {
  message: string;
  conversation_history?: Array<{ role: string; content: string }>;
}

export interface ChatAction {
  type: string;
  label: string;
  action?: string;
  url?: string;
  description?: string;
  data?: any;
}

export interface ChatResponse {
  message: string;
  actions: ChatAction[];
  data?: any;
}

export interface ToolInfo {
  tool_id: string;
  name: string;
  description: string;
  parameters: Record<string, any>;
}

export interface ToolExecutionRequest {
  tool_id: string;
  parameters: Record<string, any>;
}

export interface WebSearchResult {
  url: string;
  title: string;
  description: string;
  source: string;
}

export interface EventSearchRequest {
  postcode: string;
  radius?: number;
  frequency?: string;
}

export interface AIReasoningChatRequest {
  message: string;
  newsletter_id: string;
  conversation_history?: Array<{role: string; content: string}>;
}

export interface AIReasoningChatResponse {
  message: string;
  function_calls: Array<{
    tool_call_id: string;
    function_name: string;
    result: any;
  }>;
  reasoning: string;
  conversation_history: Array<{role: string; content: string}>;
  newsletter_id: string;
}

export class ChatService {
  private apiClient = api;

  /**
   * Send a chat message to the assistant
   */
  async sendMessage(newsletterId: string, message: string): Promise<ChatResponse> {
    try {
      const response = await this.apiClient.post(`/chat/${newsletterId}`, {
        message,
      });
      return response.data;
    } catch (error) {
      console.error('Error sending chat message:', error);
      throw new Error('Failed to send message');
    }
  }

  /**
   * Get all available tools
   */
  async getAvailableTools(): Promise<ToolInfo[]> {
    try {
      const response = await this.apiClient.get('/chat/tools/available');
      return response.data.tools;
    } catch (error) {
      console.error('Error getting available tools:', error);
      throw new Error('Failed to get available tools');
    }
  }

  /**
   * Execute a specific tool
   */
  async executeTool(toolId: string, parameters: Record<string, any>): Promise<any> {
    try {
      const response = await this.apiClient.post('/chat/tools/execute', {
        tool_id: toolId,
        parameters,
      });
      return response.data;
    } catch (error) {
      console.error('Error executing tool:', error);
      throw new Error('Failed to execute tool');
    }
  }

  /**
   * Search the web using the web search tool
   */
  async searchWeb(query: string, maxResults: number = 5): Promise<WebSearchResult[]> {
    try {
      const result = await this.executeTool('web_search', {
        query,
        max_results: maxResults,
      });

      if (result.success) {
        return result.result.results;
      } else {
        throw new Error(result.error || 'Web search failed');
      }
    } catch (error) {
      console.error('Error in web search:', error);
      throw error;
    }
  }

  /**
   * Search for local events
   */
  async searchEvents(postcode: string, radius: number = 10, frequency: string = 'weekly'): Promise<any[]> {
    try {
      const result = await this.executeTool('event_search', {
        postcode,
        radius,
        frequency,
      });

      if (result.success) {
        return result.result.events;
      } else {
        throw new Error(result.error || 'Event search failed');
      }
    } catch (error) {
      console.error('Error in event search:', error);
      throw error;
    }
  }

  /**
   * Search for local businesses
   */
  async searchLocalBusinesses(
    query: string,
    location: string,
    businessType: string = 'any'
  ): Promise<WebSearchResult[]> {
    try {
      const result = await this.executeTool('local_business_search', {
        query,
        location,
        business_type: businessType,
      });

      if (result.success) {
        return result.result.results;
      } else {
        throw new Error(result.error || 'Local business search failed');
      }
    } catch (error) {
      console.error('Error in local business search:', error);
      throw error;
    }
  }

  /**
   * Get real-time information (weather, traffic, etc.)
   */
  async getRealTimeInfo(query: string, infoType: string = 'general'): Promise<WebSearchResult[]> {
    try {
      const result = await this.executeTool('real_time_info', {
        query,
        info_type: infoType,
      });

      if (result.success) {
        return result.result.results;
      } else {
        throw new Error(result.error || 'Real-time info search failed');
      }
    } catch (error) {
      console.error('Error getting real-time info:', error);
      throw error;
    }
  }

  /**
   * Generate content using AI
   */
  async generateContent(
    contentType: string,
    topic: string,
    style: string = 'professional',
    length: string = 'medium'
  ): Promise<string> {
    try {
      const result = await this.executeTool('content_generation', {
        content_type: contentType,
        topic,
        style,
        length,
      });

      if (result.success) {
        return result.result.generated_content;
      } else {
        throw new Error(result.error || 'Content generation failed');
      }
    } catch (error) {
      console.error('Error generating content:', error);
      throw error;
    }
  }

  /**
   * Search for images
   */
  async searchImages(
    query: string,
    style: string = 'professional',
    size: string = 'large'
  ): Promise<any[]> {
    try {
      const result = await this.executeTool('image_search', {
        query,
        style,
        size,
      });

      if (result.success) {
        return result.result.images;
      } else {
        throw new Error(result.error || 'Image search failed');
      }
    } catch (error) {
      console.error('Error searching images:', error);
      throw error;
    }
  }

  /**
   * Customize newsletter
   */
  async customizeNewsletter(
    newsletterId: string,
    customizationType: string,
    parameters: Record<string, any>
  ): Promise<any> {
    try {
      const result = await this.executeTool('newsletter_customization', {
        newsletter_id: newsletterId,
        customization_type: customizationType,
        parameters,
      });

      if (result.success) {
        return result.result;
      } else {
        throw new Error(result.error || 'Newsletter customization failed');
      }
    } catch (error) {
      console.error('Error customizing newsletter:', error);
      throw error;
    }
  }

  /**
   * Manage newsletter schedule
   */
  async manageSchedule(
    newsletterId: string,
    action: string,
    scheduleData?: Record<string, any>
  ): Promise<any> {
    try {
      const result = await this.executeTool('schedule_management', {
        newsletter_id: newsletterId,
        action,
        schedule_data: scheduleData,
      });

      if (result.success) {
        return result.result;
      } else {
        throw new Error(result.error || 'Schedule management failed');
      }
    } catch (error) {
      console.error('Error managing schedule:', error);
      throw error;
    }
  }

  /**
   * Process natural language commands
   */
  async processCommand(newsletterId: string, command: string): Promise<ChatResponse> {
    // This method demonstrates how to use the chat interface for natural language processing
    const response = await this.sendMessage(newsletterId, command);
    
    // Process the response and execute any suggested actions
    if (response.actions && response.actions.length > 0) {
      console.log('Available actions:', response.actions);
    }
    
    return response;
  }

  /**
   * Example usage methods for common scenarios
   */
  
  // Example: Search for restaurants around a location
  async findRestaurantsNearby(location: string): Promise<WebSearchResult[]> {
    return this.searchWeb(`best restaurants around ${location}`, 5);
  }

  // Example: Find events this weekend
  async findWeekendEvents(postcode: string): Promise<any[]> {
    return this.searchEvents(postcode, 15, 'weekly');
  }

  // Example: Get weather information
  async getWeatherInfo(location: string): Promise<WebSearchResult[]> {
    return this.getRealTimeInfo(`${location} weather today`, 'weather');
  }

  // Example: Generate newsletter content about a topic
  async createNewsletterContent(topic: string): Promise<string> {
    return this.generateContent('article', topic, 'friendly', 'medium');
  }

  // Example: Find images for a newsletter section
  async findNewsletterImages(topic: string): Promise<any[]> {
    return this.searchImages(topic, 'professional', 'large');
  }

  /**
   * AI Chat with GPT Function Calling and Reasoning
   * This is exactly what was requested - AI that can reason and use tools
   */
  async aiChatWithReasoning(request: AIReasoningChatRequest): Promise<AIReasoningChatResponse> {
    try {
      const response = await api.post<AIReasoningChatResponse>(`/chat/ai-chat`, request);
      return response.data;
    } catch (error) {
      console.error('AI Chat Error:', error);
      throw error;
    }
  }
}

// Export a singleton instance
export const chatService = new ChatService();


export default ChatService; 