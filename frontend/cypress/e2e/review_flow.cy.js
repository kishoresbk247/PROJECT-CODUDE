/**
 * review_flow.cy.js — E2E test for the full code review flow (Day 18)
 *
 * Flow tested:
 *   1. Visit the /review page
 *   2. Clear the editor and type a Python snippet with a security issue (eval)
 *   3. Click "⚡ Review Code"
 *   4. Wait for the loading skeleton to disappear
 *   5. Assert the results panel contains at least one finding card
 *
 * The test uses the real backend (must be running on localhost:8000).
 * Timeout is set to 120s to allow for LLM processing.
 *
 * Running:
 *   npx cypress open      ← interactive (headed)
 *   npx cypress run       ← headless (CI)
 */

describe('Code Review Flow', () => {
  beforeEach(() => {
    // Visit the review page before each test
    cy.visit('/review');
  });

  it('submits Python code with a security issue and sees findings in the results panel', () => {
    // ── Step 1: Confirm the page loaded ─────────────────────────────────────
    cy.get('.review-page').should('exist');
    cy.get('h1').should('contain', 'Review');

    // ── Step 2: Clear the editor and type a security-vulnerable snippet ──────
    // The CodeMirror editor renders inside .cm-content (contenteditable div)
    cy.get('.cm-content')
      .click()
      .focused()
      .type('{ctrl+a}', { force: true })  // select all existing text
      .type(
        // Python snippet with eval() — should trigger a security finding
        `def run_user_code(user_input):` +
        `\n    result = eval(user_input)` +
        `\n    return result` +
        `\n\n# Hardcoded secret` +
        `\nAPI_KEY = "sk-secret-abc123"` +
        `\npassword = "admin123"`,
        { force: true, delay: 10 },
      );

    // ── Step 3: Click the submit button ──────────────────────────────────────
    cy.get('#submit-review-button')
      .should('not.be.disabled')
      .click();

    // ── Step 4: Loading state should appear ──────────────────────────────────
    // The skeleton or spinner should be visible while the LLM is processing
    cy.get('.btn-submit').should('contain', 'Analyzing');

    // ── Step 5: Wait for results (allow up to 120 seconds for LLM) ───────────
    cy.get('.btn-submit', { timeout: 120_000 })
      .should('not.contain', 'Analyzing');

    // ── Step 6: Assert results panel has findings ─────────────────────────────
    // At least one FindingCard should be in the DOM
    cy.get('.finding-card', { timeout: 10_000 })
      .should('have.length.at.least', 1);

    // ── Step 7: Assert at least one severity badge exists ─────────────────────
    cy.get('.severity-badge')
      .should('have.length.at.least', 1);

    // ── Step 8: The results tabs should be visible ────────────────────────────
    cy.get('.results-tabs').should('exist');
  });

  it('shows an error banner when the backend is unreachable', () => {
    // Intercept the review API call and force a network error
    cy.intercept('POST', '**/api/v1/review', { forceNetworkError: true }).as('reviewError');

    // Click submit without changing code
    cy.get('#submit-review-button').click();

    // Wait for the intercepted request
    cy.wait('@reviewError');

    // Error banner should appear
    cy.get('.error-banner', { timeout: 10_000 }).should('exist');
  });

  it('disables the submit button while loading', () => {
    // Intercept and delay the response
    cy.intercept('POST', '**/api/v1/review', (req) => {
      req.reply((res) => {
        res.delay = 3000;
      });
    }).as('slowReview');

    cy.get('#submit-review-button').click();

    // Button should be disabled while loading
    cy.get('#submit-review-button').should('be.disabled');

    // Wait for request to complete then button re-enables
    cy.wait('@slowReview', { timeout: 15_000 });
    cy.get('#submit-review-button', { timeout: 10_000 }).should('not.be.disabled');
  });
});
