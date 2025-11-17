# Design Document: Frontend Dashboard Enhancement

## Overview

This design enhances the existing MISIX web dashboard with a complete chat interface, real-time updates, data visualization, and improved UX. The solution builds on the existing React + TypeScript + Tailwind CSS foundation while adding new features for a production-ready web application.

## Architecture

### Component Hierarchy

```
App
├── AuthProvider (JWT management)
├── ThemeProvider (Dark mode)
├── QueryClientProvider (React Query)
└── Router
    ├── LoginPage
    ├── RegisterPage
    └── DashboardLayout
        ├── Sidebar (Navigation)
        ├── Header (User menu, settings)
        └── MainContent
            ├── OverviewPage (Summary cards + Chat)
            ├── TasksPage
            ├── FinancesPage
            ├── NotesPage
            ├── MoodPage
            └── SettingsPage
```

### State Management

```
Zustand Stores:
├── authStore (user, token, login, logout)
├── uiStore (theme, sidebar, modals, toasts)
├── chatStore (messages, isTyping, sendMessage)
└── settingsStore (preferences, sync)

React Query:
├── queries (data fetching with caching)
├── mutations (data updates with optimistic UI)
└── invalidation (automatic refetch on changes)
```

## Components and Interfaces

### 1. Chat Interface

**File:** `frontend/src/features/chat/ChatInterface.tsx`

**Design:**

```typescript
interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  entities?: CreatedEntity[];
}

interface ChatInterfaceProps {
  userId: string;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ userId }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  
  const sendMessage = async (text: string) => {
    // Add user message
    const userMessage = { id: uuid(), role: 'user', content: text, timestamp: new Date() };
    setMessages(prev => [...prev, userMessage]);
    
    // Show typing indicator
    setIsTyping(true);
    
    try {
      // Call API
      const response = await apiClient.post('/api/assistant/send-message', {
        message: text,
        user_id: userId
      });
      
      // Add assistant response
      const assistantMessage = {
        id: uuid(),
        role: 'assistant',
        content: response.data.message,
        timestamp: new Date(),
        entities: response.data.entities
      };
      setMessages(prev => [...prev, assistantMessage]);
    } finally {
      setIsTyping(false);
    }
  };
  
  return (
    <div className="flex flex-col h-full">
      <MessageList messages={messages} />
      {isTyping && <TypingIndicator />}
      <MessageInput onSend={sendMessage} />
    </div>
  );
};
```

**Features:**
- Markdown rendering with `marked` library
- Auto-scroll to latest message
- Entity confirmations displayed inline
- Voice input button
- Message timestamps
- Loading states

### 2. Data Visualization

**File:** `frontend/src/features/analytics/Charts.tsx`

**Library:** Recharts (lightweight, responsive)

**Charts:**

```typescript
// Finance Trend Chart
<LineChart data={financeData}>
  <XAxis dataKey="date" />
  <YAxis />
  <Tooltip />
  <Legend />
  <Line type="monotone" dataKey="income" stroke="#10b981" />
  <Line type="monotone" dataKey="expense" stroke="#ef4444" />
</LineChart>

// Expense Categories Pie Chart
<PieChart>
  <Pie
    data={categoryData}
    dataKey="amount"
    nameKey="category"
    cx="50%"
    cy="50%"
    outerRadius={80}
    label
  />
  <Tooltip />
</PieChart>

// Task Completion Bar Chart
<BarChart data={taskData}>
  <XAxis dataKey="week" />
  <YAxis />
  <Tooltip />
  <Bar dataKey="completed" fill="#10b981" />
  <Bar dataKey="pending" fill="#f59e0b" />
</BarChart>
```

### 3. Authentication System

**Files:**
- `frontend/src/features/auth/LoginPage.tsx`
- `frontend/src/features/auth/RegisterPage.tsx`
- `frontend/src/stores/authStore.ts`

**Auth Store:**

