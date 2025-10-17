// prompt-optimizer.js - Smart Prompt Optimizer for Trading Bot Videos
// Automatically enhances user prompts with trading-specific terminology and visual quality improvements

/**
 * Prompt Optimizer Service
 * Transforms basic prompts into high-quality, trading-specific video generation prompts
 */
class PromptOptimizer {
  constructor() {
    // Trading-specific vocabulary to inject
    this.tradingTerms = {
      charts: ['candlestick charts', 'real-time price action', 'technical indicators', 'volume bars'],
      indicators: ['RSI', 'MACD', 'Bollinger Bands', 'moving averages', 'Fibonacci retracements'],
      actions: ['executing trades', 'placing orders', 'managing positions', 'adjusting stop-losses'],
      visual: ['green profit indicators', 'red loss warnings', 'percentage gains', 'trade statistics'],
      ui: ['professional trading dashboard', 'multi-monitor setup', 'dark theme interface', 'real-time data feeds']
    };

    // Quality enhancement terms
    this.qualityEnhancements = {
      lighting: 'studio lighting, high contrast, professional color grading',
      camera: 'cinematic camera angle, smooth zoom transitions, focus on key elements',
      clarity: 'sharp details, 4K quality, crystal clear text and numbers',
      atmosphere: 'professional trading floor atmosphere, focused concentration'
    };

    // Compliance-safe replacements (avoid regulatory issues)
    this.complianceReplacements = {
      'guaranteed profit': 'potential profit opportunity',
      'guaranteed returns': 'historical performance indicators',
      'risk-free': 'risk-managed',
      'always wins': 'optimized win rate',
      'never loses': 'loss mitigation strategies',
      'get rich': 'build wealth',
      'easy money': 'automated trading efficiency'
    };

    // Negative prompts to add (what to avoid)
    this.negativePrompts = [
      'no cartoon style',
      'no low quality',
      'no blurry images',
      'no amateur graphics',
      'no unrealistic scenarios',
      'no text overlays blocking key information'
    ];
  }

  /**
   * Main optimization function
   * @param {string} userPrompt - Original user prompt
   * @param {Object} options - Configuration options
   * @returns {Object} - Optimized prompt and metadata
   */
  optimize(userPrompt, options = {}) {
    const {
      enhanceVisuals = true,
      addTradingContext = true,
      ensureCompliance = true,
      addNegativePrompts = true,
      targetLength = 'optimal' // 'short', 'optimal', 'detailed'
    } = options;

    let optimizedPrompt = userPrompt.trim();

    // Step 1: Ensure compliance (replace risky terms)
    if (ensureCompliance) {
      optimizedPrompt = this.ensureCompliance(optimizedPrompt);
    }

    // Step 2: Add trading context
    if (addTradingContext) {
      optimizedPrompt = this.addTradingContext(optimizedPrompt);
    }

    // Step 3: Enhance visual quality
    if (enhanceVisuals) {
      optimizedPrompt = this.enhanceVisuals(optimizedPrompt);
    }

    // Step 4: Add negative prompts
    const negativePrompt = addNegativePrompts ? this.negativePrompts.join(', ') : '';

    // Step 5: Optimize length
    optimizedPrompt = this.optimizeLength(optimizedPrompt, targetLength);

    return {
      original: userPrompt,
      optimized: optimizedPrompt,
      negativePrompt,
      metadata: {
        originalLength: userPrompt.length,
        optimizedLength: optimizedPrompt.length,
        complianceIssuesFixed: this.countComplianceIssues(userPrompt),
        enhancementsAdded: this.countEnhancements(userPrompt, optimizedPrompt)
      }
    };
  }

  /**
   * Ensure prompt is compliance-safe
   */
  ensureCompliance(prompt) {
    let compliantPrompt = prompt;

    for (const [risky, safe] of Object.entries(this.complianceReplacements)) {
      const regex = new RegExp(risky, 'gi');
      compliantPrompt = compliantPrompt.replace(regex, safe);
    }

    return compliantPrompt;
  }

  /**
   * Add trading-specific context
   */
  addTradingContext(prompt) {
    let enhanced = prompt;

    // Check if prompt mentions charts, if not add them
    if (!prompt.toLowerCase().includes('chart') && !prompt.toLowerCase().includes('graph')) {
      enhanced += ', with real-time candlestick charts displaying price action';
    }

    // Check if prompt mentions indicators
    if (!prompt.toLowerCase().includes('indicator') && !prompt.toLowerCase().includes('rsi') && !prompt.toLowerCase().includes('macd')) {
      enhanced += ', showing technical indicators like RSI and MACD';
    }

    // Check if prompt mentions trading dashboard
    if (!prompt.toLowerCase().includes('dashboard') && !prompt.toLowerCase().includes('interface')) {
      enhanced += ', on a professional trading dashboard interface';
    }

    // Add profit/loss visualization if not present
    if (!prompt.toLowerCase().includes('profit') && !prompt.toLowerCase().includes('gain') && !prompt.toLowerCase().includes('loss')) {
      enhanced += ', with green profit indicators and percentage gains displayed';
    }

    return enhanced;
  }

