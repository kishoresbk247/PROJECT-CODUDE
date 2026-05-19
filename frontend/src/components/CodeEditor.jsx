/**
 * CodeEditor.jsx — Reusable CodeMirror wrapper
 *
 * Wraps @uiw/react-codemirror with automatic language-extension switching.
 *
 * Props:
 *   value      — current source code string
 *   onChange   — callback(newValue) fired on every keystroke
 *   language   — 'python' | 'javascript' | 'java' | 'cpp'
 *   height     — CSS height for the editor (default '100%')
 *   onEditorReady — optional callback(EditorView) for imperative access
 */

import CodeMirror from '@uiw/react-codemirror';
import { javascript } from '@codemirror/lang-javascript';
import { python } from '@codemirror/lang-python';
import { java } from '@codemirror/lang-java';
import { cpp } from '@codemirror/lang-cpp';
import { vscodeDark } from '@uiw/codemirror-theme-vscode';

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
      return python();
  }
}

export default function CodeEditor({
  value,
  onChange,
  language = 'python',
  height = '100%',
  onEditorReady,
}) {
  return (
    <CodeMirror
      value={value}
      height={height}
      theme={vscodeDark}
      extensions={[getLanguageExtension(language)]}
      onChange={(val) => onChange?.(val)}
      onCreateEditor={(view) => onEditorReady?.(view)}
      placeholder="Paste your code here..."
      basicSetup={{
        lineNumbers: true,
        highlightActiveLineGutter: true,
        highlightActiveLine: true,
        foldGutter: true,
        autocompletion: false,
      }}
    />
  );
}
