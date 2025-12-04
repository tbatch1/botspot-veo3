import {
  cn,
  formatCurrency,
  formatDuration,
  formatFileSize,
  generateId,
  validatePrompt,
  calculateCost,
} from '@/lib/utils';

describe('utils', () => {
  describe('cn', () => {
    it('should merge class names correctly', () => {
      expect(cn('foo', 'bar')).toBe('foo bar');
    });

    it('should handle conditional classes', () => {
      expect(cn('foo', false && 'bar', 'baz')).toBe('foo baz');
    });

    it('should merge Tailwind classes correctly', () => {
      expect(cn('px-2 py-1', 'px-4')).toBe('py-1 px-4');
    });
  });

  describe('formatCurrency', () => {
    it('should format USD correctly', () => {
      expect(formatCurrency(1.5)).toBe('$1.50');
      expect(formatCurrency(0.4)).toBe('$0.40');
      expect(formatCurrency(10)).toBe('$10.00');
    });
  });

  describe('formatDuration', () => {
    it('should format seconds', () => {
      expect(formatDuration(30)).toBe('30s');
      expect(formatDuration(59)).toBe('59s');
    });

    it('should format minutes', () => {
      expect(formatDuration(60)).toBe('1m');
      expect(formatDuration(120)).toBe('2m');
    });

    it('should format minutes and seconds', () => {
      expect(formatDuration(90)).toBe('1m 30s');
      expect(formatDuration(125)).toBe('2m 5s');
    });
  });

  describe('formatFileSize', () => {
    it('should format bytes', () => {
      expect(formatFileSize(0)).toBe('0 Bytes');
      expect(formatFileSize(500)).toBe('500 Bytes');
    });

    it('should format kilobytes', () => {
      expect(formatFileSize(1024)).toBe('1 KB');
      expect(formatFileSize(2048)).toBe('2 KB');
    });

    it('should format megabytes', () => {
      expect(formatFileSize(1048576)).toBe('1 MB');
    });
  });

  describe('generateId', () => {
    it('should generate unique IDs', () => {
      const id1 = generateId();
      const id2 = generateId();
      expect(id1).not.toBe(id2);
      expect(id1).toMatch(/^\d+-[a-z0-9]+$/);
    });
  });

  describe('validatePrompt', () => {
    it('should reject empty prompts', () => {
      expect(validatePrompt('')).toEqual({
        valid: false,
        error: 'Prompt is required',
      });
    });

    it('should reject short prompts', () => {
      expect(validatePrompt('short')).toEqual({
        valid: false,
        error: 'Prompt must be at least 10 characters',
      });
    });

    it('should reject long prompts', () => {
      const longPrompt = 'a'.repeat(1001);
      expect(validatePrompt(longPrompt)).toEqual({
        valid: false,
        error: 'Prompt must be less than 1000 characters',
      });
    });

    it('should accept valid prompts', () => {
      expect(validatePrompt('A valid trading bot prompt')).toEqual({
        valid: true,
      });
    });
  });

  describe('calculateCost', () => {
    it('should calculate cost for fast model', () => {
      expect(calculateCost(5, 'veo-3.1-fast-generate-preview')).toBe(1.75);
      expect(calculateCost(10, 'veo-3.1-fast-generate-preview')).toBe(3.5);
    });

    it('should calculate cost for standard model', () => {
      expect(calculateCost(5, 'veo-3.1-generate-preview')).toBe(2.5);
      expect(calculateCost(10, 'veo-3.1-generate-preview')).toBe(5.0);
    });
  });
});
