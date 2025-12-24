import axios from 'axios';

const API_URL = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4000/api').replace(/\/+$/, '');

export interface Scene {
    id: number;
    visual_prompt: string;
    motion_prompt: string;
    audio_prompt: string;
    duration: number;
    image_path?: string;
    video_path?: string;
    sfx_path?: string;
    image_source?: string; // "ai" or "upload:{filename}"
}

export interface ScriptLine {
    speaker: string;
    text: string;
    time_range: string;
    voice_id?: string;
    scene_id?: number;
    audio_path?: string;
}

export interface Script {
    lines: ScriptLine[];
    mood: string;
    scenes: Scene[];
}

export interface BrandCard {
    brand_name?: string;
    what_it_is?: string;
    category?: string;
    target_audience?: string;
    core_promise?: string;
    key_benefits?: string[];
    key_features?: string[];
    differentiators?: string[];
    proof_points?: string[];
    constraints?: string[];
    compliance_notes?: string[];
    creative_angle?: string;
    visual_motifs?: string[];
    call_to_action?: string;
}

export interface AppliedPreferences {
    style?: string | string[];
    mood?: string | string[];
    platform?: string | string[];
    commercial_style?: string;
    camera_style?: string | string[];
    lighting_preference?: string;
    color_grade?: string;
    url?: string;
    [key: string]: unknown;
}

export interface Strategy {
    core_concept?: string;
    visual_language?: string;
    narrative_arc?: string;
    audience_hook?: string;
    cinematic_direction?: any;
    product_name?: string;
    brand_card?: BrandCard;
    brand_summary?: string;
    applied_preferences?: AppliedPreferences;
}

export interface ProjectState {
    id: string;
    user_input: string;
    status: string;
    script?: Script;
    strategy?: Strategy;
    final_video_path?: string;
    player_mode?: string;
    logs: string[];
    error?: string;
}

export interface ElevenLabsVoice {
    voice_id: string;
    name: string;
    category?: string;
    description?: string;
    labels?: Record<string, string>;
    preview_url?: string;
}

export interface ElevenLabsLibraryVoice {
    public_owner_id: string;
    voice_id: string;
    name: string;
    accent?: string;
    gender?: string;
    age?: string;
    descriptive?: string;
    use_case?: string;
    category?: string;
    language?: string;
    locale?: string;
    description?: string;
    preview_url?: string;
    free_users_allowed?: boolean;
    featured?: boolean;
    is_added_by_user?: boolean;
}

export interface UnifiedVoice {
    provider: string;
    voice_id: string;
    name: string;
    category?: string;
    description?: string;
    labels?: Record<string, string>;
    preview_url?: string | null;
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
    },

    // Update a scene's image source (AI or uploaded file)
    updateSceneSource: async (projectId: string, sceneId: number, imageSource: string): Promise<void> => {
        await axios.post(`${API_URL}/scene/source`, {
            project_id: projectId,
            scene_id: sceneId,
            image_source: imageSource
        });
    },

    // List uploaded files for a project
    listUploads: async (projectId: string): Promise<{filename: string, mode: string}[]> => {
        const response = await axios.get(`${API_URL}/uploads/${projectId}`);
        return response.data?.uploads || [];
    },

    listElevenlabsVoices: async (): Promise<ElevenLabsVoice[]> => {
        const response = await axios.get(`${API_URL}/elevenlabs/voices`);
        const voices = response.data?.voices;
        return Array.isArray(voices) ? voices : [];
    },

    listVoices: async (params?: {
        provider?: string;
        q?: string;
        locale?: string;
        gender?: string;
        limit?: number;
    }): Promise<UnifiedVoice[]> => {
        const response = await axios.get(`${API_URL}/voices`, { params });
        const voices = response.data?.voices;
        return Array.isArray(voices) ? voices : [];
    },

    searchElevenlabsVoiceLibrary: async (params?: {
        search?: string;
        category?: string;
        gender?: string;
        age?: string;
        accent?: string;
        language?: string;
        locale?: string;
        use_case?: string;
        featured?: boolean;
        page?: number;
        page_size?: number;
    }): Promise<{ voices: ElevenLabsLibraryVoice[]; has_more: boolean; page: number; page_size: number }> => {
        const response = await axios.get(`${API_URL}/elevenlabs/voice_library`, { params });
        return {
            voices: Array.isArray(response.data?.voices) ? response.data.voices : [],
            has_more: !!response.data?.has_more,
            page: Number(response.data?.page || 1),
            page_size: Number(response.data?.page_size || 30),
        };
    },

    addElevenlabsVoiceFromLibrary: async (input: {
        public_owner_id: string;
        voice_id: string;
        new_name: string;
    }): Promise<{ voice_id: string }> => {
        const response = await axios.post(`${API_URL}/elevenlabs/voice_library/add`, input);
        return { voice_id: response.data?.voice_id || input.voice_id };
    },

    elevenlabsTtsPreview: async (input: {
        voice_id: string;
        text: string;
        model_id?: string;
    }): Promise<{ audio_path: string }> => {
        const response = await axios.post(`${API_URL}/elevenlabs/tts_preview`, input);
        return { audio_path: response.data?.audio_path };
    },

    ttsPreview: async (input: { voice_id: string; text: string }): Promise<{ audio_path: string }> => {
        const response = await axios.post(`${API_URL}/tts_preview`, input);
        return { audio_path: response.data?.audio_path };
    },

    remixVoiceover: async (
        projectId: string,
        script: Script,
        options?: {
            regenerate_all?: boolean;
            include_sfx?: boolean;
            include_bgm?: boolean;
            bgm_prompt?: string;
            speaker_voice_map?: Record<string, string>;
        }
    ): Promise<void> => {
        await axios.post(`${API_URL}/remix/voiceover`, {
            project_id: projectId,
            script,
            regenerate_all: options?.regenerate_all ?? false,
            include_sfx: options?.include_sfx ?? false,
            include_bgm: options?.include_bgm ?? false,
            bgm_prompt: options?.bgm_prompt ?? null,
            speaker_voice_map: options?.speaker_voice_map ?? null,
        });
    },
};
