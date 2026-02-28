import { useState, useEffect, useRef } from 'react';
import { Send, BookOpen, Brain, Settings, Trash2, ChevronDown, Loader2, Beaker, Database, ExternalLink, Calendar, Users, Tag } from 'lucide-react';
import VSCLogo from './VSCLogo';

// Backend API URL - always use localhost for now (overridden by Vite config)
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function ScholarsTerminal() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [selectedModel, setSelectedModel] = useState('llama3.2');
  const [selectedSource, setSelectedSource] = useState('all');
  const [showSettings, setShowSettings] = useState(false);
  const [availableModels, setAvailableModels] = useState(['llama3.2']);
  const [connectionStatus, setConnectionStatus] = useState('checking');
  const [researchStats, setResearchStats] = useState(null);
  const [showStats, setShowStats] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Check backend connection and fetch models on mount
  useEffect(() => {
    const checkConnection = async () => {
      try {
        const response = await fetch(`${API_URL}/api/tags`);
        if (response.ok) {
          const data = await response.json();
          const models = data.models?.map(m => m.name) || ['llama3.2'];
          setAvailableModels(models);
          if (models.length > 0 && !models.includes(selectedModel)) {
            setSelectedModel(models[0]);
          }
          setConnectionStatus('connected');
        } else {
          setConnectionStatus('error');
        }
      } catch (err) {
        console.error('Connection check failed:', err);
        setConnectionStatus('error');
      }
    };
    checkConnection();
    fetchResearchStats();
  }, []);

  // Fetch research paper statistics
  const fetchResearchStats = async () => {
    try {
      // Research scanner disabled
      // const response = await fetch(`${API_URL}/api/research/status`);
      return;
      if (response.ok) {
        const data = await response.json();
        setResearchStats(data);
      }
    } catch (err) {
      console.error('Failed to fetch research stats:', err);
    }
  };

  // Load conversation history from localStorage
  useEffect(() => {
    const saved = localStorage.getItem('scholars_terminal_chat');
    if (saved) {
      try {
        setMessages(JSON.parse(saved));
      } catch (e) {
        console.error('Failed to load chat history:', e);
      }
    }
  }, []);

  // Save conversation history to localStorage
  useEffect(() => {
    if (messages.length > 0) {
      localStorage.setItem('scholars_terminal_chat', JSON.stringify(messages));
    }
  }, [messages]);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage = {
      role: 'user',
      content: input,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await fetch(`${API_URL}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model: selectedModel,
          messages: [...messages, userMessage].map(m => ({
            role: m.role,
            content: m.content
          })),
          use_knowledge_base: true,
          num_results: 5,
          source_filter: selectedSource  // NEW: Pass source filter
        })
      });

      if (!response.ok) throw new Error('Failed to get response');

      const data = await response.json();

      const assistantMessage = {
        role: 'assistant',
        content: data.message.content,
        timestamp: new Date().toISOString(),
        model: selectedModel,
        citations: data.citations
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (err) {
      console.error('Error:', err);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `Connection error. Make sure the backend API is running:\n\ncd D:\\Claude\\Projects\\scholars-terminal\nstart_backend.bat`,
        timestamp: new Date().toISOString(),
        isError: true
      }]);
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const clearHistory = () => {
    setMessages([]);
    localStorage.removeItem('scholars_terminal_chat');
  };

  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString([], { 
      month: 'short', 
      day: 'numeric', 
      year: 'numeric' 
    });
  };

  // NEW: Render research paper citation
  const renderCitation = (citation) => {
    // Check if this is a research paper
    const isResearchPaper = citation.content_type === 'research_paper' || 
                           citation.source?.includes('arxiv') || 
                           citation.source?.includes('semantic_scholar') ||
                           citation.source?.includes('huggingface') ||
                           citation.source?.includes('pubmed');

    if (!isResearchPaper) {
      // Regular book citation (Books/GitHub mixed - no path metadata)
      return (
        <div style={styles.citation} key={citation.chunk_id}>
          <BookOpen size={14} style={styles.citationIcon} />
          <div style={styles.citationContent}>
            <div style={styles.citationTitle}>{citation.title || 'Book/Code Library'}</div>
            <div style={styles.citationMeta}>
              📚 From Books or 💻 GitHub collection
            </div>
          </div>
        </div>
      );
    }

    // Research paper citation with rich metadata
    return (
      <div style={styles.researchCitation} key={citation.paper_id || citation.chunk_id}>
        <div style={styles.researchHeader}>
          <Beaker size={16} style={styles.researchIcon} />
          <a 
            href={citation.url} 
            target="_blank" 
            rel="noopener noreferrer"
            style={styles.researchTitle}
          >
            {citation.title || 'Untitled Paper'}
            <ExternalLink size={12} style={styles.externalLink} />
          </a>
        </div>
        
        <div style={styles.researchMetadata}>
          {citation.authors && (
            <div style={styles.metaItem}>
              <Users size={12} />
              <span>{citation.authors.split(',').slice(0, 2).join(', ')}
                {citation.authors.split(',').length > 2 ? ' et al.' : ''}
              </span>
            </div>
          )}
          
          <div style={styles.metaRow}>
            {citation.source && (
              <span style={styles.sourceBadge}>
                {citation.source === 'arxiv' ? '📄 arXiv' :
                 citation.source === 'semantic_scholar' ? '🔍 S2' :
                 citation.source === 'huggingface' ? '🤗 HF' :
                 citation.source === 'pubmed' ? '🧬 PubMed' :
                 `📚 ${citation.source}`}
              </span>
            )}
            
            {citation.published_date && (
              <div style={styles.metaItem}>
                <Calendar size={12} />
                <span>{formatDate(citation.published_date)}</span>
              </div>
            )}
            
            {citation.citation_count !== undefined && citation.citation_count > 0 && (
              <div style={styles.metaItem}>
                <span>📊 {citation.citation_count.toLocaleString()} citations</span>
              </div>
            )}
          </div>
          
          {citation.relevance_score !== undefined && (
            <div style={styles.metaItem}>
              <span style={styles.relevanceBadge}>
                Relevance: {(citation.relevance_score * 100).toFixed(0)}%
              </span>
            </div>
          )}
          
          {citation.topics && (
            <div style={styles.topicTags}>
              <Tag size={12} />
              {citation.topics.split(',').slice(0, 3).map((topic, i) => (
                <span key={i} style={styles.topicTag}>{topic.trim()}</span>
              ))}
            </div>
          )}
        </div>

        {citation.summary_excerpt && (
          <div style={styles.paperSummary}>
            {citation.summary_excerpt.substring(0, 200)}
            {citation.summary_excerpt.length > 200 ? '...' : ''}
          </div>
        )}
      </div>
    );
  };

  return (
    <div style={styles.container}>
      {/* Header */}
      <header style={styles.header}>
        <div style={styles.headerLeft}>
          <VSCLogo size={48} />
          <div>
            <h1 style={styles.title}>Scholar's Terminal</h1>
            <span style={styles.subtitle}>Knowledge Base Assistant</span>
          </div>
        </div>
        <div style={styles.headerRight}>
          <div style={styles.statusIndicator}>
            <span style={{
              ...styles.statusDot,
              backgroundColor: connectionStatus === 'connected' ? '#4ade80' :
                connectionStatus === 'error' ? '#f87171' : '#fbbf24'
            }} />
            <span style={styles.statusText}>
              {connectionStatus === 'connected' ? 'Connected' :
                connectionStatus === 'error' ? 'Disconnected' : 'Checking...'}
            </span>
          </div>
          <button
            style={styles.iconButton}
            onClick={() => setShowStats(!showStats)}
            title="Collection Stats"
          >
            <Database size={20} />
          </button>
          <button
            style={styles.iconButton}
            onClick={() => setShowSettings(!showSettings)}
            title="Settings"
          >
            <Settings size={20} />
          </button>
          <button
            style={styles.iconButton}
            onClick={clearHistory}
            title="Clear History"
          >
            <Trash2 size={20} />
          </button>
        </div>
      </header>

      {/* Stats Panel */}
      {showStats && researchStats && (
        <div style={styles.statsPanel}>
          <h3 style={styles.statsPanelTitle}>
            <Database size={18} />
            Collection Statistics
          </h3>
          <div style={styles.statsGrid}>
            <div style={styles.statCard}>
              <BookOpen size={24} style={{ color: '#c9a227' }} />
              <div>
                <div style={styles.statValue}>24,528</div>
                <div style={styles.statLabel}>Books + GitHub</div>
              </div>
            </div>
            <div style={styles.statCard}>
              <Beaker size={24} style={{ color: '#4ade80' }} />
              <div>
                <div style={styles.statValue}>
                  {researchStats.total_papers?.toLocaleString() || '0'}
                </div>
                <div style={styles.statLabel}>Research Papers</div>
              </div>
            </div>
            <div style={styles.statCard}>
              <Brain size={24} style={{ color: '#60a5fa' }} />
              <div>
                <div style={styles.statValue}>
                  {researchStats.enabled_sources?.length || 0}
                </div>
                <div style={styles.statLabel}>Active Sources</div>
              </div>
            </div>
          </div>
          {researchStats.latest_scan_time && (
            <div style={styles.statsFooter}>
              Last updated: {new Date(researchStats.latest_scan_time).toLocaleString()}
            </div>
          )}
        </div>
      )}

      {/* Settings Panel */}
      {showSettings && (
        <div style={styles.settingsPanel}>
          <div style={styles.settingGroup}>
            <label style={styles.settingsLabel}>
              <Brain size={16} />
              Model:
            </label>
            <div style={styles.selectWrapper}>
              <select
                value={selectedModel}
                onChange={(e) => setSelectedModel(e.target.value)}
                style={styles.select}
              >
                {availableModels.map(model => (
                  <option key={model} value={model}>{model}</option>
                ))}
              </select>
              <ChevronDown size={16} style={styles.selectIcon} />
            </div>
          </div>

          <div style={styles.settingGroup}>
            <label style={styles.settingsLabel}>
              <Database size={16} />
              Search In:
            </label>
            <div style={styles.selectWrapper}>
              <select
                value={selectedSource}
                onChange={(e) => setSelectedSource(e.target.value)}
                style={styles.select}
              >
                <option value="all">🌐 All Sources</option>
                <option value="newsletters">📰 Newsletters (Ancient Origins)</option>
                <option value="books-only">📚 Books Only</option>
                <option value="github">💻 GitHub Only</option>
                <option value="books">📚💻 Books + GitHub (Mixed)</option>
                <option value="research">🔬 Research Papers</option>
                <option value="arxiv">📄 arXiv Papers</option>
                <option value="semantic_scholar">🔍 Semantic Scholar</option>
                <option value="huggingface">🤗 HuggingFace</option>
                <option value="pubmed">🧬 PubMed</option>
              </select>
              <ChevronDown size={16} style={styles.selectIcon} />
            </div>
          </div>
        </div>
      )}

      {/* Messages Area */}
      <main style={styles.messagesContainer}>
        {messages.length === 0 ? (
          <div style={styles.emptyState}>
            <BookOpen size={48} style={styles.emptyIcon} />
            <h2 style={styles.emptyTitle}>Welcome to Scholar's Terminal</h2>
            <p style={styles.emptyText}>
              Your personal knowledge base assistant with 9,000+ books and 
              {researchStats?.total_papers ? ` ${researchStats.total_papers}` : ''} research papers.
              Ask questions, explore ideas, and delve into your library of wisdom.
            </p>
          </div>
        ) : (
          messages.map((msg, idx) => (
            <div
              key={idx}
              style={{
                ...styles.message,
                ...(msg.role === 'user' ? styles.userMessage : styles.assistantMessage),
                ...(msg.isError ? styles.errorMessage : {})
              }}
            >
              <div style={styles.messageHeader}>
                <span style={styles.messageRole}>
                  {msg.role === 'user' ? 'You' : 'Scholar'}
                </span>
                <span style={styles.messageTime}>{formatTime(msg.timestamp)}</span>
                {msg.model && <span style={styles.modelBadge}>{msg.model}</span>}
              </div>
              <div style={styles.messageContent}>
                {msg.content.split('\n').map((line, i) => (
                  <p key={i} style={{ margin: line ? '0.5em 0' : '0' }}>{line}</p>
                ))}
              </div>
              
              {/* Citations */}
              {msg.citations && msg.citations.length > 0 && (
                <div style={styles.citationsContainer}>
                  <div style={styles.citationsHeader}>Sources Referenced:</div>
                  {msg.citations.map((citation, i) => renderCitation(citation))}
                </div>
              )}
            </div>
          ))
        )}
        {isLoading && (
          <div style={styles.loadingIndicator}>
            <Loader2 size={20} style={styles.spinner} />
            <span>Consulting the archives...</span>
          </div>
        )}
        <div ref={messagesEndRef} />
      </main>

      {/* Input Area */}
      <footer style={styles.inputContainer}>
        <div style={styles.inputWrapper}>
          <textarea
            ref={inputRef}
            style={styles.input}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={
              selectedSource === 'all' ? "Ask a question or begin your research..." :
              selectedSource === 'newsletters' ? "Search Ancient Origins newsletters..." :
              selectedSource === 'books-only' ? "Search your book library..." :
              selectedSource === 'github' ? "Search GitHub repositories..." :
              selectedSource === 'books' ? "Search books and GitHub..." :
              selectedSource === 'research' ? "Search research papers..." :
              `Search ${selectedSource} papers...`
            }
            disabled={isLoading}
            rows={1}
          />
          <button
            style={{
              ...styles.sendButton,
              opacity: isLoading || !input.trim() ? 0.5 : 1
            }}
            onClick={sendMessage}
            disabled={isLoading || !input.trim()}
          >
            <Send size={18} />
          </button>
        </div>
      </footer>
    </div>
  );
}

const styles = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    height: '100vh',
    backgroundColor: '#1a1915',
    color: '#e8e4d9',
    fontFamily: '"Crimson Pro", Georgia, serif',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '1rem 1.5rem',
    backgroundColor: '#252218',
    borderBottom: '1px solid #3d3a2f',
  },
  headerLeft: {
    display: 'flex',
    alignItems: 'center',
    gap: '1rem',
  },
  title: {
    margin: 0,
    fontSize: '1.5rem',
    fontWeight: 600,
    color: '#f5f0e1',
  },
  subtitle: {
    fontSize: '0.85rem',
    color: '#8a8578',
  },
  headerRight: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.75rem',
  },
  statusIndicator: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
    padding: '0.25rem 0.75rem',
    backgroundColor: '#1a1915',
    borderRadius: '1rem',
  },
  statusDot: {
    width: '8px',
    height: '8px',
    borderRadius: '50%',
  },
  statusText: {
    fontSize: '0.8rem',
    color: '#8a8578',
  },
  iconButton: {
    background: 'none',
    border: 'none',
    color: '#8a8578',
    cursor: 'pointer',
    padding: '0.5rem',
    borderRadius: '0.375rem',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    transition: 'all 0.2s',
  },
  
  // NEW: Stats Panel Styles
  statsPanel: {
    padding: '1rem 1.5rem',
    backgroundColor: '#252218',
    borderBottom: '1px solid #3d3a2f',
  },
  statsPanelTitle: {
    margin: '0 0 1rem 0',
    fontSize: '1rem',
    fontWeight: 600,
    color: '#f5f0e1',
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
  },
  statsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: '1rem',
  },
  statCard: {
    display: 'flex',
    alignItems: 'center',
    gap: '1rem',
    padding: '1rem',
    backgroundColor: '#1a1915',
    borderRadius: '0.5rem',
    border: '1px solid #3d3a2f',
  },
  statValue: {
    fontSize: '1.5rem',
    fontWeight: 600,
    color: '#f5f0e1',
  },
  statLabel: {
    fontSize: '0.8rem',
    color: '#8a8578',
  },
  statsFooter: {
    marginTop: '1rem',
    fontSize: '0.75rem',
    color: '#6b6558',
    textAlign: 'center',
  },
  
  // Settings Panel Styles (Enhanced)
  settingsPanel: {
    display: 'flex',
    alignItems: 'center',
    gap: '2rem',
    padding: '0.75rem 1.5rem',
    backgroundColor: '#252218',
    borderBottom: '1px solid #3d3a2f',
    flexWrap: 'wrap',
  },
  settingGroup: {
    display: 'flex',
    alignItems: 'center',
    gap: '1rem',
  },
  settingsLabel: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
    color: '#8a8578',
    fontSize: '0.9rem',
    whiteSpace: 'nowrap',
  },
  selectWrapper: {
    position: 'relative',
    display: 'flex',
    alignItems: 'center',
  },
  select: {
    appearance: 'none',
    backgroundColor: '#1a1915',
    color: '#e8e4d9',
    border: '1px solid #3d3a2f',
    borderRadius: '0.375rem',
    padding: '0.5rem 2rem 0.5rem 0.75rem',
    fontSize: '0.9rem',
    cursor: 'pointer',
    minWidth: '200px',
  },
  selectIcon: {
    position: 'absolute',
    right: '0.5rem',
    color: '#8a8578',
    pointerEvents: 'none',
  },
  
  messagesContainer: {
    flex: 1,
    overflowY: 'auto',
    padding: '1.5rem',
    display: 'flex',
    flexDirection: 'column',
    gap: '1rem',
  },
  emptyState: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    height: '100%',
    textAlign: 'center',
    color: '#8a8578',
  },
  emptyIcon: {
    color: '#c9a227',
    opacity: 0.5,
    marginBottom: '1rem',
  },
  emptyTitle: {
    fontSize: '1.5rem',
    color: '#f5f0e1',
    marginBottom: '0.5rem',
  },
  emptyText: {
    maxWidth: '500px',
    lineHeight: 1.6,
  },
  message: {
    padding: '1rem',
    borderRadius: '0.5rem',
    maxWidth: '85%',
  },
  userMessage: {
    backgroundColor: '#2d2a1f',
    alignSelf: 'flex-end',
    borderBottomRightRadius: '0.125rem',
  },
  assistantMessage: {
    backgroundColor: '#252218',
    alignSelf: 'flex-start',
    borderBottomLeftRadius: '0.125rem',
    border: '1px solid #3d3a2f',
  },
  errorMessage: {
    borderColor: '#7f1d1d',
    backgroundColor: '#2d1f1f',
  },
  messageHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.75rem',
    marginBottom: '0.5rem',
    fontSize: '0.8rem',
  },
  messageRole: {
    fontWeight: 600,
    color: '#c9a227',
  },
  messageTime: {
    color: '#6b6558',
  },
  modelBadge: {
    backgroundColor: '#3d3a2f',
    padding: '0.125rem 0.5rem',
    borderRadius: '0.25rem',
    fontSize: '0.7rem',
    color: '#8a8578',
  },
  messageContent: {
    lineHeight: 1.7,
    whiteSpace: 'pre-wrap',
  },
  
  // NEW: Citation Styles
  citationsContainer: {
    marginTop: '1rem',
    paddingTop: '1rem',
    borderTop: '1px solid #3d3a2f',
  },
  citationsHeader: {
    fontSize: '0.8rem',
    color: '#8a8578',
    marginBottom: '0.75rem',
    fontWeight: 600,
  },
  citation: {
    display: 'flex',
    gap: '0.5rem',
    padding: '0.5rem',
    marginBottom: '0.5rem',
    backgroundColor: '#1a1915',
    borderRadius: '0.375rem',
    fontSize: '0.85rem',
  },
  citationIcon: {
    color: '#c9a227',
    flexShrink: 0,
    marginTop: '0.125rem',
  },
  citationContent: {
    flex: 1,
  },
  citationTitle: {
    color: '#e8e4d9',
    fontWeight: 500,
  },
  citationMeta: {
    color: '#8a8578',
    fontSize: '0.75rem',
    marginTop: '0.25rem',
  },
  
  // NEW: Research Paper Citation Styles
  researchCitation: {
    padding: '0.75rem',
    marginBottom: '0.75rem',
    backgroundColor: '#1a1915',
    borderRadius: '0.375rem',
    border: '1px solid #3d3a2f',
    fontSize: '0.85rem',
  },
  researchHeader: {
    display: 'flex',
    alignItems: 'flex-start',
    gap: '0.5rem',
    marginBottom: '0.5rem',
  },
  researchIcon: {
    color: '#4ade80',
    flexShrink: 0,
    marginTop: '0.125rem',
  },
  researchTitle: {
    color: '#e8e4d9',
    fontWeight: 500,
    textDecoration: 'none',
    flex: 1,
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
    transition: 'color 0.2s',
  },
  externalLink: {
    color: '#8a8578',
  },
  researchMetadata: {
    display: 'flex',
    flexDirection: 'column',
    gap: '0.5rem',
    fontSize: '0.75rem',
    color: '#8a8578',
  },
  metaRow: {
    display: 'flex',
    alignItems: 'center',
    gap: '1rem',
    flexWrap: 'wrap',
  },
  metaItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.375rem',
  },
  sourceBadge: {
    backgroundColor: '#3d3a2f',
    padding: '0.125rem 0.5rem',
    borderRadius: '0.25rem',
    fontSize: '0.7rem',
    fontWeight: 600,
  },
  relevanceBadge: {
    backgroundColor: '#2d4a2f',
    color: '#4ade80',
    padding: '0.125rem 0.5rem',
    borderRadius: '0.25rem',
    fontSize: '0.7rem',
    fontWeight: 600,
  },
  topicTags: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.375rem',
    flexWrap: 'wrap',
  },
  topicTag: {
    backgroundColor: '#3d3a2f',
    padding: '0.125rem 0.5rem',
    borderRadius: '0.25rem',
    fontSize: '0.65rem',
  },
  paperSummary: {
    marginTop: '0.5rem',
    paddingTop: '0.5rem',
    borderTop: '1px solid #3d3a2f',
    fontSize: '0.75rem',
    lineHeight: 1.5,
    color: '#8a8578',
    fontStyle: 'italic',
  },
  
  loadingIndicator: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.75rem',
    padding: '1rem',
    color: '#8a8578',
    fontStyle: 'italic',
  },
  spinner: {
    animation: 'spin 1s linear infinite',
  },
  inputContainer: {
    padding: '1rem 1.5rem',
    backgroundColor: '#252218',
    borderTop: '1px solid #3d3a2f',
  },
  inputWrapper: {
    display: 'flex',
    gap: '0.75rem',
    alignItems: 'flex-end',
  },
  input: {
    flex: 1,
    backgroundColor: '#1a1915',
    color: '#e8e4d9',
    border: '1px solid #3d3a2f',
    borderRadius: '0.5rem',
    padding: '0.75rem 1rem',
    fontSize: '1rem',
    fontFamily: 'inherit',
    resize: 'none',
    outline: 'none',
    minHeight: '2.75rem',
    maxHeight: '150px',
  },
  sendButton: {
    backgroundColor: '#c9a227',
    color: '#1a1915',
    border: 'none',
    borderRadius: '0.5rem',
    padding: '0.75rem 1rem',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    transition: 'all 0.2s',
    fontWeight: 600,
  },
};

// Add keyframe animations
const styleSheet = document.createElement('style');
styleSheet.textContent = `
  @keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }
  
  /* VSC Logo Animations */
  .vsc-logo .vsc-rings {
    animation: vsc-rotate 25s linear infinite;
    transform-origin: 300px 300px;
  }
  
  .vsc-logo .vsc-core {
    animation: vsc-pulse 2s ease-in-out infinite;
    transform-origin: 300px 300px;
  }
  
  @keyframes vsc-rotate {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }
  
  @keyframes vsc-pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.7; }
  }
  
  /* Hover effects */
  .vsc-logo:hover .vsc-rings {
    animation-duration: 15s;
  }
  
  a:hover {
    color: #c9a227 !important;
  }
  
  button:hover {
    background-color: #3d3a2f !important;
  }
  
  @import url('https://fonts.googleapis.com/css2?family=Crimson+Pro:wght@400;600&display=swap');
`;
document.head.appendChild(styleSheet);
