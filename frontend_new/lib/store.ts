import { create } from 'zustand';
import { ProjectState, api } from './api';

type WorkflowStep = 'input' | 'strategy' | 'images' | 'videos' | 'complete';

interface AppState {
    project: ProjectState | null;
    isLoading: boolean;
    error: string | null;
    pollingInterval: NodeJS.Timeout | null;
    pollRetryCount: number;
    currentStep: WorkflowStep;

    createPlan: (input: string, config?: any) => Promise<ProjectState | void>;
    startGeneration: () => Promise<void>;

    // Approval workflow actions
    approveStrategy: () => Promise<void>;
    approveImages: () => Promise<void>;
    approveVideos: () => Promise<void>;

    pollStatus: () => void;
    stopPolling: () => void;
    reset: () => void;
    updateScript: (script: any) => void; // In a real app, use proper type
}

const MAX_POLL_RETRIES = 20; // 20 retries * 3s = 60 seconds max

export const useStore = create<AppState>((set, get) => ({
    project: null,
    isLoading: false,
    error: null,
    pollingInterval: null,
    pollRetryCount: 0,
    currentStep: 'input',

    createPlan: async (input: string, config?: any) => {
        set({ isLoading: true, error: null, currentStep: 'input' });
        try {
            const project = await api.createPlan(input, config);
            set({ project, isLoading: false, currentStep: 'strategy' });
            return project;
        } catch (err: any) {
            const errorMsg = err.response?.data?.detail || err.message || 'Failed to create plan';
            set({ error: errorMsg, isLoading: false });
        }
    },

    startGeneration: async () => {
        const { project } = get();
        if (!project || !project.script) return;

        set({ isLoading: true, error: null, pollRetryCount: 0 });
        try {
            await api.startGeneration(project.id, project.script);
            // Start polling
            get().pollStatus();
        } catch (err: any) {
            const errorMsg = err.response?.data?.detail || err.message || 'Failed to start generation';
            set({ error: errorMsg, isLoading: false });
        }
    },

    // ========================================================================================
    // APPROVAL WORKFLOW: Stage-Based Actions
    // ========================================================================================

    approveStrategy: async () => {
        const { project } = get();
        if (!project || !project.script) return;

        set({ isLoading: true, error: null, pollRetryCount: 0, currentStep: 'images' });
        try {
            await api.generateImages(project.id, project.script);
            // Start polling for image generation progress
            get().pollStatus();
        } catch (err: any) {
            const errorMsg = err.response?.data?.detail || err.message || 'Failed to start image generation';
            set({ error: errorMsg, isLoading: false });
        }
    },

    approveImages: async () => {
        const { project } = get();
        if (!project || !project.script) return;

        set({ isLoading: true, error: null, pollRetryCount: 0, currentStep: 'videos' });
        try {
            await api.generateVideos(project.id, project.script);
            // Start polling for video generation progress
            get().pollStatus();
        } catch (err: any) {
            const errorMsg = err.response?.data?.detail || err.message || 'Failed to start video generation';
            set({ error: errorMsg, isLoading: false });
        }
    },

    approveVideos: async () => {
        const { project } = get();
        if (!project || !project.script) return;

        set({ isLoading: true, error: null, pollRetryCount: 0 });
        try {
            await api.assembleFinal(project.id, project.script);
            // Start polling for final assembly progress
            get().pollStatus();
        } catch (err: any) {
            const errorMsg = err.response?.data?.detail || err.message || 'Failed to start final assembly';
            set({ error: errorMsg, isLoading: false });
        }
    },

    pollStatus: () => {
        // Clear any existing interval first
        const { pollingInterval } = get();
        if (pollingInterval) {
            clearInterval(pollingInterval);
        }

        const interval = setInterval(async () => {
            const { project, pollRetryCount } = get();
            if (!project) {
                get().stopPolling();
                return;
            }

            try {
                const updated = await api.getStatus(project.id);

                // Update currentStep based on status
                let newStep: WorkflowStep = get().currentStep;
                if (updated.status === 'images_complete') {
                    newStep = 'images';
                    set({ isLoading: false }); // Stop loading to show approval UI
                } else if (updated.status === 'videos_complete') {
                    newStep = 'videos';
                    set({ isLoading: false }); // Stop loading to show approval UI
                } else if (updated.status === 'completed') {
                    newStep = 'complete';
                }

                set({ project: updated, pollRetryCount: 0, currentStep: newStep }); // Reset retry count on success

                if (updated.status === 'completed') {
                    get().stopPolling();
                    set({ isLoading: false, error: null });
                } else if (updated.status === 'failed') {
                    get().stopPolling();
                    const errorMsg = (updated as any).error || 'Generation failed';
                    set({ isLoading: false, error: errorMsg });
                }
            } catch (err: any) {
                console.error('Polling error', err);

                const newRetryCount = pollRetryCount + 1;

                if (newRetryCount >= MAX_POLL_RETRIES) {
                    // Max retries reached - stop polling and show error
                    get().stopPolling();
                    const errorMsg = err.response?.status === 404
                        ? 'Project not found'
                        : 'Failed to check status - server may be down';
                    set({
                        isLoading: false,
                        error: errorMsg,
                        pollRetryCount: 0
                    });
                } else {
                    // Increment retry count
                    set({ pollRetryCount: newRetryCount });
                }
            }
        }, 3000); // Poll every 3 seconds

        set({ pollingInterval: interval });
    },

    stopPolling: () => {
        const { pollingInterval } = get();
        if (pollingInterval) {
            clearInterval(pollingInterval);
            set({ pollingInterval: null, pollRetryCount: 0 });
        }
    },

    reset: () => {
        get().stopPolling();
        set({
            project: null,
            isLoading: false,
            error: null,
            pollRetryCount: 0
        });
    },

    updateScript: (script) => {
        set((state) => ({
            project: state.project ? { ...state.project, script } : null
        }))
    }
}));
