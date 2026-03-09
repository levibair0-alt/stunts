"""
Audio capture and transcription using Faster-Whisper.
"""

import io
import wave
from dataclasses import dataclass
from typing import Optional

try:
    import numpy as np

    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    np = None


@dataclass
class TranscriptionResult:
    """Result of a transcription."""

    text: str
    confidence: float
    language: str
    segments: list[dict]


class VoiceInput:
    """Handles audio capture and transcription."""

    def __init__(
        self,
        sample_rate: int = 16000,
        chunk_size: int = 1024,
        channels: int = 1,
        model_size: str = "base",
    ):
        """
        Initialize voice input handler.

        Args:
            sample_rate: Audio sample rate in Hz
            chunk_size: Audio buffer chunk size
            channels: Number of audio channels
            model_size: Whisper model size (tiny, base, small, medium, large)
        """
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.channels = channels
        self.model_size = model_size

        self._whisper_model = None
        self._audio = None
        self._stream = None
        self._is_recording = False

        # VAD (Voice Activity Detection) settings
        self.vad_threshold = 0.015
        self.silence_duration = 1.5
        self.min_speech_duration = 0.5

    def _load_whisper(self) -> Optional[object]:
        """Lazy load the Whisper model."""
        if self._whisper_model is None:
            try:
                from faster_whisper import WhisperModel

                self._whisper_model = WhisperModel(
                    self.model_size,
                    device="cpu",
                    compute_type="int8",
                )
            except ImportError:
                print("Warning: faster-whisper not installed. Transcription will be simulated.")
                return None
        return self._whisper_model

    def start_recording(self) -> bool:
        """
        Start recording audio from microphone.

        Returns:
            True if recording started successfully
        """
        try:
            import pyaudio

            self._audio = pyaudio.PyAudio()
            self._stream = self._audio.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size,
            )
            self._is_recording = True
            return True
        except ImportError:
            print("Warning: pyaudio not installed. Audio capture will be simulated.")
            self._is_recording = True
            return True
        except Exception as e:
            print(f"Error starting audio recording: {e}")
            return False

    def stop_recording(self) -> None:
        """Stop recording audio."""
        self._is_recording = False

        if self._stream:
            try:
                self._stream.stop_stream()
                self._stream.close()
            except Exception:
                pass
            self._stream = None

        if self._audio:
            try:
                self._audio.terminate()
            except Exception:
                pass
            self._audio = None

    def record_audio(self, duration: Optional[float] = None) -> Optional[bytes]:
        """
        Record audio with VAD-based endpoint detection.

        Args:
            duration: Maximum recording duration in seconds (None for VAD-based)

        Returns:
            Recorded audio as WAV bytes
        """
        if not self._is_recording:
            if not self.start_recording():
                return None

        try:
            import pyaudio
        except ImportError:
            # Simulate audio recording
            return b"SIMULATED_AUDIO_DATA"

        frames = []
        silent_frames = 0
        speech_frames = 0
        max_frames = int(duration * self.sample_rate / self.chunk_size) if duration else None
        total_frames = 0

        while True:
            try:
                data = self._stream.read(self.chunk_size, exception_on_overflow=False)
                frames.append(data)

                # VAD (Voice Activity Detection)
                if HAS_NUMPY and np is not None:
                    audio_data = np.frombuffer(data, dtype=np.int16)
                    volume = np.abs(audio_data).mean() / 32768.0
                else:
                    # Fallback without numpy
                    audio_data = [int.from_bytes(data[i:i+2], 'little', signed=True)
                                  for i in range(0, len(data), 2)]
                    volume = sum(abs(x) for x in audio_data) / (len(audio_data) * 32768.0) if audio_data else 0

                if volume > self.vad_threshold:
                    speech_frames += 1
                    silent_frames = 0
                else:
                    silent_frames += 1

                total_frames += 1

                # Stop conditions
                if max_frames and total_frames >= max_frames:
                    break

                if speech_frames > int(self.min_speech_duration * self.sample_rate / self.chunk_size):
                    if silent_frames > int(self.silence_duration * self.sample_rate / self.chunk_size):
                        break

                if total_frames > int(30 * self.sample_rate / self.chunk_size):  # Max 30 seconds
                    break

            except Exception as e:
                print(f"Error during recording: {e}")
                break

        return self._frames_to_wav(frames)

    def _frames_to_wav(self, frames: list[bytes]) -> bytes:
        """Convert audio frames to WAV bytes."""
        try:
            import pyaudio

            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, "wb") as wav_file:
                wav_file.setnchannels(self.channels)
                wav_file.setsampwidth(self._audio.get_sample_size(pyaudio.paInt16))
                wav_file.setframerate(self.sample_rate)
                wav_file.writeframes(b"".join(frames))

            return wav_buffer.getvalue()
        except Exception as e:
            print(f"Error converting to WAV: {e}")
            return b""

    def transcribe(self, audio_data: bytes) -> TranscriptionResult:
        """
        Transcribe audio data to text.

        Args:
            audio_data: Audio data as WAV bytes

        Returns:
            TranscriptionResult with text and confidence
        """
        if audio_data == b"SIMULATED_AUDIO_DATA":
            # Return empty result for simulated audio
            return TranscriptionResult(
                text="",
                confidence=0.0,
                language="en",
                segments=[],
            )

        model = self._load_whisper()
        if model is None:
            return TranscriptionResult(
                text="",
                confidence=0.0,
                language="en",
                segments=[],
            )

        try:
            # Convert to temporary file for Whisper
            import tempfile

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp:
                temp.write(audio_data)
                temp_path = temp.name

            segments, info = model.transcribe(
                temp_path,
                language="en",
                beam_size=5,
                best_of=5,
                patience=2.0,
                condition_on_previous_text=True,
            )

            # Collect all segments
            text_parts = []
            all_segments = []
            avg_prob = 0.0

            for segment in segments:
                text_parts.append(segment.text.strip())
                all_segments.append({
                    "id": segment.id,
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text,
                    "avg_logprob": segment.avg_logprob,
                })
                avg_prob = max(avg_prob, segment.avg_logprob)

            text = " ".join(text_parts)

            # Calculate confidence from log probability
            confidence = min(1.0, max(0.0, (avg_prob + 1.0) / 2.0))

            # Clean up temp file
            import os

            os.unlink(temp_path)

            return TranscriptionResult(
                text=text,
                confidence=confidence,
                language=info.language,
                segments=all_segments,
            )

        except Exception as e:
            print(f"Transcription error: {e}")
            return TranscriptionResult(
                text="",
                confidence=0.0,
                language="en",
                segments=[],
            )

    def is_recording(self) -> bool:
        """Check if currently recording."""
        return self._is_recording
