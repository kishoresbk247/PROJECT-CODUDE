/**
 * App.jsx — Root Application Component
 *
 * Sets up react-router-dom with a Layout wrapper and three routes:
 *   /        → HomePage
 *   /review  → ReviewPage
 *   /about   → AboutPage
 */

import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import HomePage from './pages/HomePage';
import ReviewPage from './pages/ReviewPage';
import AboutPage from './pages/AboutPage';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<HomePage />} />
          <Route path="/review" element={<ReviewPage />} />
          <Route path="/about" element={<AboutPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
