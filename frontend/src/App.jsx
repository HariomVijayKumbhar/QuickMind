import { BrowserRouter, Routes, Route, Navigate, useLocation, useNavigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { DocumentProvider } from './context/DocumentContext';
import ProtectedRoute from './components/ProtectedRoute';
import Login from './pages/Login';
import Register from './pages/Register';
import Summarizer from './components/Summarizer';
import QuestionAnswer from './components/QuestionAnswer';
import ContentGenerator from './components/ContentGenerator';
import DocumentAnalyzer from './components/DocumentAnalyzer';
import SuggestionEngine from './components/SuggestionEngine';
import DocumentBanner from './components/DocumentBanner';

const TABS = [
  { id: 'summarizer', label: 'Summarize', Component: Summarizer },
  { id: 'ask', label: 'Ask', Component: QuestionAnswer },
  { id: 'generate', label: 'Generate', Component: ContentGenerator },
  { id: 'analyze', label: 'Analyze', Component: DocumentAnalyzer },
  { id: 'suggest', label: 'Suggest', Component: SuggestionEngine },
];

function AppContent() {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const currentPath = location.pathname === '/' ? 'summarizer' : location.pathname.replace('/', '');

  return (
    <Routes>
      <Route path="/login" element={user ? <Navigate to="/" replace /> : <Login />} />
      <Route path="/register" element={user ? <Navigate to="/" replace /> : <Register />} />
      <Route
        path="/*"
        element={
          <ProtectedRoute>
            <div className="app">
              <header>
                <div className="header-left">
                  <h1>Quickmind</h1>
                  <p>AI-powered productivity assistant</p>
                </div>
                <div className="header-right">
                  <span className="user-email">{user?.email}</span>
                  <button onClick={logout} className="logout-btn">Logout</button>
                </div>
              </header>
              <nav className="tabs">
                {TABS.map((tab) => (
                  <button
                    key={tab.id}
                    className={currentPath === tab.id ? 'active' : ''}
                    onClick={() => navigate(tab.id === 'summarizer' ? '/' : `/${tab.id}`)}
                  >
                    {tab.label}
                  </button>
                ))}
              </nav>
              <DocumentBanner />
              <main>
                <Routes>
                  {TABS.map((tab) => (
                    <Route key={tab.id} path={tab.id === 'summarizer' ? '/' : `/${tab.id}`} element={<tab.Component />} />
                  ))}
                </Routes>
              </main>
            </div>
          </ProtectedRoute>
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <AuthProvider>
        <DocumentProvider>
          <AppContent />
        </DocumentProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}
