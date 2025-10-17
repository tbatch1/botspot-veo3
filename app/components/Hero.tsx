'use client';

import { motion } from 'framer-motion';
import { TrendingUp, Zap, Shield } from 'lucide-react';
import { log } from '@/lib/logger';
import { apiClient } from '@/lib/api-client';
import { useEffect, useState } from 'react';

export function Hero() {
  const [stats, setStats] = useState({
    videosGenerated: 0,
    botsActive: 0,
    totalRevenue: 0,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    log.info('Hero component mounted, fetching stats');

    const fetchStats = async () => {
      try {
        const data = await apiClient.getStats();
        log.info('Stats loaded from API', data);

        // Animate numbers counting up to real values
        const targetStats = {
          videosGenerated: data.videosGenerated,
          botsActive: data.botsActive,
          totalRevenue: data.totalRevenue,
        };

        const duration = 2000;
        const steps = 50;
        const interval = duration / steps;

        let currentStep = 0;
        const timer = setInterval(() => {
          currentStep++;
          const progress = currentStep / steps;

          setStats({
            videosGenerated: Math.floor(targetStats.videosGenerated * progress),
            botsActive: Math.floor(targetStats.botsActive * progress),
            totalRevenue: Math.floor(targetStats.totalRevenue * progress),
          });

          if (currentStep >= steps) {
            clearInterval(timer);
            setStats(targetStats);
            setLoading(false);
          }
        }, interval);

        return () => clearInterval(timer);
      } catch (error) {
        log.error('Failed to load stats', { error });
        setLoading(false);
        // Keep stats at 0 on error
      }
    };

    fetchStats();
  }, []);

  return (
    <section className="relative overflow-hidden bg-gradient-to-br from-blue-600 via-purple-600 to-blue-800 py-20 px-4">
      {/* TSLA Chart Background - SVG */}
      <div className="absolute inset-0 overflow-hidden opacity-25" style={{ zIndex: 1 }}>
        <svg
          className="w-full h-full"
          viewBox="0 0 1200 400"
          preserveAspectRatio="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          {/* Grid lines */}
          <g stroke="white" strokeWidth="0.5" opacity="0.3">
            {[0, 1, 2, 3, 4].map((i) => (
              <line
                key={`h-${i}`}
                x1="0"
                y1={i * 100}
                x2="1200"
                y2={i * 100}
              />
            ))}
            {[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12].map((i) => (
              <line
                key={`v-${i}`}
                x1={i * 100}
                y1="0"
                x2={i * 100}
                y2="400"
              />
            ))}
          </g>

          {/* TSLA Price Line - Bullish uptrend */}
          <motion.path
            d="M 0,350 L 100,320 L 200,280 L 300,250 L 400,230 L 500,200 L 600,170 L 700,150 L 800,120 L 900,100 L 1000,80 L 1100,60 L 1200,50"
            fill="none"
            stroke="#10b981"
            strokeWidth="3"
            strokeLinecap="round"
            initial={{ pathLength: 0, opacity: 0 }}
            animate={{ pathLength: 1, opacity: 1 }}
            transition={{ duration: 3, ease: "easeInOut" }}
          />

          {/* Area under the line */}
          <motion.path
            d="M 0,350 L 100,320 L 200,280 L 300,250 L 400,230 L 500,200 L 600,170 L 700,150 L 800,120 L 900,100 L 1000,80 L 1100,60 L 1200,50 L 1200,400 L 0,400 Z"
            fill="url(#gradient)"
            initial={{ opacity: 0 }}
            animate={{ opacity: 0.3 }}
            transition={{ duration: 2 }}
          />

          {/* Gradient definition */}
          <defs>
            <linearGradient id="gradient" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#10b981" stopOpacity="0.8" />
              <stop offset="100%" stopColor="#10b981" stopOpacity="0" />
            </linearGradient>
          </defs>

          {/* Candlesticks overlay */}
          {[
            { x: 100, h: 40, color: '#10b981' },
            { x: 200, h: 50, color: '#10b981' },
            { x: 300, h: 30, color: '#ef4444' },
            { x: 400, h: 60, color: '#10b981' },
            { x: 500, h: 45, color: '#10b981' },
            { x: 600, h: 35, color: '#10b981' },
            { x: 700, h: 55, color: '#ef4444' },
            { x: 800, h: 70, color: '#10b981' },
            { x: 900, h: 40, color: '#10b981' },
            { x: 1000, h: 50, color: '#10b981' },
            { x: 1100, h: 45, color: '#10b981' },
          ].map((candle, i) => (
            <motion.rect
              key={i}
              x={candle.x - 8}
              y={350 - candle.h - i * 25}
              width="16"
              height={candle.h}
              fill={candle.color}
              opacity="0.6"
              initial={{ scaleY: 0 }}
              animate={{ scaleY: 1 }}
              transition={{ duration: 0.5, delay: i * 0.1 }}
            />
          ))}

          {/* TSLA Label */}
          <text
            x="20"
            y="30"
            fill="white"
            fontSize="24"
            fontWeight="bold"
            opacity="0.7"
          >
            TSLA
          </text>
          <text
            x="20"
            y="55"
            fill="#10b981"
            fontSize="16"
            opacity="0.7"
          >
            ↑ $384.50 +2.4%
          </text>
        </svg>
      </div>

      {/* Animated background overlay */}
      <div className="absolute inset-0 overflow-hidden" style={{ zIndex: 2 }}>
        <div className="absolute -top-1/2 -left-1/2 w-full h-full bg-blue-500/30 rounded-full blur-3xl animate-pulse" />
        <div className="absolute -bottom-1/2 -right-1/2 w-full h-full bg-purple-500/30 rounded-full blur-3xl animate-pulse delay-1000" />
      </div>

      <div className="relative max-w-7xl mx-auto" style={{ zIndex: 10 }}>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="text-center"
        >
          {/* Logo and brand */}
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="inline-flex items-center gap-3 mb-6"
          >
            <div className="w-14 h-14 bg-white rounded-xl flex items-center justify-center shadow-xl">
              <TrendingUp className="w-8 h-8 text-blue-600" />
            </div>
            <h1 className="text-4xl md:text-5xl font-bold text-white">
              Botspot<span className="text-blue-200">.trade</span>
            </h1>
          </motion.div>

          {/* Headline */}
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="text-3xl md:text-6xl font-extrabold text-white mb-6 leading-tight"
          >
            AI Trading Bot <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-200 to-purple-200">Demo Videos</span>
          </motion.h2>

          {/* Subheadline */}
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="text-xl md:text-2xl text-blue-100 mb-8 max-w-3xl mx-auto"
          >
            Create stunning demo videos for your trading strategies in seconds.
          </motion.p>

          {/* Veo 3 Badge */}
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.5, delay: 0.4 }}
            className="inline-flex items-center gap-2 px-6 py-3 bg-white/20 backdrop-blur-md rounded-full border border-white/30 shadow-lg mb-12"
          >
            <div className="flex items-center gap-2">
              <svg className="w-5 h-5 text-white" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2L2 7v10c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-10-5z" />
              </svg>
              <span className="text-white font-semibold">Powered by</span>
              <span className="text-white font-bold">Google Veo 3</span>
            </div>
          </motion.div>

          {/* Stats */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.4 }}
            className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-4xl mx-auto"
          >
            <StatCard
              icon={<Zap className="w-6 h-6" />}
              value={stats.videosGenerated.toLocaleString()}
              label="Videos Generated"
            />
            <StatCard
              icon={<TrendingUp className="w-6 h-6" />}
              value={stats.botsActive.toLocaleString()}
              label="Active Bots"
            />
            <StatCard
              icon={<Shield className="w-6 h-6" />}
              value={`$${(stats.totalRevenue / 1000).toFixed(1)}K`}
              label="Total Revenue"
            />
          </motion.div>
        </motion.div>
      </div>
    </section>
  );
}

function StatCard({ icon, value, label }: { icon: React.ReactNode; value: string; label: string }) {
  return (
    <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/20 shadow-xl hover:scale-105 transition-transform duration-300">
      <div className="flex items-center justify-center mb-3 text-blue-200">
        {icon}
      </div>
      <div className="text-3xl font-bold text-white mb-1">{value}</div>
      <div className="text-sm text-blue-200">{label}</div>
    </div>
  );
}
