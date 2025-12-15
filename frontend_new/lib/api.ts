import axios from 'axios';

const API_URL = 'http://localhost:4000/api';

export interface Scene {
    id: number;
    visual_prompt: string;
    motion_prompt: string;
    audio_prompt: string;
    duration: number;
    image_path?: string;
    video_path?: string;
    sfx_path?: string;
}

export interface ScriptLine {
    speaker: string;
    text: string;
    time_range: string;
    audio_path?: string;
}

export interface Script {
    lines: ScriptLine[];
    mood: string;
    scenes: Scene[];
}

export interface Strategy {
    core_concept?: string;
    visual_language?: string;
    narrative_arc?: string;
    audience_hook?: string;
    cinematic_direction?: any;
}

export interface ProjectState {
    id: string;
    user_input: string;
    status: string;
    script?: Script;
    strategy?: Strategy;
    final_video_path?: string;
    logs: string[];
    error?: string;
}

export const api = {
    createPlan: async (userInput: string, config?: any): Promise<ProjectState> => {
        const payload = {
            user_input: userInput,
            config_overrides: config
        };
        const response = await axios.post(`${API_URL}/plan`, payload);
        return response.data;
    },

    startGeneration: async (projectId: string, script: Script): Promise<void> => {
        await axios.post(`${API_URL}/generate`, { project_id: projectId, script });
    },

    // ========================================================================================
    // APPROVAL WORKFLOW: Stage-Based Generation Methods
    // ========================================================================================

    generateImages: async (projectId: string, script: Script): Promise<void> => {
        await axios.post(`${API_URL}/generate/images`, { project_id: projectId, script });
    },

    generateVideos: async (projectId: string, script: Script): Promise<void> => {
        await axios.post(`${API_URL}/generate/videos`, { project_id: projectId, script });
    },

    assembleFinal: async (projectId: string, script: Script): Promise<void> => {
        await axios.post(`${API_URL}/generate/assemble`, { project_id: projectId, script });
    },

    getStatus: async (projectId: string): Promise<ProjectState> => {
        const response = await axios.get(`${API_URL}/status/${projectId}`);
        return response.data;
    },

    getAssetUrl: (filename: string) => {
        if (!filename) return '';
        // Extract just the filename if a full path is given
        const name = filename.split(/[/\\]/).pop();
        return `${API_URL}/assets/${name}`;
    },

    // Regenerate a single scene's image with optional new prompt
    regenerateScene: async (projectId: string, sceneId: number, newPrompt?: string): Promise<void> => {
        await axios.post(`${API_URL}/regenerate/scene`, { 
            project_id: projectId, 
            scene_id: sceneId,
            new_prompt: newPrompt
        });
    }
};
