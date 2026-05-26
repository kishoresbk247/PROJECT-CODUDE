/**
 * ReviewPage.jsx — Code Review Page (Day 18 — API Integration)
 *
 * Day 18 changes:
 *   ✅ useReview() now calls real FastAPI backend (no mock data)
 *   ✅ AbortController cancels in-flight requests on rapid re-submission
 *   ✅ cancel() destructured and called in useEffect cleanup on unmount
 *        → prevents "state update on unmounted component" React warnings
 *   ✅ VITE_API_BASE_URL drives the axios baseURL (frontend/.env)
 *
 * Previous (Day 17):
 *   ✅ LoadingSkeleton, ErrorBanner, EmptyState, LanguageSelector
 *   ✅ Ctrl/Cmd + Enter keyboard shortcut
 *   ✅ Responsive layout (< 768px stack)
 */


import { useState, useCallback, useRef, useEffect } from 'react';
import CodeEditor from '../components/CodeEditor';
import ResultsTabs from '../components/ResultsTabs';
import LoadingSkeleton from '../components/LoadingSkeleton';
import ErrorBanner from '../components/ErrorBanner';
import LanguageSelector, { LANGUAGES } from '../components/LanguageSelector';
import { useReview } from '../hooks/useReview';
import './ReviewPage.css';

/* ── Sample code per language ─────────────────────────────────────────────── */
const SAMPLE_CODE = {
  python: `def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr

def find_max(arr):
    max_val = arr[0]
    for item in arr:
        if item > max_val:
            max_val = item
    return max_val

user = get_user(user_id)
profile = user.getProfile()
query = "SELECT * FROM users WHERE id = " + user_id
API_KEY = "sk-secret-1234567890"`,

  javascript: `function bubbleSort(arr) {
  const n = arr.length;
  for (let i = 0; i <= n; i++) {
    for (let j = 0; j < n - i - 1; j++) {
      if (arr[j] > arr[j + 1]) {
        [arr[j], arr[j + 1]] = [arr[j + 1], arr[j]];
      }
    }
  }
  return arr;
}

const tempResult = compute();
const SECONDS = 86400;`,

  java: `public class Main {
    public static void main(String[] args) {
        int[] arr = {5, 3, 8, 1, 2};
        bubbleSort(arr);
    }

    static void bubbleSort(int[] arr) {
        for (int i = 0; i < arr.length; i++)
            for (int j = 0; j < arr.length - 1; j++)
                if (arr[j] > arr[j+1]) {
                    int t = arr[j];
                    arr[j] = arr[j+1];
                    arr[j+1] = t;
                }
    }
}`,

  cpp: `#include <vector>
#include <iostream>

void bubbleSort(std::vector<int>& arr) {
    for (size_t i = 0; i < arr.size(); i++)
        for (size_t j = 0; j < arr.size()-1; j++)
            if (arr[j] > arr[j+1])
                std::swap(arr[j], arr[j+1]);
}

int main() {
    std::vector<int> v = {5,3,8,1,2};
    bubbleSort(v);
    return 0;
}`,

  auto: `# Auto-detect mode — paste any code below
def hello():
    print("Hello, World!")
`,
};

