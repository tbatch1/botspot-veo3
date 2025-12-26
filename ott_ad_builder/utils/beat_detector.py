"""
Beat Detector - Extract beat grid from music for sync
Uses librosa for beat detection, with fallback to estimated grid.
"""
import os


def extract_beat_grid(audio_path: str, duration: float = None, fallback_bpm: int = 120) -> dict:
    """
    Extract beat information from audio file.
    
    Args:
        audio_path: Path to audio file (mp3, wav, etc.)
        duration: Total duration in seconds (for fallback grid)
        fallback_bpm: BPM to use if detection fails
    
    Returns:
        dict with:
            - bpm: Detected or fallback BPM
            - beats: List of beat timestamps in seconds
            - drop_time: Estimated "drop" point (peak energy)
    """
    if not audio_path or not os.path.exists(audio_path):
        return _fallback_grid(duration or 15, fallback_bpm)
    
    try:
        import librosa
        
        # Load audio
        y, sr = librosa.load(audio_path, sr=22050)
        
        # Detect tempo and beats
        tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
        beat_times = librosa.frames_to_time(beat_frames, sr=sr).tolist()
        
        # Handle tempo as array (librosa 0.10+)
        if hasattr(tempo, '__iter__'):
            tempo = float(tempo[0]) if len(tempo) > 0 else fallback_bpm
        else:
            tempo = float(tempo)
        
        # Find energy peak (likely "drop" point)
        drop_time = _find_energy_peak(y, sr, beat_times)
        
        print(f"[BEAT DETECTOR] Detected BPM: {tempo:.1f}, Beats: {len(beat_times)}, Drop: {drop_time:.1f}s")
        
        return {
            "bpm": tempo,
            "beats": beat_times,
            "drop_time": drop_time
        }
        
    except ImportError:
        print("[BEAT DETECTOR] librosa not installed, using fallback grid")
        return _fallback_grid(duration or 15, fallback_bpm)
    except Exception as e:
        print(f"[BEAT DETECTOR] Error: {e}, using fallback grid")
        return _fallback_grid(duration or 15, fallback_bpm)


def _find_energy_peak(y, sr, beat_times: list) -> float:
    """Find the timestamp of maximum energy (likely the 'drop')."""
    try:
        import librosa
        import numpy as np
        
        # RMS energy
        rms = librosa.feature.rms(y=y)[0]
        times = librosa.times_like(rms, sr=sr)
        
        # Find peak energy time
        peak_idx = np.argmax(rms)
        peak_time = times[peak_idx]
        
        # Snap to nearest beat
        if beat_times:
            peak_time = min(beat_times, key=lambda b: abs(b - peak_time))
        
        return float(peak_time)
    except Exception:
        # Default to 60% through the track (common drop point)
        if beat_times and len(beat_times) > 2:
            idx = int(len(beat_times) * 0.6)
            return beat_times[idx]
        return 8.0  # Default 8 seconds


def _fallback_grid(duration: float, bpm: int) -> dict:
    """Generate a simple beat grid without audio analysis."""
    beat_interval = 60.0 / bpm  # Seconds per beat
    beats = []
    t = 0.0
    while t < duration:
        beats.append(t)
        t += beat_interval
    
    # Drop at 60% of duration
    drop_time = duration * 0.6
    
    print(f"[BEAT DETECTOR] Fallback grid: {bpm} BPM, {len(beats)} beats")
    
    return {
        "bpm": bpm,
        "beats": beats,
        "drop_time": drop_time
    }


def snap_to_beat(timestamp: float, beat_grid: dict, tolerance: float = 0.3) -> float:
    """
    Snap a timestamp to the nearest beat.
    
    Args:
        timestamp: Time in seconds
        beat_grid: Output from extract_beat_grid()
        tolerance: Max distance to snap (seconds)
    
    Returns:
        Snapped timestamp (or original if no beat close enough)
    """
    beats = beat_grid.get("beats", [])
    if not beats:
        return timestamp
    
    nearest = min(beats, key=lambda b: abs(b - timestamp))
    if abs(nearest - timestamp) <= tolerance:
        return nearest
    return timestamp


def get_cut_points(beat_grid: dict, scene_durations: list[float]) -> list[float]:
    """
    Calculate optimal cut points that land on beats.
    
    Args:
        beat_grid: Output from extract_beat_grid()
        scene_durations: Desired duration for each scene
    
    Returns:
        List of cut timestamps snapped to beats
    """
    beats = beat_grid.get("beats", [])
    if not beats:
        # No beats, use cumulative durations
        cuts = []
        t = 0.0
        for d in scene_durations:
            t += d
            cuts.append(t)
        return cuts
    
    cuts = []
    current_time = 0.0
    
    for duration in scene_durations:
        target_cut = current_time + duration
        snapped_cut = snap_to_beat(target_cut, beat_grid)
        cuts.append(snapped_cut)
        current_time = snapped_cut
    
    return cuts
