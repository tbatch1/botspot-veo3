'use client';

import React from 'react';
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent,
} from '@dnd-kit/core';
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  horizontalListSortingStrategy,
} from '@dnd-kit/sortable';
import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import type { Scene } from '../../types/sequence';

interface TimelineProps {
  scenes: Scene[];
  onReorder: (sceneOrders: Array<{ sceneNumber: number; newPosition: number }>) => void;
  onSceneClick: (sceneNumber: number) => void;
  selectedSceneNumber?: number;
  className?: string;
}

interface SortableSceneItemProps {
  scene: Scene;
  isSelected: boolean;
  onClick: () => void;
}

function SortableSceneItem({ scene, isSelected, onClick }: SortableSceneItemProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: scene.sceneNumber });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  const getStatusColor = (status: Scene['status']) => {
    switch (status) {
      case 'completed':
        return 'bg-green-500';
      case 'generating':
        return 'bg-blue-500 animate-pulse';
      case 'failed':
        return 'bg-red-500';
      case 'pending':
      default:
        return 'bg-gray-400';
    }
  };

  const getStatusText = (status: Scene['status']) => {
    switch (status) {
      case 'completed':
        return 'Done';
      case 'generating':
        return 'Generating...';
      case 'failed':
        return 'Failed';
      case 'pending':
      default:
        return 'Pending';
    }
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...attributes}
      {...listeners}
      onClick={onClick}
      className={`
        relative flex flex-col items-center justify-center
        w-32 h-24 rounded-lg border-2 cursor-pointer
        transition-all duration-200 hover:scale-105
        ${isSelected ? 'border-blue-500 ring-2 ring-blue-300' : 'border-gray-300'}
        ${isDragging ? 'z-50' : 'z-0'}
        bg-white shadow-sm hover:shadow-md
      `}
    >
      {/* Scene Number Badge */}
      <div className="absolute top-1 left-1 bg-gray-800 text-white text-xs font-bold px-2 py-1 rounded">
        {scene.sceneNumber}
      </div>

      {/* Status Indicator */}
      <div className={`absolute top-1 right-1 w-3 h-3 rounded-full ${getStatusColor(scene.status)}`} />

      {/* Thumbnail or Placeholder */}
      <div className="flex-1 w-full flex items-center justify-center p-2">
        {scene.result?.thumbnailUrl ? (
          <img
            src={scene.result.thumbnailUrl}
            alt={`Scene ${scene.sceneNumber}`}
            className="w-full h-full object-cover rounded"
          />
        ) : (
          <div className="text-gray-400 text-center text-xs">
            {scene.status === 'generating' ? '⏳' : '🎬'}
          </div>
        )}
      </div>

      {/* Duration & Status */}
      <div className="w-full px-2 py-1 bg-gray-50 rounded-b-lg">
        <div className="text-xs text-gray-600 text-center truncate">
          {scene.config.duration}s
        </div>
        <div className="text-xs text-gray-500 text-center truncate">
          {getStatusText(scene.status)}
        </div>
      </div>

      {/* Continuity Indicator */}
      {scene.continuity.usesLastFrame && scene.sceneNumber > 1 && (
        <div className="absolute -left-2 top-1/2 -translate-y-1/2 text-blue-500">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
            <path d="M8 0L6 2h4L8 0zM8 16l2-2H6l2 2zM0 8l2-2v4L0 8zm16 0l-2 2V6l2 2z" />
          </svg>
        </div>
      )}
    </div>
  );
}

export function Timeline({
  scenes,
  onReorder,
  onSceneClick,
  selectedSceneNumber,
  className = '',
}: TimelineProps) {
  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;

    if (over && active.id !== over.id) {
      const oldIndex = scenes.findIndex((s) => s.sceneNumber === active.id);
      const newIndex = scenes.findIndex((s) => s.sceneNumber === over.id);

      if (oldIndex !== -1 && newIndex !== -1) {
        const reorderedScenes = arrayMove(scenes, oldIndex, newIndex);

        // Create reorder instructions
        const sceneOrders = reorderedScenes.map((scene, index) => ({
          sceneNumber: scene.sceneNumber,
          newPosition: index + 1,
        }));

        onReorder(sceneOrders);
      }
    }
  };

  if (scenes.length === 0) {
    return (
      <div className={`flex items-center justify-center h-32 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300 ${className}`}>
        <p className="text-gray-500 text-sm">No scenes yet. Add a scene to get started!</p>
      </div>
    );
  }

  return (
    <div className={`${className}`}>
      <div className="mb-2 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-700">Timeline</h3>
        <p className="text-xs text-gray-500">
          {scenes.length} scene{scenes.length !== 1 ? 's' : ''} ·
          {scenes.reduce((sum, s) => sum + s.config.duration, 0)}s total
        </p>
      </div>

      <DndContext
        sensors={sensors}
        collisionDetection={closestCenter}
        onDragEnd={handleDragEnd}
      >
        <SortableContext
          items={scenes.map((s) => s.sceneNumber)}
          strategy={horizontalListSortingStrategy}
        >
          <div className="flex gap-3 overflow-x-auto pb-2">
            {scenes.map((scene) => (
              <SortableSceneItem
                key={scene.sceneNumber}
                scene={scene}
                isSelected={scene.sceneNumber === selectedSceneNumber}
                onClick={() => onSceneClick(scene.sceneNumber)}
              />
            ))}
          </div>
        </SortableContext>
      </DndContext>

      {/* Legend */}
      <div className="mt-3 flex items-center gap-4 text-xs text-gray-500">
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded-full bg-gray-400" />
          <span>Pending</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded-full bg-blue-500" />
          <span>Generating</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded-full bg-green-500" />
          <span>Completed</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded-full bg-red-500" />
          <span>Failed</span>
        </div>
      </div>
    </div>
  );
}