```typescript
interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => void;
  refreshToken: () => Promise<void>;
}

const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: localStorage.getItem('token'),
  isAuthenticated: !!localStorage.getItem('token'),
  
  login: async (email, password) => {
    const response = await apiClient.post('/api/v2/auth/login', { email, password });
    const { access_token, user } = response.data;
    localStorage.setItem('token', access_token);
    set({ token: access_token, user, isAuthenticated: true });
  },
  
  logout: () => {
    localStorage.removeItem('token');
    set({ token: null, user: null, isAuthenticated: false });
  },
  
  refreshToken: async () => {
    const refresh_token = localStorage.getItem('refresh_token');
    const response = await apiClient.post('/api/v2/auth/refresh', { refresh_token });
    const { access_token } = response.data;
    localStorage.setItem('token', access_token);
    set({ token: access_token });
  }
}));
```

**Axios Interceptor:**

```typescript
apiClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      try {
        await useAuthStore.getState().refreshToken();
        return apiClient.request(error.config);
      } catch {
        useAuthStore.getState().logout();
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);
```

### 4. Dark Mode Implementation

**File:** `frontend/src/providers/ThemeProvider.tsx`

**Design:**

```typescript
const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [theme, setTheme] = useState<'light' | 'dark'>(() => {
    const saved = localStorage.getItem('theme');
    if (saved) return saved as 'light' | 'dark';
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  });
  
  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark');
    localStorage.setItem('theme', theme);
  }, [theme]);
  
  return (
    <ThemeContext.Provider value={{ theme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  );
};
```

**Tailwind Config:**

```javascript
// tailwind.config.js
module.exports = {
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        background: {
          light: '#ffffff',
          dark: '#1a1a1a'
        },
        text: {
          light: '#1f2937',
          dark: '#f9fafb'
        }
      }
    }
  }
}
```

### 5. Mobile Responsive Layout

**Breakpoints:**
- `sm`: 640px (mobile)
- `md`: 768px (tablet)
- `lg`: 1024px (desktop)
- `xl`: 1280px (large desktop)

**Responsive Sidebar:**

