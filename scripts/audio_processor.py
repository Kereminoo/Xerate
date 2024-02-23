import os
from pydub import AudioSegment


class AudioProcessor:
    # Class to process audio
    def __init__(self) -> None:
        # Get the path of ffmpeg and add it to PATH
        ffmpeg_path = os.path.join(os.path.dirname(
            os.path.dirname(__file__)), "bin")
        os.environ["PATH"] += os.pathsep + ffmpeg_path

    @staticmethod
    def change_speed(input_audio, speed_factor) -> AudioSegment:
        # If the AudioSegment is not already loaded, load it
        if not isinstance(input_audio, AudioSegment):
            audio = AudioSegment.from_file(input_audio)
        else:
            audio = input_audio

        # Change the frame rate, which correlates to the speed.
        adjusted_audio = audio._spawn(audio.raw_data, overrides={
            "frame_rate": int(audio.frame_rate * speed_factor)
        })

        # Set the channels and frame rate to the original audio
        adjusted_audio = (
            adjusted_audio.set_frame_rate(audio.frame_rate)
                          .set_channels(audio.channels)
        )

        return adjusted_audio

    @staticmethod
    def crop_audio(audio, start_ms, end_ms, fade_duration=500) -> AudioSegment:
        # Crop the audio
        cropped_audio = audio[start_ms:end_ms]

        # Add fade out effect
        if fade_duration > 0:
            fade_out = cropped_audio[-fade_duration:].fade_out(fade_duration)
            cropped_audio = cropped_audio[:-fade_duration] + fade_out

        return cropped_audio

    @staticmethod
    def merge_audio_files_with_breaks(audio_files, output_file, break_duration_ms, audio_cuts, map_queue) -> None:
        merged_audio = AudioSegment.empty()

        for i, file_path in enumerate(audio_files):
            # Load the audio
            audio = AudioSegment.from_file(file_path)
            audio_start, audio_end = audio_cuts[i]
            audio = AudioProcessor.change_speed(audio, map_queue[i][0])
            audio = AudioProcessor.crop_audio(audio, audio_start, audio_end)

            merged_audio += audio

            if i < len(audio_files) - 1:
                merged_audio += AudioSegment.silent(duration=break_duration_ms)

        merged_audio.export(output_file, format='mp3')

    @staticmethod
    def generate_map_audio(audio_file_path, new_audio_file_path, rate) -> None:
        new_audio = AudioProcessor.change_speed(audio_file_path, rate)
        audio_format = new_audio_file_path.split('.')[-1]
        new_audio.export(new_audio_file_path, format=audio_format)
