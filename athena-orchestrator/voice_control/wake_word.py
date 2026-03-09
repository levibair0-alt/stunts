"""
Wake word detection for "Athena" activation phrase.
"""

import re
from typing import Optional


class WakeWordDetector:
    """Detects the wake word 'Athena' in audio transcripts."""

    def __init__(self, wake_word: str = "athena", sensitivity: float = 0.8):
        """
        Initialize wake word detector.

        Args:
            wake_word: The activation phrase to detect
            sensitivity: Detection sensitivity (0.0 - 1.0)
        """
        self.wake_word = wake_word.lower()
        self.sensitivity = sensitivity
        self._is_listening = False
        self._activation_phrases = [
            rf"\b{re.escape(self.wake_word)}\b",
            rf"\bhey\s+{re.escape(self.wake_word)}\b",
            rf"\bokay\s+{re.escape(self.wake_word)}\b",
            rf"\byo\s+{re.escape(self.wake_word)}\b",
        ]
        self._compiled_patterns = [re.compile(p, re.IGNORECASE) for p in self._activation_phrases]

    def detect(self, transcript: str) -> tuple[bool, Optional[str]]:
        """
        Detect wake word in transcript.

        Args:
            transcript: The transcribed text to analyze

        Returns:
            Tuple of (detected, command_text)
            - detected: True if wake word found
            - command_text: The text after the wake word, or None
        """
        if not transcript:
            return False, None

        transcript_lower = transcript.lower()

        # Check if wake word is present
        for pattern in self._compiled_patterns:
            match = pattern.search(transcript)
            if match:
                # Extract command text after wake word
                end_pos = match.end()
                command_text = transcript[end_pos:].strip()

                # Remove leading punctuation
                command_text = command_text.lstrip(",.!?;: ")

                return True, command_text if command_text else None

        # Fuzzy matching for partial wake word detection
        if self._fuzzy_match(transcript_lower):
            # Try to extract command after the partial match
            parts = transcript_lower.split(self.wake_word, 1)
            if len(parts) > 1:
                return True, parts[1].strip()

        return False, None

    def _fuzzy_match(self, text: str) -> bool:
        """
        Perform fuzzy matching for wake word detection.

        Args:
            text: Lowercase text to match against

        Returns:
            True if fuzzy match found
        """
        # Simple Levenshtein distance-based fuzzy match
        words = text.split()
        for word in words:
            similarity = self._calculate_similarity(word, self.wake_word)
            if similarity >= self.sensitivity:
                return True
        return False

    def _calculate_similarity(self, s1: str, s2: str) -> float:
        """
        Calculate similarity between two strings using Levenshtein distance.

        Args:
            s1: First string
            s2: Second string

        Returns:
            Similarity score between 0.0 and 1.0
        """
        if len(s1) < len(s2):
            return self._calculate_similarity(s2, s1)

        if len(s2) == 0:
            return 0.0

        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        distance = previous_row[-1]
        max_len = max(len(s1), len(s2))

        return 1.0 - (distance / max_len) if max_len > 0 else 1.0

    def is_listening(self) -> bool:
        """Check if the system is currently listening for commands."""
        return self._is_listening

    def start_listening(self) -> None:
        """Start listening for commands."""
        self._is_listening = True

    def stop_listening(self) -> None:
        """Stop listening for commands."""
        self._is_listening = False
