import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

// Tailwind class merger utility
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// Format currency
export function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount);
}

// Format duration in seconds to readable format
export function formatDuration(seconds: number): string {
  if (seconds < 60) return `${seconds}s`;
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  return remainingSeconds > 0 ? `${minutes}m ${remainingSeconds}s` : `${minutes}m`;
}

// Format file size
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
}

// Debounce function
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout;
  return (...args: Parameters<T>) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
}

// Generate random ID
export function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

// Sleep utility for async delays
export function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

// Validate video prompt
export function validatePrompt(prompt: string): { valid: boolean; error?: string } {
  if (!prompt || prompt.trim().length === 0) {
    return { valid: false, error: 'Prompt is required' };
  }
  if (prompt.length < 10) {
    return { valid: false, error: 'Prompt must be at least 10 characters' };
  }
  if (prompt.length > 1000) {
    return { valid: false, error: 'Prompt must be less than 1000 characters' };
  }
  return { valid: true };
}

// Calculate video cost
export function calculateCost(duration: number, model: string): number {
  const pricePerSecond = model === 'veo-3.0-fast-generate-001' ? 0.15 : 0.40;
  return duration * pricePerSecond;
}
