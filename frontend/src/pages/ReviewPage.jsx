/**
 * ReviewPage.jsx — Code Review Page
 *
 * Contains:
 *  - A CodeMirror editor for code input
 *  - A language selector dropdown (Python, JavaScript, Java, C++)
 *  - A "Review Code" submit button
 *  - Results panel showing the review response
 *
 * The submit handler calls the FastAPI backend via axios and
 * displays the response in a styled results panel.
 */

import { useState, useCallback } from 'react';
import CodeMirror from '@uiw/react-codemirror';
import { javascript } from '@codemirror/lang-javascript';
import { python } from '@codemirror/lang-python';
import { java } from '@codemirror/lang-java';
import { cpp } from '@codemirror/lang-cpp';
import { vscodeDark } from '@uiw/codemirror-theme-vscode';
import axios from 'axios';
import './ReviewPage.css';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const LANGUAGES = [
  { value: 'python', label: 'Python', icon: '🐍' },
  { value: 'javascript', label: 'JavaScript', icon: '🟨' },
  { value: 'java', label: 'Java', icon: '☕' },
  { value: 'cpp', label: 'C++', icon: '⚙️' },
];

const SAMPLE_CODE = {
  python: `def find_duplicates(lst):
    """Find duplicate elements in a list."""
    seen = set()
    duplicates = []
    for item in lst:
        if item in seen:
            duplicates.append(item)
        seen.add(item)
    return duplicates

# Usage
result = find_duplicates([1, 2, 3, 2, 4, 3, 5])
print(result)`,

  javascript: `function findDuplicates(arr) {
  const seen = new Set();
  const duplicates = [];
  for (const item of arr) {
    if (seen.has(item)) {
      duplicates.push(item);
    }
    seen.add(item);
  }
  return duplicates;
}

// Usage
const result = findDuplicates([1, 2, 3, 2, 4, 3, 5]);
console.log(result);`,

  java: `import java.util.*;

public class DuplicateFinder {
    public static List<Integer> findDuplicates(int[] arr) {
        Set<Integer> seen = new HashSet<>();
        List<Integer> duplicates = new ArrayList<>();
        for (int item : arr) {
            if (!seen.add(item)) {
                duplicates.add(item);
            }
        }
        return duplicates;
    }

    public static void main(String[] args) {
        int[] arr = {1, 2, 3, 2, 4, 3, 5};
        System.out.println(findDuplicates(arr));
    }
}`,

  cpp: `#include <iostream>
#include <vector>
#include <unordered_set>

std::vector<int> findDuplicates(const std::vector<int>& arr) {
    std::unordered_set<int> seen;
    std::vector<int> duplicates;
    for (int item : arr) {
        if (seen.count(item)) {
            duplicates.push_back(item);
        }
        seen.insert(item);
    }
    return duplicates;
}

int main() {
    std::vector<int> arr = {1, 2, 3, 2, 4, 3, 5};
    auto result = findDuplicates(arr);
    for (int x : result) std::cout << x << " ";
    return 0;
}`,
};

/** Returns the CodeMirror language extension for the selected language */
function getLanguageExtension(lang) {
  switch (lang) {
    case 'python':
      return python();
    case 'javascript':
      return javascript({ jsx: true });
    case 'java':
      return java();
    case 'cpp':
      return cpp();
    default:
      return javascript();
  }
}

/** Maps severity to a CSS class */
function severityClass(severity) {
  switch (severity) {
    case 'critical':
      return 'severity-critical';
    case 'high':
      return 'severity-high';
    case 'medium':
      return 'severity-medium';
    case 'low':
      return 'severity-low';
    default:
      return '';
  }
}

