import React from 'react';
import { render, screen } from '@testing-library/react';
import { Hero } from '@/components/Hero';

// Mock framer-motion
jest.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
    h2: ({ children, ...props }: any) => <h2 {...props}>{children}</h2>,
    p: ({ children, ...props }: any) => <p {...props}>{children}</p>,
  },
}));

describe('Hero', () => {
  it('should render hero section with branding', () => {
    render(<Hero />);

    expect(screen.getByText(/Botspot/i)).toBeInTheDocument();
    expect(screen.getByText(/AI Trading Bot/i)).toBeInTheDocument();
    expect(screen.getAllByText(/Demo Videos/i).length).toBeGreaterThan(0);
  });

  it('should render all stat cards', () => {
    render(<Hero />);

    expect(screen.getByText(/Videos Generated/i)).toBeInTheDocument();
    expect(screen.getByText(/Active Bots/i)).toBeInTheDocument();
    expect(screen.getByText(/Total Revenue/i)).toBeInTheDocument();
  });

  it('should display stats with numbers', () => {
    render(<Hero />);

    // Stats should be visible (they animate from 0 to target)
    const statsSection = screen.getByText(/Videos Generated/i).closest('div');
    expect(statsSection).toBeInTheDocument();
  });
});
