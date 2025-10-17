'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { Sparkles, Search } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { templates, categories, getTemplatesByCategory, type Template } from '@/data/templates';
import { log } from '@/lib/logger';
import { cn } from '@/lib/utils';

interface PromptPanelProps {
  prompt: string;
  onPromptChange: (prompt: string) => void;
  onTemplateSelect: (template: Template) => void;
}

export function PromptPanel({ prompt, onPromptChange, onTemplateSelect }: PromptPanelProps) {
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');

  const filteredTemplates = getTemplatesByCategory(selectedCategory).filter(template =>
    template.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    template.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  const handleTemplateClick = (template: Template) => {
    log.info('Template selected', { templateId: template.id, templateName: template.name });
    onTemplateSelect(template);
  };

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-purple-600" />
          Prompt Builder
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Prompt textarea */}
        <div>
          <label className="text-sm font-medium text-gray-700 mb-2 block">
            Video Prompt
          </label>
          <Textarea
            value={prompt}
            onChange={(e) => onPromptChange(e.target.value)}
            placeholder="Describe the trading bot demo video you want to create..."
            className="min-h-[120px]"
          />
          <div className="text-xs text-gray-500 mt-1">
            {prompt.length} / 1000 characters
          </div>
        </div>

        {/* Template library */}
        <div>
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-gray-900">Templates</h3>
            <Badge variant="secondary">{filteredTemplates.length}</Badge>
          </div>

          {/* Search */}
          <div className="relative mb-3">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <Input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search templates..."
              className="pl-10"
            />
          </div>

          {/* Categories */}
          <div className="flex flex-wrap gap-2 mb-4">
            {categories.map((category) => (
              <button
                key={category.id}
                onClick={() => setSelectedCategory(category.id)}
                className={cn(
                  'px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-200',
                  selectedCategory === category.id
                    ? 'bg-blue-600 text-white shadow-md'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                )}
              >
                {category.name}
                <span className="ml-1.5 opacity-70">({category.count})</span>
              </button>
            ))}
          </div>

          {/* Template cards */}
          <div className="space-y-2 max-h-[400px] overflow-y-auto pr-2 custom-scrollbar">
            {filteredTemplates.map((template) => (
              <motion.button
                key={template.id}
                onClick={() => handleTemplateClick(template)}
                className="w-full text-left p-3 rounded-lg border-2 border-gray-200 hover:border-blue-500 hover:bg-blue-50 transition-all duration-200 group"
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                <div className="flex items-start justify-between mb-1">
                  <h4 className="font-semibold text-sm text-gray-900 group-hover:text-blue-600">
                    {template.name}
                  </h4>
                  <Badge variant="outline" className="text-xs">
                    {template.duration}s
                  </Badge>
                </div>
                <p className="text-xs text-gray-600 line-clamp-2 mb-2">
                  {template.prompt}
                </p>
                <div className="flex flex-wrap gap-1">
                  {template.tags.slice(0, 3).map((tag) => (
                    <span
                      key={tag}
                      className="px-2 py-0.5 bg-gray-100 text-gray-600 rounded text-xs"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </motion.button>
            ))}
          </div>
        </div>
      </CardContent>

      <style jsx global>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 6px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: #f1f1f1;
          border-radius: 10px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: #cbd5e1;
          border-radius: 10px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: #94a3b8;
        }
      `}</style>
    </Card>
  );
}
