/**
 * App entry: TanStack Query provider, router and the three routes.
 *   /             Command center
 *   /phone        Resident phone simulator
 *   /run/:runId   Volunteer route sheet
 *
 * Implements: PLAN.md §9 (frontend screens). Owner: P1 (Frontend and UX).
 */
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter, Route, Routes } from 'react-router-dom';
import './index.css';
import CommandCenter from './pages/CommandCenter';
import Phone from './pages/Phone';
import RunSheet from './pages/RunSheet';

// TODO(P1, §9): poll /dashboard every 3 s (refetchInterval: 3000) where it is queried.
const queryClient = new QueryClient();

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<CommandCenter />} />
          <Route path="/phone" element={<Phone />} />
          <Route path="/run/:runId" element={<RunSheet />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  </StrictMode>,
);
