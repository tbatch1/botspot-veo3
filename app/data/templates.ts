// Trading bot demo video templates

export interface Template {
  id: string;
  name: string;
  category: 'bull-market' | 'bear-market' | 'risk-management' | 'algo-trading' | 'market-analysis';
  prompt: string;
  tags: string[];
  duration: number;
  model:
    | 'veo-3.1-generate-preview'
    | 'veo-3.1-fast-generate-preview'
    | 'veo-3.0-generate-001'
    | 'veo-3.0-fast-generate-001';
}

export const templates: Template[] = [
  {
    id: 'bull-breakout',
    name: 'Bull Market Breakout',
    category: 'bull-market',
    prompt: 'Smooth camera push in on trading screen. Automated trading bot executing perfect breakout strategy. Green candlesticks rapidly ascending through resistance levels while bot enters positions with glowing profit indicators. Modern tech office with blue ambient lighting. Cinematic style with electronic trade confirmation sounds.',
    tags: ['breakout', 'bull market', 'momentum'],
    duration: 8,
    model: 'veo-3.1-generate-preview',
  },
  {
    id: 'trend-following',
    name: 'Trend Following Strategy',
    category: 'bull-market',
    prompt: 'Wide angle tracking shot. AI trading bot identifying and riding upward trend. Moving averages crossing bullish, volume bars increasing, bot progressively adding to winning positions as price climbs higher. Professional trading floor ambiance. Upbeat electronic music with subtle keyboard typing.',
    tags: ['trend', 'momentum', 'moving averages'],
    duration: 8,
    model: 'veo-3.1-generate-preview',
  },
  {
    id: 'bear-protection',
    name: 'Bear Market Protection',
    category: 'bear-market',
    prompt: 'Close-up on trading screen with red ambient lighting. Trading bot protecting capital during market downturn. Automatically exiting long positions and entering short trades while red candlesticks dominate chart. Dark moody atmosphere. SFX: alert beeps and protective trade confirmations.',
    tags: ['short selling', 'bear market', 'capital protection'],
    duration: 8,
    model: 'veo-3.1-generate-preview',
  },
  {
    id: 'volatility-trading',
    name: 'Volatility Trading',
    category: 'bear-market',
    prompt: 'Fast-paced POV shot of trading dashboard. Advanced bot capitalizing on high volatility. Rapid price swings in both directions, quick scalp trades executing, profit/loss indicators flashing updates. Energetic tech aesthetic. High-tempo electronic beats with rapid trade execution sounds.',
    tags: ['volatility', 'scalping', 'high-frequency'],
    duration: 8,
    model: 'veo-3.1-generate-preview',
  },
  {
    id: 'stop-loss-mastery',
    name: 'Stop-Loss Management',
    category: 'risk-management',
    prompt: 'Slow dolly shot across trading interface. AI bot setting intelligent trailing stops that move with profitable trades. Stop-loss markers gliding upward protecting gains, automatically cutting losses when trades reverse. Calm professional setting. Subtle confirmation chimes.',
    tags: ['risk management', 'stop-loss', 'trailing stops'],
    duration: 8,
    model: 'veo-3.1-generate-preview',
  },
  {
    id: 'portfolio-rebalancing',
    name: 'Portfolio Rebalancing',
    category: 'risk-management',
    prompt: 'Aerial view of portfolio dashboard. Bot managing diversified crypto portfolio with animated pie charts rebalancing. Reducing overperforming assets, increasing undervalued allocations, maintaining target risk levels. Clean minimalist design. Soft ambient soundscape.',
    tags: ['portfolio', 'diversification', 'rebalancing'],
    duration: 8,
    model: 'veo-3.1-generate-preview',
  },
  {
    id: 'market-making',
    name: 'Market Making Bot',
    category: 'algo-trading',
    prompt: 'Extreme close-up on order book depth chart. Market-making algorithm placing symmetrical bid and ask orders. Order book depth visualizations, spreads tightening, trades executing on both sides. Professional exchange interface. Electronic market sounds and order fills.',
    tags: ['market making', 'liquidity', 'spreads'],
    duration: 8,
    model: 'veo-3.1-generate-preview',
  },
  {
    id: 'arbitrage-execution',
    name: 'Arbitrage Opportunities',
    category: 'algo-trading',
    prompt: 'Split-screen camera pan across multiple exchanges. Bot detecting price differences. Same asset priced differently on platforms, buying low on one exchange, selling high on another. Synchronized cross-exchange layout. Rapid simultaneous trade confirmation sounds.',
    tags: ['arbitrage', 'cross-exchange', 'automated'],
    duration: 8,
    model: 'veo-3.1-generate-preview',
  },
  {
    id: 'technical-analysis',
    name: 'Technical Indicator Analysis',
    category: 'market-analysis',
    prompt: 'Crane shot revealing full technical analysis dashboard. AI bot analyzing RSI, MACD, Bollinger Bands, Fibonacci levels appearing sequentially. Multiple indicators aligning, bot executing high-conviction trades. Rich data visualization aesthetic. Analytical ambient tones with confirmation alerts.',
    tags: ['technical analysis', 'indicators', 'signals'],
    duration: 8,
    model: 'veo-3.1-generate-preview',
  },
  {
    id: 'sentiment-analysis',
    name: 'Sentiment-Driven Trading',
    category: 'market-analysis',
    prompt: 'Dynamic montage of social feeds and news. Bot analyzing Twitter/X sentiment scores, processing headlines, sentiment gauges shifting from bearish to bullish. Adjusting positions based on crowd psychology. Modern media wall display. News ticker sounds and social media notifications.',
    tags: ['sentiment', 'social media', 'news analysis'],
    duration: 8,
    model: 'veo-3.1-generate-preview',
  },
  {
    id: 'whale-tracking',
    name: 'Whale Movement Tracker',
    category: 'market-analysis',
    prompt: 'Deep focus shot of blockchain explorer. Bot tracking large wallet movements and whale activity. Blockchain transactions visualized, massive buy/sell orders appearing, whale accumulation patterns highlighted. Futuristic blockchain interface. Deep bass tones for large transactions.',
    tags: ['whale tracking', 'on-chain', 'smart money'],
    duration: 8,
    model: 'veo-3.1-generate-preview',
  },
  {
    id: 'dca-strategy',
    name: 'Dollar Cost Averaging',
    category: 'risk-management',
    prompt: 'Time-lapse tracking shot of long-term investment chart. Bot executing disciplined DCA strategy with regular buy orders appearing like clockwork. Averaging down during dips, accumulating positions gradually over time. Patient wealth-building visualization. Steady rhythmic confirmation tones.',
    tags: ['DCA', 'long-term', 'accumulation'],
    duration: 8,
    model: 'veo-3.1-generate-preview',
  },
];

export const categories = [
  { id: 'all', name: 'All Templates', count: templates.length },
  { id: 'bull-market', name: 'Bull Market', count: templates.filter(t => t.category === 'bull-market').length },
  { id: 'bear-market', name: 'Bear Market', count: templates.filter(t => t.category === 'bear-market').length },
  { id: 'risk-management', name: 'Risk Management', count: templates.filter(t => t.category === 'risk-management').length },
  { id: 'algo-trading', name: 'Algo Trading', count: templates.filter(t => t.category === 'algo-trading').length },
  { id: 'market-analysis', name: 'Market Analysis', count: templates.filter(t => t.category === 'market-analysis').length },
];

export function getTemplatesByCategory(category: string): Template[] {
  if (category === 'all') return templates;
  return templates.filter(t => t.category === category);
}

export function getTemplateById(id: string): Template | undefined {
  return templates.find(t => t.id === id);
}
