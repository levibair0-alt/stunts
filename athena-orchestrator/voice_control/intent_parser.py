"""
Intent parsing and classification for voice commands.
"""

import json
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional


class IntentType(Enum):
    """Supported intent types."""

    QUERY = "QUERY"  # Run command via subprocess/PyAutoGUI
    VERIFY = "VERIFY"  # Fetch data from Quintuple Engine
    CREATE = "CREATE"  # Trigger Generator engine
    MONETIZE = "MONETIZE"  # Request audit report from Auditor
    AUDIT = "AUDIT"  # Config/status commands
    CLARIFY = "CLARIFY"  # Request clarification
    UNKNOWN = "UNKNOWN"  # Unrecognized intent
    EMERGENCY_STOP = "EMERGENCY_STOP"  # Emergency stop
    RESUME = "RESUME"  # Resume operations


@dataclass
class ParsedIntent:
    """Parsed intent with entities and metadata."""

    intent_type: IntentType
    confidence: float
    raw_transcript: str
    entities: dict[str, Any]
    parameters: dict[str, Any]
    target_engine: Optional[str] = None
    requires_clarification: bool = False
    clarification_prompt: Optional[str] = None


class IntentParser:
    """Parses voice transcripts into structured intents."""

    # Intent classification patterns
    INTENT_PATTERNS = {
        IntentType.QUERY: [
            r"\brun\b",
            r"\bexecute\b",
            r"\bstart\b",
            r"\blaunch\b",
            r"\bopen\b",
            r"\bshow\b",
            r"\bget\b",
            r"\bfetch\b",
            r"\bfind\b",
            r"\bsearch\b",
            r"\bquery\b",
            r"\bdisplay\b",
            r"\bcheck\b",
        ],
        IntentType.VERIFY: [
            r"\bverify\b",
            r"\bvalidate\b",
            r"\bconfirm\b",
            r"\bis\s+(?:this|that)\s+(?:valid|correct|true)",
            r"\bdoes\s+(?:this|that)\s+(?:work|exist)",
            r"\bcheck\s+(?:if|whether)",
            r"\btest\b",
        ],
        IntentType.CREATE: [
            r"\bcreate\b",
            r"\bgenerate\b",
            r"\bmake\b",
            r"\bbuild\b",
            r"\bproduce\b",
            r"\bcraft\b",
            r"\bdesign\b",
            r"\bnew\b",
        ],
        IntentType.MONETIZE: [
            r"\bmonetize\b",
            r"\brevenue\b",
            r"\bprofit\b",
            r"\bearnings\b",
            r"\bincome\b",
            r"\bmoney\b",
            r"\bfinancial\b",
            r"\bpricing\b",
            r"\bsales\b",
        ],
        IntentType.AUDIT: [
            r"\baudit\b",
            r"\blog\b",
            r"\bhistory\b",
            r"\breport\b",
            r"\bstatus\b",
            r"\bconfig\b",
            r"\bsettings\b",
            r"\bmetrics\b",
            r"\banalytics\b",
        ],
    }

    # Entity extraction patterns
    ENTITY_PATTERNS = {
        "target": [
            r"(?:for|to|about)\s+([a-zA-Z_][a-zA-Z0-9_\s]*?)(?:\s+(?:from|in|at|on|with)|$)",
            r"(?:target|subject|object)\s+(?:is\s+)?([a-zA-Z_][a-zA-Z0-9_\s]*?)(?:\s+(?:from|in|at|on|with)|$)",
        ],
        "quantity": [
            r"(\d+)\s*(?:items?|records?|rows?|entries?)",
            r"(\d+(?:\.\d+)?)\s*(?:percent|%|dollars?|USD)",
        ],
        "timeframe": [
            r"(?:in\s+)?(?:the\s+)?(last|past|previous|next|upcoming)\s+(\d+)?\s*(day|week|month|year|hour|minute)s?",
            r"(?:today|yesterday|tomorrow|now|recently)",
        ],
        "location": [
            r"(?:from|in|at|on)\s+([a-zA-Z_][a-zA-Z0-9_\s]*?)(?:\s+(?:to|for|with)|$)",
        ],
    }

    # Emergency stop patterns
    EMERGENCY_PATTERNS = [
        r"emergency\s+stop",
        r"kill\s+switch",
        r"halt\s+system",
        r"stop\s+all",
        r"abort\s+all",
        r"system\s+halt",
        r"emergency\s+shutdown",
    ]

    # Resume patterns
    RESUME_PATTERNS = [
        r"resume\s+(?:athena\s+)?operations",
        r"resume\s+system",
        r"continue\s+operations",
        r"start\s+(?:athena\s+)?again",
        r"resume\s+(?:athena)?",
    ]

    def __init__(
        self,
        confidence_execute: float = 0.7,
        confidence_clarify: float = 0.4,
        safe_mode_enabled: bool = True,
    ):
        """
        Initialize intent parser.

        Args:
            confidence_execute: Minimum confidence to execute
            confidence_clarify: Minimum confidence to ask for clarification
            safe_mode_enabled: Whether SAFE_MODE is active
        """
        self.confidence_execute = confidence_execute
        self.confidence_clarify = confidence_clarify
        self.confidence_reject = 0.0
        self.safe_mode_enabled = safe_mode_enabled

        # Compile patterns
        self._compiled_intents: dict[IntentType, list[re.Pattern]] = {}
        for intent, patterns in self.INTENT_PATTERNS.items():
            self._compiled_intents[intent] = [
                re.compile(p, re.IGNORECASE) for p in patterns
            ]

        self._compiled_entities: dict[str, list[re.Pattern]] = {}
        for entity, patterns in self.ENTITY_PATTERNS.items():
            self._compiled_entities[entity] = [
                re.compile(p, re.IGNORECASE) for p in patterns
            ]

        self._emergency_patterns = [
            re.compile(p, re.IGNORECASE) for p in self.EMERGENCY_PATTERNS
        ]
        self._resume_patterns = [
            re.compile(p, re.IGNORECASE) for p in self.RESUME_PATTERNS
        ]

    def parse(self, transcript: str, whisper_confidence: float = 0.8) -> ParsedIntent:
        """
        Parse a transcript into a structured intent.

        Args:
            transcript: The transcribed text
            whisper_confidence: Confidence from Whisper transcription

        Returns:
            ParsedIntent with intent type, confidence, and entities
        """
        if not transcript:
            return ParsedIntent(
                intent_type=IntentType.UNKNOWN,
                confidence=0.0,
                raw_transcript="",
                entities={},
                parameters={},
            )

        transcript_lower = transcript.lower()

        # Check for emergency stop first (highest priority)
        for pattern in self._emergency_patterns:
            if pattern.search(transcript):
                return ParsedIntent(
                    intent_type=IntentType.EMERGENCY_STOP,
                    confidence=1.0,
                    raw_transcript=transcript,
                    entities={"command_type": "emergency_stop"},
                    parameters={},
                )

        # Check for resume command
        for pattern in self._resume_patterns:
            if pattern.search(transcript):
                return ParsedIntent(
                    intent_type=IntentType.RESUME,
                    confidence=1.0,
                    raw_transcript=transcript,
                    entities={"command_type": "resume"},
                    parameters={},
                )

        # Classify intent
        intent_scores: dict[IntentType, float] = {}
        for intent, patterns in self._compiled_intents.items():
            score = 0.0
            for pattern in patterns:
                if pattern.search(transcript):
                    score += 1.0
            if score > 0:
                intent_scores[intent] = score / len(patterns)

        # Determine primary intent
        if intent_scores:
            best_intent = max(intent_scores, key=intent_scores.get)
            base_confidence = intent_scores[best_intent]
        else:
            best_intent = IntentType.UNKNOWN
            base_confidence = 0.3

        # Combine with transcription confidence
        final_confidence = (base_confidence + whisper_confidence) / 2.0

        # Extract entities
        entities = self._extract_entities(transcript)

        # Build parameters dict
        parameters = self._build_parameters(transcript, best_intent, entities)

        # Determine action based on confidence
        requires_clarification = False
        clarification_prompt = None

        if final_confidence < self.confidence_reject:
            best_intent = IntentType.UNKNOWN
        elif final_confidence < self.confidence_clarify:
            requires_clarification = True
            clarification_prompt = self._generate_clarification(transcript)
        elif final_confidence < self.confidence_execute:
            requires_clarification = True
            clarification_prompt = f"Did you mean to {self._generate_command_description(best_intent, entities)}?"

        # Map to engine
        target_engine = self._map_to_engine(best_intent)

        return ParsedIntent(
            intent_type=best_intent,
            confidence=final_confidence,
            raw_transcript=transcript,
            entities=entities,
            parameters=parameters,
            target_engine=target_engine,
            requires_clarification=requires_clarification,
            clarification_prompt=clarification_prompt,
        )

    def _extract_entities(self, transcript: str) -> dict[str, Any]:
        """Extract entities from transcript."""
        entities: dict[str, Any] = {}

        for entity_type, patterns in self._compiled_entities.items():
            for pattern in patterns:
                match = pattern.search(transcript)
                if match:
                    if entity_type == "timeframe":
                        entities[entity_type] = {
                            "direction": match.group(1) if len(match.groups()) > 0 else None,
                            "quantity": match.group(2) if len(match.groups()) > 1 else "1",
                            "unit": match.group(3) if len(match.groups()) > 2 else match.group(0),
                        }
                    else:
                        entities[entity_type] = match.group(1).strip()
                    break

        return entities

    def _build_parameters(
        self, transcript: str, intent: IntentType, entities: dict[str, Any]
    ) -> dict[str, Any]:
        """Build command parameters from transcript and entities."""
        params: dict[str, Any] = {
            "raw_command": transcript,
            "intent": intent.value,
        }

        # Add extracted entities
        params.update(entities)

        # Extract flags/options
        flags = re.findall(r"--(\w+)(?:=([^\s]+))?", transcript)
        if flags:
            params["flags"] = {name: value if value else True for name, value in flags}

        # Extract quoted strings as arguments
        quoted = re.findall(r'"([^"]*)"', transcript)
        if quoted:
            params["quoted_args"] = quoted

        return params

    def _map_to_engine(self, intent: IntentType) -> Optional[str]:
        """Map intent type to engine name."""
        mapping = {
            IntentType.QUERY: "Sensor",
            IntentType.VERIFY: "Validator",
            IntentType.CREATE: "Generator",
            IntentType.MONETIZE: "Monetizer",
            IntentType.AUDIT: "Auditor",
        }
        return mapping.get(intent)

    def _generate_clarification(self, transcript: str) -> str:
        """Generate a clarification prompt for ambiguous input."""
        return f"I didn't fully understand '{transcript}'. Could you please rephrase that?"

    def _generate_command_description(self, intent: IntentType, entities: dict[str, Any]) -> str:
        """Generate a human-readable description of the command."""
        target = entities.get("target", "something")
        return f"{intent.value.lower()} {target}"

    def is_emergency_stop(self, transcript: str) -> bool:
        """Quick check for emergency stop command."""
        transcript_lower = transcript.lower()
        for pattern in self.EMERGENCY_PATTERNS:
            if re.search(pattern, transcript_lower):
                return True
        return False

    def is_resume(self, transcript: str) -> bool:
        """Quick check for resume command."""
        transcript_lower = transcript.lower()
        for pattern in self.RESUME_PATTERNS:
            if re.search(pattern, transcript_lower):
                return True
        return False