  /**
   * Enhance visual quality
   */
  enhanceVisuals(prompt) {
    let enhanced = prompt;

    // Add lighting if not mentioned
    if (!prompt.toLowerCase().includes('light')) {
      enhanced += `. ${this.qualityEnhancements.lighting}`;
    }

    // Add camera quality if not mentioned
    if (!prompt.toLowerCase().includes('camera') && !prompt.toLowerCase().includes('cinematic')) {
      enhanced += `. ${this.qualityEnhancements.camera}`;
    }

    // Add clarity enhancements
    if (!prompt.toLowerCase().includes('sharp') && !prompt.toLowerCase().includes('clear') && !prompt.toLowerCase().includes('4k')) {
      enhanced += `. ${this.qualityEnhancements.clarity}`;
    }

    return enhanced;
  }

  /**
   * Optimize prompt length
   */
  optimizeLength(prompt, targetLength) {
    const maxLengths = {
      short: 500,
      optimal: 1000,
      detailed: 1500
    };

    const maxLength = maxLengths[targetLength] || maxLengths.optimal;

    if (prompt.length > maxLength) {
      // Truncate intelligently at sentence boundary
      const truncated = prompt.substring(0, maxLength);
      const lastPeriod = truncated.lastIndexOf('.');
      return lastPeriod > 0 ? truncated.substring(0, lastPeriod + 1) : truncated;
    }

    return prompt;
  }

  /**
   * Count compliance issues
   */
  countComplianceIssues(prompt) {
    let count = 0;
    for (const risky of Object.keys(this.complianceReplacements)) {
      if (prompt.toLowerCase().includes(risky.toLowerCase())) {
        count++;
      }
    }
    return count;
  }

  /**
   * Count enhancements added
   */
  countEnhancements(original, optimized) {
    return Math.floor((optimized.length - original.length) / 50);
  }

  /**
   * Generate multiple prompt variations for A/B testing
   */
  generateVariations(userPrompt, count = 3) {
    const variations = [];

    // Variation 1: Minimal enhancement
    variations.push(this.optimize(userPrompt, {
      enhanceVisuals: false,
      addTradingContext: true,
      ensureCompliance: true,
      targetLength: 'short'
    }));

    // Variation 2: Optimal enhancement (default)
    variations.push(this.optimize(userPrompt, {
      enhanceVisuals: true,
      addTradingContext: true,
      ensureCompliance: true,
      targetLength: 'optimal'
    }));

    // Variation 3: Maximum detail
    if (count >= 3) {
      variations.push(this.optimize(userPrompt, {
        enhanceVisuals: true,
        addTradingContext: true,
        ensureCompliance: true,
        addNegativePrompts: true,
        targetLength: 'detailed'
      }));
    }

    return variations;
  }

  /**
   * Analyze prompt quality
   */
  analyzePrompt(prompt) {
    return {
      length: prompt.length,
      hasCharts: prompt.toLowerCase().includes('chart') || prompt.toLowerCase().includes('graph'),
      hasIndicators: prompt.toLowerCase().includes('indicator') || prompt.toLowerCase().includes('rsi') || prompt.toLowerCase().includes('macd'),
      hasProfitLoss: prompt.toLowerCase().includes('profit') || prompt.toLowerCase().includes('loss') || prompt.toLowerCase().includes('gain'),
      hasVisualQuality: prompt.toLowerCase().includes('cinematic') || prompt.toLowerCase().includes('professional') || prompt.toLowerCase().includes('4k'),
      complianceIssues: this.countComplianceIssues(prompt),
      qualityScore: this.calculateQualityScore(prompt)
    };
  }

  /**
   * Calculate quality score (0-100)
   */
  calculateQualityScore(prompt) {
    let score = 50; // Base score

    // Add points for good practices
    if (prompt.toLowerCase().includes('chart')) score += 10;
    if (prompt.toLowerCase().includes('indicator')) score += 10;
    if (prompt.toLowerCase().includes('professional')) score += 5;
    if (prompt.toLowerCase().includes('cinematic')) score += 5;
    if (prompt.toLowerCase().includes('real-time')) score += 5;
    if (prompt.length > 100 && prompt.length < 800) score += 10;

    // Subtract points for issues
    score -= this.countComplianceIssues(prompt) * 10;
    if (prompt.length < 50) score -= 20;
    if (prompt.length > 1500) score -= 10;

    return Math.max(0, Math.min(100, score));
  }
}

// Export
module.exports = PromptOptimizer;
