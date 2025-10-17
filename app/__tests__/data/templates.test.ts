import { templates, categories, getTemplatesByCategory, getTemplateById } from '@/data/templates';

describe('Templates', () => {
  it('should have 12 templates', () => {
    expect(templates).toHaveLength(12);
  });

  it('should have all required template fields', () => {
    templates.forEach((template) => {
      expect(template).toHaveProperty('id');
      expect(template).toHaveProperty('name');
      expect(template).toHaveProperty('category');
      expect(template).toHaveProperty('prompt');
      expect(template).toHaveProperty('tags');
      expect(template).toHaveProperty('duration');
      expect(template).toHaveProperty('model');

      expect(template.id).toBeTruthy();
      expect(template.name).toBeTruthy();
      expect(template.prompt.length).toBeGreaterThan(50);
      expect(template.tags.length).toBeGreaterThan(0);
      expect(template.duration).toBeGreaterThanOrEqual(4);
      expect(template.duration).toBeLessThanOrEqual(8);
    });
  });

  it('should have 6 categories', () => {
    expect(categories).toHaveLength(6);
  });

  it('should filter templates by category', () => {
    const bullMarketTemplates = getTemplatesByCategory('bull-market');
    expect(bullMarketTemplates.length).toBeGreaterThan(0);
    bullMarketTemplates.forEach((t) => {
      expect(t.category).toBe('bull-market');
    });
  });

  it('should return all templates for "all" category', () => {
    const allTemplates = getTemplatesByCategory('all');
    expect(allTemplates).toHaveLength(templates.length);
  });

  it('should find template by id', () => {
    const template = getTemplateById('bull-breakout');
    expect(template).toBeDefined();
    expect(template?.name).toBe('Bull Market Breakout');
  });

  it('should return undefined for invalid id', () => {
    const template = getTemplateById('invalid-id');
    expect(template).toBeUndefined();
  });

  it('should have valid category counts', () => {
    categories.forEach((category) => {
      if (category.id === 'all') {
        expect(category.count).toBe(templates.length);
      } else {
        const filtered = templates.filter((t) => t.category === category.id);
        expect(category.count).toBe(filtered.length);
      }
    });
  });
});