```typescript
const Sidebar: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  
  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black/50 lg:hidden z-40"
          onClick={() => setIsOpen(false)}
        />
      )}
      
      {/* Sidebar */}
      <aside className={`
        fixed lg:static inset-y-0 left-0 z-50
        w-64 bg-white dark:bg-gray-900
        transform transition-transform duration-300
        ${isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
      `}>
        <nav>...</nav>
      </aside>
      
      {/* Mobile menu button */}
      <button
        className="lg:hidden fixed top-4 left-4 z-30"
        onClick={() => setIsOpen(!isOpen)}
      >
        <MenuIcon />
      </button>
    </>
  );
};
```

### 6. Performance Optimizations

**Code Splitting:**

```typescript
// Lazy load routes
const TasksPage = lazy(() => import('./pages/TasksPage'));
const FinancesPage = lazy(() => import('./pages/FinancesPage'));
const NotesPage = lazy(() => import('./pages/NotesPage'));

<Suspense fallback={<Loader />}>
  <Routes>
    <Route path="/tasks" element={<TasksPage />} />
    <Route path="/finances" element={<FinancesPage />} />
    <Route path="/notes" element={<NotesPage />} />
  </Routes>
</Suspense>
```

**Virtual Scrolling:**

```typescript
import { useVirtualizer } from '@tanstack/react-virtual';

const VirtualList: React.FC<{ items: any[] }> = ({ items }) => {
  const parentRef = useRef<HTMLDivElement>(null);
  
  const virtualizer = useVirtualizer({
    count: items.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 60,
  });
  
  return (
    <div ref={parentRef} className="h-full overflow-auto">
      <div style={{ height: `${virtualizer.getTotalSize()}px` }}>
        {virtualizer.getVirtualItems().map((virtualItem) => (
          <div
            key={virtualItem.key}
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              height: `${virtualItem.size}px`,
              transform: `translateY(${virtualItem.start}px)`,
            }}
          >
            <ItemComponent item={items[virtualItem.index]} />
          </div>
        ))}
      </div>
    </div>
  );
};
```

## Data Models

### Chat Message

```typescript
interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  entities?: {
    type: 'task' | 'finance' | 'note' | 'mood';
    data: any;
  }[];
}
```

### Chart Data

```typescript
interface FinanceTrendData {
  date: string;
  income: number;
  expense: number;
  balance: number;
}

interface CategoryData {
  category: string;
  amount: number;
  percentage: number;
  color: string;
}
```

## Error Handling

### Error Boundary

```typescript
class ErrorBoundary extends React.Component<Props, State> {
  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
    // Log to error tracking service (e.g., Sentry)
  }
  
  render() {
    if (this.state.hasError) {
      return (
        <div className="flex items-center justify-center h-screen">
          <div className="text-center">
            <h1 className="text-2xl font-bold mb-4">Что-то пошло не так</h1>
            <Button onClick={() => window.location.reload()}>
              Перезагрузить страницу
            </Button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
```

### API Error Handling

```typescript
const handleApiError = (error: AxiosError) => {
  if (error.response) {
    // Server responded with error
    const message = error.response.data?.error || 'Ошибка сервера';
    showToast(message, 'error');
  } else if (error.request) {
    // No response received
    showToast('Нет связи с сервером', 'error');
  } else {
    // Request setup error
    showToast('Ошибка запроса', 'error');
  }
};
```

## Testing Strategy

### Unit Tests (Vitest)

```typescript
describe('ChatInterface', () => {
  it('sends message on submit', async () => {
    const { getByRole, getByText } = render(<ChatInterface userId="123" />);
    
    const input = getByRole('textbox');
    const button = getByRole('button', { name: /send/i });
    
    fireEvent.change(input, { target: { value: 'Hello' } });
    fireEvent.click(button);
    
    await waitFor(() => {
      expect(getByText('Hello')).toBeInTheDocument();
    });
  });
});
```

### Integration Tests

```typescript
describe('Dashboard Integration', () => {
  it('loads and displays summary data', async () => {
    const { getByText } = render(<DashboardPage />);
    
    await waitFor(() => {
      expect(getByText(/задачи/i)).toBeInTheDocument();
      expect(getByText(/финансы/i)).toBeInTheDocument();
    });
  });
});
```

## Deployment

### Build Optimization

```json
// vite.config.ts
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom'],
          'query-vendor': ['@tanstack/react-query'],
          'chart-vendor': ['recharts']
        }
      }
    },
    chunkSizeWarningLimit: 1000
  }
});
```

### Environment Variables

```bash
# .env.production
VITE_API_BASE_URL=https://api.misix.app
VITE_ENABLE_ANALYTICS=true
```

## Accessibility

### Keyboard Navigation

```typescript
const Modal: React.FC = ({ onClose, children }) => {
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    
    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [onClose]);
  
  return (
    <div role="dialog" aria-modal="true">
      {children}
    </div>
  );
};
```

### ARIA Labels

```typescript
<button
  aria-label="Отправить сообщение"
  aria-disabled={isLoading}
>
  <SendIcon />
</button>
```

## Security Considerations

1. **XSS Prevention**: Sanitize user input before rendering
2. **CSRF Protection**: Use CSRF tokens for mutations
3. **Secure Storage**: Store tokens in httpOnly cookies (if possible)
4. **Content Security Policy**: Restrict script sources
5. **Input Validation**: Validate all form inputs

## Performance Metrics

### Target Metrics

- **First Contentful Paint**: < 1.5s
- **Time to Interactive**: < 3.5s
- **Largest Contentful Paint**: < 2.5s
- **Cumulative Layout Shift**: < 0.1
- **First Input Delay**: < 100ms

### Monitoring

```typescript
// Web Vitals
import { getCLS, getFID, getFCP, getLCP, getTTFB } from 'web-vitals';

getCLS(console.log);
getFID(console.log);
getFCP(console.log);
getLCP(console.log);
getTTFB(console.log);
```

## Future Enhancements

1. **Progressive Web App**: Add service worker for offline support
2. **Push Notifications**: Browser notifications for reminders
3. **Real-time Sync**: WebSocket for live updates
4. **Advanced Analytics**: More detailed charts and insights
5. **Export Features**: PDF/CSV export for data
