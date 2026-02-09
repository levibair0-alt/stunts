"""
ATHENA 875 Protocol - Submission Classifier Module

PURPOSE:
    Deterministic classification of marketplace submissions into 10 industry categories
    using configurable YAML taxonomy with scoring thresholds and confidence metrics.

DEPENDENCIES:
    - pyyaml>=6.0.1 (YAML parsing)
    - Python 3.8+ (standard library: re, datetime, typing)

ENVIRONMENT:
    - CONFIG_PATH: Path to config directory (default: ./config)
    - TAXONOMY_FILE: athena_875_taxonomy.yaml location
    - MIN_SCORE: Minimum classification score threshold (default: 3)
    - MIN_MARGIN: Minimum margin between top scores (default: 1)

USAGE:
    classifier = Athena875Classifier(config_path="./config")
    result = classifier.classify_submission(submission_data)
    
    if result['meets_thresholds']:
        print(f"Classified as: {result['classified_industry']}")
    else:
        print("Classification confidence too low")

TESTING:
    Run module directly:
        python athena_875_classifier.py
    
    Or use pytest:
        pytest tests/test_athena_875_classifier.py

PROTOCOL COMPLIANCE:
    - ATHENA-875-2026 v1.0.0
    - Deterministic scoring algorithm
    - Handshake verification required
    - Configurable thresholds via YAML

LEDGER NOTES:
    2026-02-09: Initial implementation with 10-industry taxonomy
    
RISKS:
    1. Taxonomy keyword overlap may cause ambiguous classifications
       Mitigation: Use min_margin threshold to detect low confidence
    2. Industry definitions may need periodic updates
       Mitigation: Externalized YAML configuration for easy updates
    3. Domain bonus scoring may overweight URL patterns
       Mitigation: Configurable domain_bonus weight in taxonomy
"""

import yaml
import re
import os
from datetime import datetime, timezone
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field


@dataclass
class ClassificationResult:
    """Structured result from ATHENA 875 classification"""
    classified_industry: str
    industry_id: int
    confidence_score: float
    classification_score: float
    margin: float
    meets_thresholds: bool
    all_industry_scores: Dict[str, float]
    matched_keywords: List[str]
    protocol_version: str
    timestamp: str
    handshake_verified: bool = False
    warnings: List[str] = field(default_factory=list)