export default function ReviewPage() {
  const [language, setLanguage] = useState('python');
  const [code, setCode] = useState(SAMPLE_CODE.python);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  /** Handle language change — also swaps in sample code */
  const handleLanguageChange = useCallback((e) => {
    const newLang = e.target.value;
    setLanguage(newLang);
    setCode(SAMPLE_CODE[newLang] || '');
    setResult(null);
    setError(null);
  }, []);

  /** Submit code for review */
  const handleSubmit = useCallback(async () => {
    if (!code.trim()) {
      setError('Please enter some code to review.');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const payload = { code, language };
      console.log('📤 Sending review request:', payload);

      const response = await axios.post(
        `${API_BASE}/api/v1/review`,
        payload
      );

      console.log('📥 Review response:', response.data);
      setResult(response.data);
    } catch (err) {
      const message =
        err.response?.data?.detail ||
        err.message ||
        'Failed to connect to the API server.';
      console.error('❌ Review error:', err);
      setError(message);
    } finally {
      setLoading(false);
    }
  }, [code, language]);

  return (
    <div className="review-page">
      <div className="review-container">
        {/* ── Header ── */}
        <div className="review-header animate-slide-up">
          <h1 className="review-title">
            Code <span className="gradient-text">Review</span>
          </h1>
          <p className="review-subtitle">
            Paste your code below, select a language, and get instant AI-powered
            feedback on bugs, security, and complexity.
          </p>
        </div>

        {/* ── Editor Panel ── */}
        <div className="editor-panel glass animate-slide-up" style={{ animationDelay: '100ms' }}>
          {/* Toolbar */}
          <div className="editor-toolbar">
            <div className="toolbar-left">
              <div className="toolbar-dots">
                <span className="dot dot-red" />
                <span className="dot dot-yellow" />
                <span className="dot dot-green" />
              </div>
              <span className="toolbar-filename">
                code.{language === 'cpp' ? 'cpp' : language === 'java' ? 'java' : language === 'javascript' ? 'js' : 'py'}
              </span>
            </div>

            <div className="toolbar-right">
              <select
                id="language-selector"
                className="language-select"
                value={language}
                onChange={handleLanguageChange}
              >
                {LANGUAGES.map((lang) => (
                  <option key={lang.value} value={lang.value}>
                    {lang.icon} {lang.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* CodeMirror Editor */}
          <div className="editor-wrapper" id="code-editor">
            <CodeMirror
              value={code}
              height="380px"
              theme={vscodeDark}
              extensions={[getLanguageExtension(language)]}
              onChange={(value) => setCode(value)}
              placeholder="Paste your code here..."
              basicSetup={{
                lineNumbers: true,
                highlightActiveLineGutter: true,
                highlightActiveLine: true,
                foldGutter: true,
                autocompletion: false,
              }}
            />
          </div>

          {/* Submit Button */}
          <div className="editor-footer">
            <div className="char-count">
              {code.length} characters · {code.split('\n').length} lines
            </div>
            <button
              className="btn btn-primary btn-submit"
              onClick={handleSubmit}
              disabled={loading || !code.trim()}
              id="submit-review-button"
            >
              {loading ? (
                <>
                  <span className="spinner" />
                  Analyzing...
                </>
              ) : (
                <>
                  <span>⚡ Review Code</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* ── Error Message ── */}
        {error && (
          <div className="error-banner animate-slide-up" id="error-message">
            <span className="error-icon">⚠️</span>
            <span>{error}</span>
          </div>
        )}

        {/* ── Results Panel ── */}
        {result && (
          <div className="results-panel animate-slide-up" id="results-panel">
            {/* Score Header */}
            <div className="score-header glass">
              <div className="score-circle">
                <svg viewBox="0 0 120 120" className="score-ring">
                  <circle cx="60" cy="60" r="52" className="score-ring-bg" />
                  <circle
                    cx="60"
                    cy="60"
                    r="52"
                    className="score-ring-fill"
                    style={{
                      strokeDasharray: `${(result.overall_score / 100) * 327} 327`,
                    }}
                  />
                </svg>
                <span className="score-value">{result.overall_score}</span>
              </div>
              <div className="score-info">
                <h2 className="score-label">Overall Score</h2>
                <p className="score-summary">{result.summary}</p>
              </div>
            </div>

            {/* Bug Findings */}
            {result.bugs && result.bugs.length > 0 && (
              <div className="findings-section">
                <h3 className="findings-title">
                  <span className="findings-icon">🐛</span>
                  Bug Findings ({result.bugs.length})
                </h3>
                <div className="findings-list">
                  {result.bugs.map((bug, i) => (
                    <div key={i} className="finding-card glass">
                      <div className="finding-header">
                        <span className={`severity-badge ${severityClass(bug.severity)}`}>
                          {bug.severity}
                        </span>
                        {bug.line && (
                          <span className="finding-line">Line {bug.line}</span>
                        )}
                      </div>
                      <p className="finding-message">{bug.message}</p>
                      <p className="finding-suggestion">
                        💡 <strong>Fix:</strong> {bug.suggestion}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Security Findings */}
            {result.security && result.security.length > 0 && (
              <div className="findings-section">
                <h3 className="findings-title">
                  <span className="findings-icon">🔒</span>
                  Security Findings ({result.security.length})
                </h3>
                <div className="findings-list">
                  {result.security.map((sec, i) => (
                    <div key={i} className="finding-card glass">
                      <div className="finding-header">
                        <span className={`severity-badge ${severityClass(sec.severity)}`}>
                          {sec.severity}
                        </span>
                        <span className="owasp-badge">{sec.owasp_category}</span>
                      </div>
                      <p className="finding-message">{sec.message}</p>
                      <p className="finding-suggestion">
                        💡 <strong>Fix:</strong> {sec.suggestion}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Complexity Analysis */}
            {result.complexity && (
              <div className="findings-section">
                <h3 className="findings-title">
                  <span className="findings-icon">⚡</span>
                  Complexity Analysis
                </h3>
                <div className="complexity-card glass">
                  <div className="complexity-metrics">
                    <div className="complexity-metric">
                      <span className="complexity-label">Time</span>
                      <span className="complexity-value gradient-text">
                        {result.complexity.time_complexity}
                      </span>
                    </div>
                    <div className="complexity-metric">
                      <span className="complexity-label">Space</span>
                      <span className="complexity-value gradient-text">
                        {result.complexity.space_complexity}
                      </span>
                    </div>
                  </div>
                  <p className="complexity-explanation">
                    {result.complexity.explanation}
                  </p>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