/* ── Component ─────────────────────────────────────────────────────────────── */
export default function ReviewPage() {
  const [language, setLanguage]   = useState('python');
  const [code, setCode]           = useState(SAMPLE_CODE.python);
  const editorViewRef             = useRef(null);

  // ── Day 18: useReview custom hook (with cancel for unmount cleanup) ──────
  const { review, isLoading, error, result, clearError, cancel } = useReview();

  // ── Day 18: Cancel in-flight request on unmount ─────────────────────────
  // Prevents "Can't perform a React state update on an unmounted component"
  // if the user navigates away while an LLM review is in progress.
  useEffect(() => {
    return () => cancel();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ── Language change ─────────────────────────────────────────────────────
  const handleLanguageChange = useCallback((newLang) => {
    setLanguage(newLang);
    setCode(SAMPLE_CODE[newLang] || '');
  }, []);

  // ── Submit / review ─────────────────────────────────────────────────────
  const handleSubmit = useCallback(() => {
    review(code, language);
  }, [code, language, review]);

  // ── Keyboard shortcut: Cmd/Ctrl + Enter ────────────────────────────────
  useEffect(() => {
    function handleKeyDown(e) {
      if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
        e.preventDefault();
        if (!isLoading && code.trim()) {
          handleSubmit();
        }
      }
    }
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleSubmit, isLoading, code]);

  // ── Jump to line in editor ──────────────────────────────────────────────
  const handleJumpToLine = useCallback((line) => {
    const view = editorViewRef.current;
    if (!view) return;
    const lineInfo = view.state.doc.line(Math.min(line, view.state.doc.lines));
    view.dispatch({
      selection: { anchor: lineInfo.from },
      scrollIntoView: true,
    });
    view.focus();
  }, []);

  // ── Derived UI helpers ──────────────────────────────────────────────────
  const fileExt =
    language === 'cpp' ? 'cpp'
    : language === 'java' ? 'java'
    : language === 'javascript' ? 'js'
    : language === 'auto' ? 'txt'
    : 'py';

  const shortcutHint =
    typeof navigator !== 'undefined' && /Mac/i.test(navigator.platform)
      ? '⌘ + Enter'
      : 'Ctrl + Enter';

  /* ── Render ─────────────────────────────────────────────────────────── */
  return (
    <div className="review-page">
      {/* ── Header ── */}
      <div className="review-header animate-slide-up">
        <h1 className="review-title">
          Code <span className="gradient-text">Review</span>
        </h1>
        <p className="review-subtitle">
          Paste your code, select a language, and get instant AI-powered
          feedback on bugs, security, and complexity.
        </p>
        <div className="review-shortcut-hint" aria-label={`Keyboard shortcut: ${shortcutHint} to run review`}>
          <kbd className="kbd">{shortcutHint}</kbd>
          <span>to run review</span>
        </div>
      </div>

      {/* ── Split Layout ── */}
      <div className="review-split">

        {/* ── Left Panel: Code Editor ── */}
        <div className="review-panel review-panel--editor animate-slide-up" style={{ animationDelay: '100ms' }}>
          <div className="editor-panel glass">

            {/* Toolbar */}
            <div className="editor-toolbar">
              <div className="toolbar-left">
                <div className="toolbar-dots">
                  <span className="dot dot-red" />
                  <span className="dot dot-yellow" />
                  <span className="dot dot-green" />
                </div>
                <span className="toolbar-filename">code.{fileExt}</span>
              </div>
              <div className="toolbar-right">
                {/* Day 17: LanguageSelector component */}
                <LanguageSelector value={language} onChange={handleLanguageChange} />
              </div>
            </div>

            {/* Editor */}
            <div className="editor-wrapper" id="code-editor">
              <CodeEditor
                value={code}
                onChange={setCode}
                language={language === 'auto' ? 'python' : language}
                height="calc(100vh - 360px)"
                onEditorReady={(view) => { editorViewRef.current = view; }}
              />
            </div>

            {/* Footer */}
            <div className="editor-footer">
              <div className="char-count">
                {code.length.toLocaleString()} chars · {code.split('\n').length} lines
              </div>
              <button
                className="btn btn-primary btn-submit"
                onClick={handleSubmit}
                disabled={isLoading || !code.trim()}
                id="submit-review-button"
                title={`Review code (${shortcutHint})`}
              >
                {isLoading ? (
                  <><span className="spinner" /> Analyzing…</>
                ) : (
                  <span>⚡ Review Code</span>
                )}
              </button>
            </div>
          </div>
        </div>

        {/* ── Right Panel: Results ── */}
        <div className="review-panel review-panel--results animate-slide-up" style={{ animationDelay: '200ms' }}>

          {/* Day 17: ErrorBanner component */}
          <ErrorBanner
            error={error}
            onDismiss={clearError}
            onRetry={() => { clearError(); handleSubmit(); }}
          />

          {/* Day 17: LoadingSkeleton while fetching */}
          {isLoading && <LoadingSkeleton cardCount={3} />}

          {/* Results tabs when done */}
          {!isLoading && result && (
            <ResultsTabs result={result} onJumpToLine={handleJumpToLine} />
          )}

          {/* Placeholder when nothing has been run yet */}
          {!isLoading && !result && !error && (
            <div className="results-placeholder glass" id="results-placeholder">
              <div className="results-placeholder__icon">🔍</div>
              <h3 className="results-placeholder__title">Ready to Analyze</h3>
              <p className="results-placeholder__text">
                Write or paste code in the editor, then click{' '}
                <strong>⚡ Review Code</strong> (or press{' '}
                <kbd className="kbd kbd--inline">{shortcutHint}</kbd>) to see results here.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
