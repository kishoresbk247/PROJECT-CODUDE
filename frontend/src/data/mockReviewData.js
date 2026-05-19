/**
 * mockReviewData.js — Hardcoded mock CodeReviewResponse
 *
 * Simulates the API response shape from the FastAPI backend.
 * Used to populate all panels in ReviewPage before API wiring (Day 18).
 */

const MOCK_REVIEW_RESPONSE = {
  overall_score: 72,
  summary:
    'The code demonstrates reasonable logic but contains a potential SQL injection vulnerability, ' +
    'an unchecked null dereference, and uses a brute-force O(n²) sorting approach. ' +
    'Refactoring to parameterized queries and optimized algorithms is strongly recommended.',

  bugs: [
    {
      severity: 'critical',
      line: 14,
      message:
        'Potential NullPointerException: `user.getProfile()` is called without a null check, ' +
        'which will throw if the user object is null.',
      suggestion:
        'Add a null guard before accessing `user.getProfile()`, e.g. `if (user != null && user.getProfile() != null)`.',
    },
    {
      severity: 'high',
      line: 27,
      message:
        'Array index out of bounds: The loop iterates `i <= arr.length` instead of `i < arr.length`, ' +
        'causing an off-by-one error on the last iteration.',
      suggestion:
        'Change the loop condition to `i < arr.length` to prevent accessing an undefined index.',
    },
    {
      severity: 'medium',
      line: 42,
      message:
        'Unused variable `tempResult` is assigned but never read, leading to dead code.',
      suggestion:
        'Remove the unused variable or use it in the subsequent computation.',
    },
    {
      severity: 'low',
      line: 8,
      message:
        'Magic number 86400 used directly. Consider extracting to a named constant for readability.',
      suggestion:
        'Define `const SECONDS_PER_DAY = 86400;` and reference it instead of the raw number.',
    },
  ],

  security: [
    {
      severity: 'critical',
      line: 19,
      message:
        'SQL Injection: User input is directly concatenated into a SQL query string ' +
        'without sanitization or parameterized queries.',
      suggestion:
        'Use parameterized queries or an ORM to prevent SQL injection. ' +
        'Example: `cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))`',
      owasp_category: 'A03:2021 – Injection',
    },
    {
      severity: 'high',
      line: 35,
      message:
        'Hardcoded API key found in source code. Secrets should never be stored in version-controlled files.',
      suggestion:
        'Move the API key to environment variables and access via `process.env.API_KEY` or a secrets manager.',
      owasp_category: 'A02:2021 – Cryptographic Failures',
    },
    {
      severity: 'medium',
      line: null,
      message:
        'No rate limiting is implemented on the authentication endpoint, making it susceptible to brute-force attacks.',
      suggestion:
        'Implement rate limiting middleware (e.g., express-rate-limit) to throttle repeated login attempts.',
      owasp_category: 'A07:2021 – Identification Failures',
    },
  ],

  complexity: {
    time_complexity: 'O(n²)',
    space_complexity: 'O(n)',
    explanation:
      'The dominant cost comes from the nested loop in `bubble_sort`, giving O(n²) time. ' +
      'The `merge_results` function allocates a new list proportional to input size, giving O(n) space.',
    complexity_scores: [
      {
        function_name: 'bubble_sort',
        time_complexity: 'O(n²)',
        space_complexity: 'O(1)',
        score: 3,
      },
      {
        function_name: 'find_max',
        time_complexity: 'O(n)',
        space_complexity: 'O(1)',
        score: 8,
      },
      {
        function_name: 'merge_results',
        time_complexity: 'O(n)',
        space_complexity: 'O(n)',
        score: 7,
      },
      {
        function_name: 'validate_input',
        time_complexity: 'O(1)',
        space_complexity: 'O(1)',
        score: 10,
      },
      {
        function_name: 'search_users',
        time_complexity: 'O(n log n)',
        space_complexity: 'O(log n)',
        score: 6,
      },
    ],
  },
};

export default MOCK_REVIEW_RESPONSE;
