"""
Timing Engine - Adjust scene durations based on audio
Ensures VO fits within scenes and cuts land on beats.
"""
import os
from .beat_detector import snap_to_beat


def probe_audio_duration(audio_path: str) -> float:
    """
    Get the actual duration of an audio file in seconds.
    Uses ffprobe (via ffmpeg-python) or falls back to estimation.
    """
    if not audio_path or not os.path.exists(audio_path):
        return 0.0
    
    try:
        import ffmpeg
        probe = ffmpeg.probe(audio_path)
        fmt = probe.get("format", {})
        duration = float(fmt.get("duration", 0))
        return duration
    except Exception:
        pass
    
    # Fallback: estimate from file size (rough, for MP3)
    try:
        size_bytes = os.path.getsize(audio_path)
        # Assume ~16kbps for compressed speech
        estimated = size_bytes / (16 * 1024 / 8)
        return min(estimated, 30.0)  # Cap at 30s
    except Exception:
        return 0.0


def clamp_to_veo_duration(duration: float) -> int:
    """
    Clamp duration to Veo-compatible values: 4, 6, or 8 seconds.
    """
    if duration <= 5:
        return 4
    elif duration <= 7:
        return 6
    else:
        return 8


def adjust_scene_durations(
    scenes: list,
    lines: list,
    beat_grid: dict = None,
    vo_buffer: float = 0.5,
    min_scene_duration: float = 4.0
) -> list:
    """
    Adjust scene durations based on:
    1. Actual VO duration (+ buffer so voice doesn't cut off)
    2. Snap to beat grid (if available)
    3. Clamp to Veo-compatible durations
    
    Args:
        scenes: List of scene objects (must have 'id' and 'duration')
        lines: List of dialogue lines (must have 'scene_id' and 'actual_duration')
        beat_grid: Output from beat_detector.extract_beat_grid()
        vo_buffer: Extra seconds after VO ends before scene cut
        min_scene_duration: Minimum scene length
    
    Returns:
        Modified scenes list with adjusted durations
    """
    if not scenes:
        return scenes
    
    # Build a map of scene_id -> total VO duration
    scene_vo_durations = {}
    for line in (lines or []):
        scene_id = getattr(line, "scene_id", None)
        if scene_id is None:
            continue
        
        actual_dur = getattr(line, "actual_duration", None) or 0.0
        if scene_id not in scene_vo_durations:
            scene_vo_durations[scene_id] = 0.0
        scene_vo_durations[scene_id] += actual_dur
    
    adjustments_made = 0
    
    for scene in scenes:
        scene_id = getattr(scene, "id", None)
        current_duration = getattr(scene, "duration", 4) or 4
        
        # Get VO duration for this scene
        vo_duration = scene_vo_durations.get(scene_id, 0.0)
        
        if vo_duration > 0:
            # Needed duration = VO + buffer
            needed = vo_duration + vo_buffer
            
            # If VO needs more time than current duration, extend
            if needed > current_duration:
                new_duration = needed
            else:
                new_duration = current_duration
        else:
            # No VO, keep current duration
            new_duration = current_duration
        
        # Ensure minimum duration
        new_duration = max(new_duration, min_scene_duration)
        
        # Snap to beat if we have beat grid
        if beat_grid and beat_grid.get("beats"):
            new_duration = _snap_duration_to_beat(new_duration, beat_grid)
        
        # Clamp to Veo-compatible duration
        final_duration = clamp_to_veo_duration(new_duration)
        
        if final_duration != current_duration:
            print(f"   [TIMING] Scene {scene_id}: {current_duration}s -> {final_duration}s (VO: {vo_duration:.1f}s)")
            scene.duration = final_duration
            adjustments_made += 1
    
    if adjustments_made:
        print(f"[TIMING ENGINE] Adjusted {adjustments_made} scene(s) for audio fit")
    
    return scenes


def _snap_duration_to_beat(duration: float, beat_grid: dict) -> float:
    """
    Snap a duration to land on a beat boundary.
    """
    beats = beat_grid.get("beats", [])
    if not beats:
        return duration
    
    # Find beat closest to our target duration
    closest_beat = min(beats, key=lambda b: abs(b - duration))
    
    # Only snap if within 1 second
    if abs(closest_beat - duration) <= 1.0:
        return closest_beat
    
    return duration


def calculate_timeline(
    scenes: list,
    beat_grid: dict = None
) -> list[dict]:
    """
    Calculate the final timeline with start/end times for each scene.
    Snaps cuts to beats when possible.
    
    Returns:
        List of dicts with: scene_id, start, end, duration
    """
    timeline = []
    current_time = 0.0
    
    for scene in scenes:
        scene_id = getattr(scene, "id", None)
        duration = getattr(scene, "duration", 4)
        
        start = current_time
        end = current_time + duration
        
        # Snap end to beat if possible
        if beat_grid and beat_grid.get("beats"):
            snapped_end = snap_to_beat(end, beat_grid, tolerance=0.5)
            if snapped_end != end:
                end = snapped_end
                duration = end - start
        
        timeline.append({
            "scene_id": scene_id,
            "start": round(start, 2),
            "end": round(end, 2),
            "duration": round(duration, 2)
        })
        
        current_time = end
    
    return timeline


def get_vo_timing(
    line,
    scene_start: float,
    scene_end: float,
    vo_start_delay: float = 0.2,
    vo_end_buffer: float = 0.5
) -> dict:
    """
    Calculate when VO should start and end within a scene.
    
    Rules:
    - VO starts 0.2s after scene starts
    - VO must end 0.5s before scene ends
    
    Returns:
        dict with vo_start, vo_end timestamps
    """
    actual_duration = getattr(line, "actual_duration", 0) or 0
    
    vo_start = scene_start + vo_start_delay
    vo_end = vo_start + actual_duration
    
    # Ensure VO ends before scene cut
    max_vo_end = scene_end - vo_end_buffer
    if vo_end > max_vo_end:
        # VO is too long, it will get cut - this shouldn't happen
        # if scene durations were adjusted properly
        print(f"   [WARN] VO overruns scene: ends at {vo_end:.1f}s, scene ends at {scene_end:.1f}s")
        vo_end = max_vo_end
    
    return {
        "vo_start": round(vo_start, 2),
        "vo_end": round(vo_end, 2)
    }
