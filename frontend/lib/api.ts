import axios from 'axios';

const API_URL = 'http://localhost:8000/api';

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

export interface ProjectState {
    id: string;
    user_input: string;
    status: string;
    script?: Script;
    final_video_path?: string;
}

export const api = {
    createPlan: async (userInput: string): Promise<ProjectState> => {
        const response = await axios.post(`${API_URL}/plan`, { user_input: userInput });
        return response.data;
    },

    startGeneration: async (projectId: string, script: Script): Promise<void> => {
        await axios.post(`${API_URL}/generate`, { project_id: projectId, script });
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
    }
};
