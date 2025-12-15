import { create } from 'zustand';
import { ProjectState, api } from './api';

interface AppState {
    project: ProjectState | null;
    isLoading: boolean;
    error: string | null;

    createPlan: (input: string) => Promise<void>;
    startGeneration: () => Promise<void>;
    pollStatus: () => void;
    updateScript: (script: any) => void; // In a real app, use proper type
}

export const useStore = create<AppState>((set, get) => ({
    project: null,
    isLoading: false,
    error: null,

    createPlan: async (input: string) => {
        set({ isLoading: true, error: null });
        try {
            const project = await api.createPlan(input);
            set({ project, isLoading: false });
        } catch (err) {
            set({ error: 'Failed to create plan', isLoading: false });
        }
    },

    startGeneration: async () => {
        const { project } = get();
        if (!project || !project.script) return;

        set({ isLoading: true });
        try {
            await api.startGeneration(project.id, project.script);
            // Start polling
            get().pollStatus();
        } catch (err) {
            set({ error: 'Failed to start generation', isLoading: false });
        }
    },

    pollStatus: () => {
        const interval = setInterval(async () => {
            const { project } = get();
            if (!project) return clearInterval(interval);

            try {
                const updated = await api.getStatus(project.id);
                set({ project: updated });

                if (updated.status === 'completed' || updated.status === 'failed') {
                    clearInterval(interval);
                    set({ isLoading: false });
                }
            } catch (err) {
                console.error('Polling error', err);
            }
        }, 3000);
    },

    updateScript: (script) => {
        set((state) => ({
            project: state.project ? { ...state.project, script } : null
        }))
    }
}));