class Athena875Classifier:
    """
    ATHENA 875 Protocol Classifier
    
    Deterministic submission classification with configurable scoring thresholds.
    Implements handshake verification and confidence-based filtering.
    """
    
    PROTOCOL_NAME = "ATHENA 875"
    PROTOCOL_VERSION = "1.0.0"
    EXPECTED_VERIFICATION_CODE = "ATHENA-875-VERIFIED"
    
    def __init__(self, config_path: str = "./config", taxonomy_file: str = "athena_875_taxonomy.yaml"):
        """
        Initialize classifier with taxonomy configuration
        
        Args:
            config_path: Path to configuration directory
            taxonomy_file: Name of taxonomy YAML file
        
        Raises:
            RuntimeError: If taxonomy cannot be loaded or handshake fails
        """
        self.config_path = config_path
        self.taxonomy_file = taxonomy_file
        self.taxonomy = self._load_taxonomy()
        
        # Extract configuration
        self.protocol_config = self.taxonomy.get('protocol', {})
        self.classification_config = self.taxonomy.get('classification', {})
        self.industries = self.taxonomy.get('industries', {})
        self.domain_patterns = self.taxonomy.get('domain_patterns', {})
        
        # Verify protocol handshake
        self._verify_handshake()
        
        # Load thresholds
        self.min_score = self.classification_config.get('min_score', 3)
        self.min_margin = self.classification_config.get('min_margin', 1)
        self.confidence_threshold = self.classification_config.get('confidence_threshold', 0.65)
        
        print(f"[ATHENA-875] Classifier initialized")
        print(f"[ATHENA-875] Protocol: {self.PROTOCOL_NAME} v{self.PROTOCOL_VERSION}")
        print(f"[ATHENA-875] Thresholds - min_score: {self.min_score}, min_margin: {self.min_margin}")
        print(f"[ATHENA-875] Industries loaded: {len(self.industries)}")
    
    def _load_taxonomy(self) -> Dict[str, Any]:
        """Load and parse taxonomy YAML configuration"""
        taxonomy_path = os.path.join(self.config_path, self.taxonomy_file)
        
        if not os.path.exists(taxonomy_path):
            raise RuntimeError(
                f"ATHENA-875 CRITICAL: Taxonomy file not found at {taxonomy_path}\n"
                "Classifier cannot operate without taxonomy configuration."
            )
        
        try:
            with open(taxonomy_path, 'r', encoding='utf-8') as f:
                taxonomy = yaml.safe_load(f)
            
            if not taxonomy:
                raise ValueError("Taxonomy file is empty")
            
            print(f"[ATHENA-875] Taxonomy loaded from {taxonomy_path}")
            return taxonomy
            
        except yaml.YAMLError as e:
            raise RuntimeError(f"ATHENA-875 ERROR: Failed to parse taxonomy YAML: {e}")
        except Exception as e:
            raise RuntimeError(f"ATHENA-875 ERROR: Failed to load taxonomy: {e}")
    
    def _verify_handshake(self) -> None:
        """
        Verify ATHENA 875 protocol handshake
        
        Ensures taxonomy configuration contains proper protocol identification
        and verification code. Refuses to operate if handshake fails.
        """
        if not self.protocol_config.get('handshake_required', False):
            raise RuntimeError(
                "ATHENA-875 HANDSHAKE FAILURE: handshake_required not set to true\n"
                "Protocol compliance requires explicit handshake verification."
            )
        
        verification_code = self.protocol_config.get('verification_code', '')
        if verification_code != self.EXPECTED_VERIFICATION_CODE:
            raise RuntimeError(
                f"ATHENA-875 HANDSHAKE FAILURE: Invalid verification code\n"
                f"Expected: {self.EXPECTED_VERIFICATION_CODE}\n"
                f"Received: {verification_code}\n"
                "Classifier will refuse to operate."
            )
        
        protocol_name = self.protocol_config.get('name', '')
        if protocol_name != self.PROTOCOL_NAME:
            raise RuntimeError(
                f"ATHENA-875 HANDSHAKE FAILURE: Protocol name mismatch\n"
                f"Expected: {self.PROTOCOL_NAME}\n"
                f"Received: {protocol_name}"
            )
        
        print(f"[ATHENA-875] Handshake verified: {self.EXPECTED_VERIFICATION_CODE}")
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for keyword matching"""
        if not text:
            return ""
        return text.lower().strip()
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract individual words from text for matching"""
        normalized = self._normalize_text(text)
        # Remove special characters and split
        words = re.findall(r'\b[a-z]+\b', normalized)
        return words
    
    def _calculate_industry_score(
        self, 
        text_content: str, 
        industry_key: str, 
        domain_url: Optional[str] = None
    ) -> Tuple[float, List[str]]:
        """
        Calculate deterministic score for a specific industry
        
        Args:
            text_content: Combined text (title + description + tags)
            industry_key: Industry identifier from taxonomy
            domain_url: Optional website URL for domain bonus
        
        Returns:
            Tuple of (total_score, matched_keywords)
        """
        industry_config = self.industries[industry_key]
        keywords = industry_config.get('keywords', {})
        scoring = industry_config.get('scoring', {})
        
        primary_keywords = keywords.get('primary', [])
        secondary_keywords = keywords.get('secondary', [])
        
        primary_weight = scoring.get('primary_weight', 2.0)
        secondary_weight = scoring.get('secondary_weight', 1.0)
        domain_bonus_weight = scoring.get('domain_bonus', 1.5)
        
        normalized_content = self._normalize_text(text_content)
        matched_keywords = []
        score = 0.0
        
        # Score primary keywords
        for keyword in primary_keywords:
            keyword_pattern = r'\b' + re.escape(self._normalize_text(keyword)) + r'\b'
            matches = re.findall(keyword_pattern, normalized_content)
            if matches:
                score += len(matches) * primary_weight
                matched_keywords.append(keyword)
        
        # Score secondary keywords
        for keyword in secondary_keywords:
            keyword_pattern = r'\b' + re.escape(self._normalize_text(keyword)) + r'\b'
            matches = re.findall(keyword_pattern, normalized_content)
            if matches:
                score += len(matches) * secondary_weight
                matched_keywords.append(keyword)
        
        # Domain bonus if URL matches industry patterns
        if domain_url:
            domain_normalized = self._normalize_text(domain_url)
            industry_domains = self.domain_patterns.get(industry_key, [])
            
            for pattern in industry_domains:
                if self._normalize_text(pattern) in domain_normalized:
                    score += domain_bonus_weight
                    break
        
        return score, matched_keywords
    
    def _calculate_confidence(
        self, 
        top_score: float, 
        second_score: float, 
        total_possible: float
    ) -> float:
        """
        Calculate confidence score based on score separation and magnitude
        
        Confidence is high when:
        1. Top score is significantly higher than second score (margin)
        2. Top score is substantial (not all scores near zero)
        """
        if total_possible == 0:
            return 0.0
        
        # Normalized score strength (0-1)
        score_strength = min(top_score / max(total_possible * 0.3, 1.0), 1.0)
        
        # Margin ratio (how much better is first vs second)
        if second_score == 0:
            margin_ratio = 1.0
        else:
            margin_ratio = min((top_score - second_score) / top_score, 1.0)
        
        # Combine both factors
        confidence = (score_strength * 0.6) + (margin_ratio * 0.4)
        
        return round(confidence, 3)
    
    def classify_submission(self, submission: Dict[str, Any]) -> ClassificationResult:
        """
        Classify a submission into an industry category
        
        Args:
            submission: Dictionary containing submission data
                Required keys: title, description
                Optional keys: tags, website_url, additional_context
        
        Returns:
            ClassificationResult with industry, scores, and confidence metrics
        
        Raises:
            ValueError: If required fields are missing
        """
        # Validate required fields
        if 'title' not in submission or not submission['title']:
            raise ValueError("ATHENA-875 ERROR: Missing or empty required field 'title'")
        if 'description' not in submission or not submission['description']:
            raise ValueError("ATHENA-875 ERROR: Missing or empty required field 'description'")
        
        # Combine text content for analysis
        text_parts = [
            submission.get('title', ''),
            submission.get('description', ''),
            submission.get('additional_context', '')
        ]
        
        # Add tags if present
        tags = submission.get('tags', [])
        if tags:
            text_parts.append(' '.join(tags))
        
        combined_text = ' '.join(text_parts)
        website_url = submission.get('website_url', None)
        
        # Calculate scores for all industries
        industry_scores: Dict[str, float] = {}
        all_matched_keywords: Dict[str, List[str]] = {}
        
        for industry_key in self.industries.keys():
            score, matched_kw = self._calculate_industry_score(
                combined_text, 
                industry_key, 
                website_url
            )
            industry_scores[industry_key] = score
            all_matched_keywords[industry_key] = matched_kw
        
        # Sort industries by score
        sorted_industries = sorted(
            industry_scores.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        # Get top two scores
        top_industry, top_score = sorted_industries[0]
        second_score = sorted_industries[1][1] if len(sorted_industries) > 1 else 0.0
        
        # Calculate margin and confidence
        margin = top_score - second_score
        
        # Estimate total possible score for confidence calculation
        total_possible_score = len(self.industries) * 10  # Rough estimate
        confidence = self._calculate_confidence(top_score, second_score, total_possible_score)
        
        # Check thresholds
        meets_score_threshold = top_score >= self.min_score
        meets_margin_threshold = margin >= self.min_margin
        meets_thresholds = meets_score_threshold and meets_margin_threshold
        
        # Collect warnings
        warnings = []
        if not meets_score_threshold:
            warnings.append(f"Classification score {top_score} below minimum {self.min_score}")
        if not meets_margin_threshold:
            warnings.append(f"Score margin {margin} below minimum {self.min_margin}")
        if confidence < self.confidence_threshold:
            warnings.append(f"Confidence {confidence} below threshold {self.confidence_threshold}")
        
        # Get industry metadata
        industry_config = self.industries[top_industry]
        industry_id = industry_config.get('id', 0)
        
        # Build result
        result = ClassificationResult(
            classified_industry=top_industry,
            industry_id=industry_id,
            confidence_score=confidence,
            classification_score=top_score,
            margin=margin,
            meets_thresholds=meets_thresholds,
            all_industry_scores=industry_scores,
            matched_keywords=all_matched_keywords[top_industry],
            protocol_version=self.PROTOCOL_VERSION,
            timestamp=datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            handshake_verified=True,
            warnings=warnings
        )
        
        return result
    
    def format_result(self, result: ClassificationResult) -> Dict[str, Any]:
        """Convert ClassificationResult to dictionary for serialization"""
        return {
            'classified_industry': result.classified_industry,
            'industry_id': result.industry_id,
            'confidence_score': result.confidence_score,
            'classification_score': result.classification_score,
            'margin': result.margin,
            'meets_thresholds': result.meets_thresholds,
            'all_industry_scores': result.all_industry_scores,
            'matched_keywords': result.matched_keywords,
            'protocol_version': result.protocol_version,
            'timestamp': result.timestamp,
            'handshake_verified': result.handshake_verified,
            'warnings': result.warnings
        }
    
    def get_industry_label(self, industry_key: str) -> str:
        """Get human-readable label for an industry"""
        return self.industries.get(industry_key, {}).get('label', industry_key)
    
    def validate_submission(self, submission: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate submission structure before classification
        
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        # Check required fields
        if 'title' not in submission or not submission['title']:
            errors.append("Missing or empty 'title' field")
        elif len(submission['title']) < 5:
            errors.append("Title must be at least 5 characters")
        
        if 'description' not in submission or not submission['description']:
            errors.append("Missing or empty 'description' field")
        elif len(submission['description']) < 50:
            errors.append("Description must be at least 50 characters")
        
        # Validate optional fields if present
        if 'website_url' in submission and submission['website_url']:
            url = submission['website_url']
            if not url.startswith(('http://', 'https://')):
                errors.append("Website URL must start with http:// or https://")
        
        if 'tags' in submission:
            if not isinstance(submission['tags'], list):
                errors.append("Tags must be a list")
        
        is_valid = len(errors) == 0
        return is_valid, errors


if __name__ == "__main__":
    """
    Test the classifier with example submissions
    """
    import json
    
    print("=" * 80)
    print("ATHENA 875 Protocol - Classifier Test Suite")
    print("=" * 80)
    
    # Initialize classifier
    try:
        classifier = Athena875Classifier(config_path="config")
    except Exception as e:
        print(f"ERROR: Failed to initialize classifier: {e}")
        exit(1)
    
    # Test submission 1: Healthcare
    print("\n" + "-" * 80)
    print("TEST 1: Healthcare Submission")
    print("-" * 80)
    
    submission_healthcare = {
        'submission_id': 'SUB-2026-001234',
        'title': 'MediTrack - Patient Management Platform',
        'description': '''MediTrack is a comprehensive healthcare platform designed for hospitals
        and clinics to manage patient records, appointments, and medical histories.
        Features include HIPAA-compliant storage, telemedicine integration,
        electronic health records (EHR), and real-time patient monitoring dashboards.''',
        'tags': ['healthcare', 'patient management', 'telemedicine', 'EHR'],
        'website_url': 'https://meditrack.health',
        'submitter_info': {
            'name': 'John Smith',
            'email': 'john.smith@meditrack.com',
            'organization': 'MediTrack Inc.'
        }
    }
    
    result = classifier.classify_submission(submission_healthcare)
    result_dict = classifier.format_result(result)
    
    print(f"\nClassified as: {classifier.get_industry_label(result.classified_industry)}")
    print(f"Industry ID: {result.industry_id}")
    print(f"Score: {result.classification_score}")
    print(f"Confidence: {result.confidence_score}")
    print(f"Margin: {result.margin}")
    print(f"Meets Thresholds: {result.meets_thresholds}")
    print(f"Matched Keywords: {', '.join(result.matched_keywords[:10])}")
    if result.warnings:
        print(f"Warnings: {', '.join(result.warnings)}")
    
    # Test submission 2: Technology
    print("\n" + "-" * 80)
    print("TEST 2: Technology Submission")
    print("-" * 80)
    
    submission_tech = {
        'title': 'CloudSync API Gateway',
        'description': '''CloudSync is a modern API gateway and microservices platform
        built for cloud-native applications. Features include automatic scaling,
        service mesh integration, real-time monitoring, and DevOps automation tools.
        Built with Kubernetes and designed for high-performance distributed systems.''',
        'tags': ['cloud', 'api', 'microservices', 'devops', 'kubernetes'],
        'website_url': 'https://cloudsync.io'
    }
    
    result = classifier.classify_submission(submission_tech)
    
    print(f"\nClassified as: {classifier.get_industry_label(result.classified_industry)}")
    print(f"Industry ID: {result.industry_id}")
    print(f"Score: {result.classification_score}")
    print(f"Confidence: {result.confidence_score}")
    print(f"Margin: {result.margin}")
    print(f"Meets Thresholds: {result.meets_thresholds}")
    print(f"Matched Keywords: {', '.join(result.matched_keywords[:10])}")
    
    # Test submission 3: Ambiguous (low confidence)
    print("\n" + "-" * 80)
    print("TEST 3: Ambiguous Submission (Low Confidence)")
    print("-" * 80)
    
    submission_ambiguous = {
        'title': 'Business Solutions Inc',
        'description': '''We provide various business solutions for companies of all sizes.
        Our services help organizations improve efficiency and reduce costs.''',
        'tags': ['business', 'solutions']
    }
    
    result = classifier.classify_submission(submission_ambiguous)
    
    print(f"\nClassified as: {classifier.get_industry_label(result.classified_industry)}")
    print(f"Industry ID: {result.industry_id}")
    print(f"Score: {result.classification_score}")
    print(f"Confidence: {result.confidence_score}")
    print(f"Margin: {result.margin}")
    print(f"Meets Thresholds: {result.meets_thresholds}")
    if result.warnings:
        print(f"⚠️  WARNINGS:")
        for warning in result.warnings:
            print(f"   - {warning}")
    
    print("\n" + "=" * 80)
    print("Test suite completed")
    print("=" * 80)
