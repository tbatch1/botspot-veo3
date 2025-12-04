import os
import ffmpeg
from ..config import config
from ..state import ProjectState

class Composer:
    """FFmpeg Composer for final assembly."""
    
    def compose(self, state: ProjectState) -> str:
        """
        Stitches video clips and mixes audio.
        Returns path to final video.
        """
        print("🎬 Composing final video...")
        
        # 1. Gather Inputs
        video_clips = []
        for scene in state.script.scenes:
            if scene.video_path and os.path.exists(scene.video_path):
                video_clips.append(ffmpeg.input(scene.video_path))
            else:
                print(f"⚠️ Missing video for scene {scene.id}, skipping.")
        
        if not video_clips:
            raise Exception("No video clips to compose!")

        # 2. Concatenate Video
        # Simple concat for now. Cross-fade is complex in ffmpeg-python without complex filter graphs.
        # We'll do a straight cut for v1.
        joined_video = ffmpeg.concat(*video_clips, v=1, a=0).node[0]
        
        # 3. Audio Mixing
        # We need to align VO to specific times or just sequence them.
        # For simplicity v1: Sequence VO files matching scene durations? 
        # Or just concat them if they match the script flow.
        # Let's assume we have a list of VO files corresponding to scenes/lines.
        
        audio_inputs = []
        # Collect all VO files from script lines
        for line in state.script.lines:
            if line.audio_path and os.path.exists(line.audio_path):
                audio_inputs.append(ffmpeg.input(line.audio_path))
        
        if audio_inputs:
            # Concat audio to form the narration track
            joined_audio = ffmpeg.concat(*audio_inputs, v=0, a=1).node[0]
            
            # Mix with video
            # output = ffmpeg.output(joined_video, joined_audio, filename)
            # But wait, video might be longer/shorter.
            # Let's just output video + audio.
            stream = ffmpeg.output(joined_video, joined_audio, os.path.join(config.OUTPUT_DIR, "final_ad.mp4"))
        else:
            # Silent video
            stream = ffmpeg.output(joined_video, os.path.join(config.OUTPUT_DIR, "final_ad.mp4"))
            
        # 4. Render
        output_path = os.path.join(config.OUTPUT_DIR, "final_ad.mp4")
        try:
            ffmpeg.run(stream, overwrite_output=True, capture_stdout=True, capture_stderr=True)
            print(f"✅ Final video rendered: {output_path}")
            return output_path
        except ffmpeg.Error as e:
            print(f"❌ FFmpeg Error: {e.stderr.decode('utf8')}")
            raise e
