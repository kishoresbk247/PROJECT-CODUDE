import { defineConfig } from 'cypress';

export default defineConfig({
  e2e: {
    // Base URL of the Vite dev server
    baseUrl: 'http://localhost:5173',

    // Where spec files live
    specPattern: 'cypress/e2e/**/*.cy.{js,jsx,ts,tsx}',

    // Viewport matching a typical laptop
    viewportWidth: 1280,
    viewportHeight: 800,

    // Allow more time for LLM-backed responses
    defaultCommandTimeout: 30_000,
    responseTimeout: 120_000,
    pageLoadTimeout: 30_000,

    // Useful for CI: don't open a browser window
    video: false,
    screenshotOnRunFailure: true,

    setupNodeEvents(on, config) {
      // No custom node events needed yet
      return config;
    },
  },
});
