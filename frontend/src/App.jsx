import { useState } from 'react';
import Summarizer from './components/Summarizer';
import QuestionAnswer from './components/QuestionAnswer';
import ContentGenerator from './components/ContentGenerator';
import DocumentAnalyzer from './components/DocumentAnalyzer';
import SuggestionEngine from './components/SuggestionEngine';

const TABS = [
  { id: 'summarizer', label: 'Summarize', Component: Summarizer },
  { id: 'ask', label: 'Ask', Component: QuestionAnswer },
  { id: 'generate', label: 'Generate', Component: ContentGenerator },
  { id: 'analyze', label: 'Analyze', Component: DocumentAnalyzer },
  { id: 'suggest', label: 'Suggest', Component: SuggestionEngine },
];

export default function App() {
  const [active, setActive] = useState('summarizer');
  const ActiveComponent = TABS.find((t) => t.id === active).Component;

  return (
    <div className="app">
      <header>
        <h1>Quickmind</h1>
        <p>AI-powered productivity assistant</p>
      </header>
      <nav className="tabs">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            className={active === tab.id ? 'active' : ''}
            onClick={() => setActive(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </nav>
      <main>
        <ActiveComponent />
      </main>
    </div>
  );
}
