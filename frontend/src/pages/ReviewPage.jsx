/**
 * ReviewPage.jsx — Code Review Page (Day 16 refactor)
 *
 * Split-panel layout:
 *   Left  — CodeEditor with language selector & submit button
 *   Right — ResultsTabs with ScoreGauge at the top
 *
 * Hardcodes a mock CodeReviewResponse to populate all panels.
 * API wiring comes on Day 18.
 */

import { useState, useCallback, useRef } from 'react';
import CodeEditor from '../components/CodeEditor';
import ResultsTabs from '../components/ResultsTabs';
import MOCK_REVIEW_RESPONSE from '../data/mockReviewData';
import './ReviewPage.css';

const LANGUAGES = [
  { value: 'python', label: 'Python', icon: '🐍' },
  { value: 'javascript', label: 'JavaScript', icon: '🟨' },
  { value: 'java', label: 'Java', icon: '☕' },
  { value: 'cpp', label: 'C++', icon: '⚙️' },
];

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
};

export default function ReviewPage() {
  const [language, setLanguage] = useState('python');
  const [code, setCode] = useState(SAMPLE_CODE.python);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(MOCK_REVIEW_RESPONSE);
  const [error, setError] = useState(null);
  const editorViewRef = useRef(null);

  const handleLanguageChange = useCallback((e) => {
    const lang = e.target.value;
    setLanguage(lang);
    setCode(SAMPLE_CODE[lang] || '');
  }, []);

  const handleSubmit = useCallback(async () => {
    if (!code.trim()) {
      setError('Please enter some code to review.');
      return;
    }
    setLoading(true);
    setError(null);

    // Simulate API call — will be replaced with real axios call on Day 18
    await new Promise((r) => setTimeout(r, 1500));
    setResult(MOCK_REVIEW_RESPONSE);
    setLoading(false);
  }, [code]);

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

  const fileExt = language === 'cpp' ? 'cpp' : language === 'java' ? 'java' : language === 'javascript' ? 'js' : 'py';

  return (
    <div className="review-page">
      {/* Header */}
      <div className="review-header animate-slide-up">
        <h1 className="review-title">
          Code <span className="gradient-text">Review</span>
        </h1>
        <p className="review-subtitle">
          Paste your code below, select a language, and get instant AI-powered
          feedback on bugs, security, and complexity.
        </p>
      </div>

      {/* Split Layout */}
      <div className="review-split">
        {/* ── Left Panel: Code Editor ── */}
        <div className="review-panel review-panel--editor animate-slide-up" style={{ animationDelay: '100ms' }}>
          <div className="editor-panel glass">
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
                <select
                  id="language-selector"
                  className="language-select"
                  value={language}
                  onChange={handleLanguageChange}
                >
                  {LANGUAGES.map((l) => (
                    <option key={l.value} value={l.value}>
                      {l.icon} {l.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="editor-wrapper" id="code-editor">
              <CodeEditor
                value={code}
                onChange={setCode}
                language={language}
                height="calc(100vh - 340px)"
                onEditorReady={(view) => { editorViewRef.current = view; }}
              />
            </div>

            <div className="editor-footer">
              <div className="char-count">
                {code.length} chars · {code.split('\n').length} lines
              </div>
              <button
                className="btn btn-primary btn-submit"
                onClick={handleSubmit}
                disabled={loading || !code.trim()}
                id="submit-review-button"
              >
                {loading ? (
                  <><span className="spinner" /> Analyzing...</>
                ) : (
                  <span>⚡ Review Code</span>
                )}
              </button>
            </div>
          </div>
        </div>

        {/* ── Right Panel: Results ── */}
        <div className="review-panel review-panel--results animate-slide-up" style={{ animationDelay: '200ms' }}>
          {error && (
            <div className="error-banner" id="error-message">
              <span>⚠️</span>
              <span>{error}</span>
            </div>
          )}

          {result ? (
            <ResultsTabs result={result} onJumpToLine={handleJumpToLine} />
          ) : (
            <div className="results-placeholder glass">
              <div className="results-placeholder__icon">🔍</div>
              <h3 className="results-placeholder__title">Ready to Analyze</h3>
              <p className="results-placeholder__text">
                Write or paste code in the editor, then click
                <strong> ⚡ Review Code</strong> to see results here.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
