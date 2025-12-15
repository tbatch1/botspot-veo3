
import librosa
import numpy as np

class BeatDetector:
    """
    Analyzes audio to find optimal cut points based on musical beats.
    """
    
    def get_beat_times(self, audio_path: str) -> list[float]:
        """
        Returns a list of timestamps (in seconds) where strong beats occur.
        """
        try:
            print(f"[BEAT] Analyzing rhythm of {audio_path}...")
            # Load audio (mono)
            y, sr = librosa.load(audio_path)
            
            # Detect tempo and beats
            tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
            
            # Convert frames to time
            beat_times = librosa.frames_to_time(beat_frames, sr=sr)
            
            # Filter beats to avoid "too fast" cuts (e.g., minimum 2 seconds between cuts)
            # This is a simple heuristic: Keep a beat only if it's > 2s from the last accepted beat
            # But we actually want to find beats that are CLOSE to our target scene durations.
            
            print(f"[BEAT] Detected tempo: {tempo:.2f} BPM. Found {len(beat_times)} beats.")
            return beat_times.tolist()
            
        except Exception as e:
            print(f"[WARN] Beat detection failed: {e}")
            return []

    def get_energy_profile(self, audio_path: str, duration: float) -> str:
        """
        Analyzes the audio energy (RMS) to determine the vibe: 'high' or 'low'.
        Returns 'high' if average RMS > threshold, else 'low'.
        """
        try:
            y, sr = librosa.load(audio_path, duration=duration)
            rms = librosa.feature.rms(y=y)[0]
            avg_rms = np.mean(rms)
            print(f"[AUDIO] Average Energy (RMS): {avg_rms:.4f}")
            
            # Threshold is empirical. 0.1 is usually "loud". 0.05 is "moderate".
            if avg_rms > 0.08:
                return "high"
            return "low"
        except Exception:
            return "low"

    def snap_to_beat(self, target_time: float, beat_times: list[float], threshold: float = 1.0) -> float:
        """
        Finds the closest beat to the target_time within a threshold.
        If no beat found, returns target_time (no snap).
        """
        if not beat_times:
            return target_time
            
        # Find closest beat
        closest_beat = min(beat_times, key=lambda x: abs(x - target_time))
        
        if abs(closest_beat - target_time) <= threshold:
            print(f"      [SNAP] Adjusted {target_time:.2f}s -> {closest_beat:.2f}s (Beat Sync)")
            return closest_beat
        
        return target_time
