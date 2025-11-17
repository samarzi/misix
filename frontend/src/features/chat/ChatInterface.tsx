import { useState, useRef, useEffect } from 'react';
import { marked } from 'marked';
import axios from 'axios';
import { API_BASE_URL } from '../../config';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  entities?: Array<{
    type: 'task' | 'finance' | 'note' | 'mood';
    data: any;
  }>;
}

interface ChatInterfaceProps {
  userId: string;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ userId }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Load messages from localStorage on mount
  useEffect(() => {
    const savedMessages = localStorage.getItem(`chat_${userId}`);
    if (savedMessages) {
      try {
        const parsed = JSON.parse(savedMessages);
        setMessages(parsed.map((m: any) => ({
          ...m,
          timestamp: new Date(m.timestamp)
        })));
      } catch (e) {
        console.error('Failed to load messages:', e);
      }
    }
  }, [userId]);

  // Save messages to localStorage
  useEffect(() => {
    if (messages.length > 0) {
      localStorage.setItem(`chat_${userId}`, JSON.stringify(messages));
    }
  }, [messages, userId]);

  const sendMessage = async (text: string) => {
    if (!text.trim() || isLoading) return;

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: text.trim(),
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsTyping(true);
    setIsLoading(true);

    try {
      const response = await axios.post(`${API_BASE_URL}/api/assistant/send-message`, {
        message: text.trim(),
        user_id: userId,
      });

      const assistantMessage: Message = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: response.data.message || 'Извините, не удалось получить ответ.',
        timestamp: new Date(),
        entities: response.data.entities,
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Failed to send message:', error);
      
      const errorMessage: Message = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: 'Извините, произошла ошибка при отправке сообщения. Попробуйте еще раз.',
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsTyping(false);
      setIsLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage(input);
    }
  };

  const formatTimestamp = (date: Date) => {
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    
    if (minutes < 1) return 'только что';
    if (minutes < 60) return `${minutes} мин назад`;
    
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours} ч назад`;
    
    return date.toLocaleDateString('ru-RU', { 
      day: 'numeric', 
      month: 'short',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const renderMessage = (message: Message) => {
    const isUser = message.role === 'user';
    const htmlContent = marked(message.content);

    return (
      <div
        key={message.id}
        className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}
      >
        <div className={`max-w-[80%] ${isUser ? 'order-2' : 'order-1'}`}>
          <div
            className={`rounded-2xl px-4 py-3 ${
              isUser
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100'
            }`}
          >
            <div
              className="prose prose-sm max-w-none dark:prose-invert"
              dangerouslySetInnerHTML={{ __html: htmlContent }}
            />
            
            {message.entities && message.entities.length > 0 && (
              <div className="mt-3 pt-3 border-t border-white/20 space-y-2">
                {message.entities.map((entity, idx) => (
                  <div key={idx} className="text-sm opacity-90">
                    {entity.type === 'task' && (
                      <div className="flex items-center gap-2">
                        <span>✅</span>
                        <span>Создал задачу: {entity.data.title}</span>
                      </div>
                    )}
                    {entity.type === 'finance' && (
                      <div className="flex items-center gap-2">
                        <span>{entity.data.finance_type === 'expense' ? '💸' : '💰'}</span>
                        <span>
                          {entity.data.finance_type === 'expense' ? 'Расход' : 'Доход'}: {entity.data.amount}₽
                        </span>
                      </div>
                    )}
                    {entity.type === 'note' && (
                      <div className="flex items-center gap-2">
                        <span>📝</span>
                        <span>Сохранил заметку: {entity.data.title}</span>
                      </div>
                    )}
                    {entity.type === 'mood' && (
                      <div className="flex items-center gap-2">
                        <span>😊</span>
                        <span>Отметил настроение: {entity.data.mood}</span>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
          
          <div className={`text-xs text-gray-500 mt-1 ${isUser ? 'text-right' : 'text-left'}`}>
            {formatTimestamp(message.timestamp)}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="flex flex-col h-full bg-white dark:bg-gray-900">
      {/* Header */}
      <div className="flex-shrink-0 px-6 py-4 border-b border-gray-200 dark:border-gray-700">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
          💬 Чат с MISIX
        </h2>
        <p className="text-sm text-gray-500 dark:text-gray-400">
          Задавайте вопросы, создавайте задачи и управляйте данными
        </p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-4">
        {messages.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center text-gray-500 dark:text-gray-400">
              <div className="text-6xl mb-4">👋</div>
              <p className="text-lg font-medium mb-2">Привет! Я MISIX</p>
              <p className="text-sm">
                Напишите что-нибудь, чтобы начать разговор
              </p>
              <div className="mt-6 space-y-2 text-sm text-left max-w-md mx-auto">
                <p className="text-gray-600 dark:text-gray-300">Примеры:</p>
                <div className="space-y-1">
                  <p>• "напомни завтра купить молоко"</p>
                  <p>• "потратил 500₽ на кофе"</p>
                  <p>• "сегодня отличное настроение"</p>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <>
            {messages.map(renderMessage)}
            {isTyping && (
              <div className="flex justify-start mb-4">
                <div className="bg-gray-100 dark:bg-gray-800 rounded-2xl px-4 py-3">
                  <div className="flex gap-1">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Input */}
      <div className="flex-shrink-0 px-6 py-4 border-t border-gray-200 dark:border-gray-700">
        <div className="flex gap-3">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Напишите сообщение..."
            disabled={isLoading}
            className="flex-1 resize-none rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-4 py-3 text-gray-900 dark:text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
            rows={1}
            style={{ minHeight: '48px', maxHeight: '120px' }}
          />
          <button
            onClick={() => sendMessage(input)}
            disabled={!input.trim() || isLoading}
            className="flex-shrink-0 w-12 h-12 rounded-xl bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center"
            aria-label="Отправить сообщение"
          >
            {isLoading ? (
              <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
            ) : (
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
              </svg>
            )}
          </button>
        </div>
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
          Нажмите Enter для отправки, Shift+Enter для новой строки
        </p>
      </div>
    </div>
  );
};

export default ChatInterface;
