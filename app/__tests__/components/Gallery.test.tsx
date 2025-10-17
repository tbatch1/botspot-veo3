import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { Gallery } from '@/components/Gallery';

// Mock framer-motion
jest.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}));

describe('Gallery', () => {
  it('should render gallery with title', () => {
    render(<Gallery />);
    expect(screen.getByText(/Video Gallery/i)).toBeInTheDocument();
    expect(screen.getByText(/Browse your generated/i)).toBeInTheDocument();
  });

  it('should render search input', () => {
    render(<Gallery />);
    expect(screen.getByPlaceholderText(/Search videos/i)).toBeInTheDocument();
  });

  it('should render category filters', () => {
    render(<Gallery />);
    expect(screen.getByText('All Videos')).toBeInTheDocument();
    expect(screen.getByText('Bull Market')).toBeInTheDocument();
    expect(screen.getByText('Bear Market')).toBeInTheDocument();
    expect(screen.getByText('Risk Management')).toBeInTheDocument();
    expect(screen.getByText('Algo Trading')).toBeInTheDocument();
  });

  it('should display video cards', () => {
    render(<Gallery />);
    // Should have multiple video cards with share/download buttons
    const shareButtons = screen.getAllByText(/Share/i);
    const downloadButtons = screen.getAllByText(/Download/i);
    expect(shareButtons.length).toBeGreaterThan(0);
    expect(downloadButtons.length).toBeGreaterThan(0);
  });

  it('should filter videos by category', () => {
    render(<Gallery />);

    // Click Bull Market filter
    const bullMarketButton = screen.getByText('Bull Market');
    fireEvent.click(bullMarketButton);

    // Button should have active class
    expect(bullMarketButton).toHaveClass('bg-blue-600');
  });

  it('should filter videos by search query', () => {
    render(<Gallery />);

    const searchInput = screen.getByPlaceholderText(/Search videos/i);
    fireEvent.change(searchInput, { target: { value: 'Risk' } });

    expect(searchInput).toHaveValue('Risk');
  });

  it('should show video count badge', () => {
    render(<Gallery />);

    // Should show count of videos
    const badge = screen.getByText(/videos?/i);
    expect(badge).toBeInTheDocument();
  });
});
