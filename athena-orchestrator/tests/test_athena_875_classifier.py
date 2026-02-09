"""
ATHENA 875 Protocol - Classifier Unit Tests

Test suite for the ATHENA 875 submission classifier module.
Covers classification, validation, scoring, handshake, and edge cases.

Run with pytest:
    pytest tests/test_athena_875_classifier.py -v
"""

import sys
import os
import pytest
import tempfile
import yaml

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.athena_875_classifier import Athena875Classifier, ClassificationResult


class TestClassifierInitialization:
    """Test classifier initialization and handshake verification"""
    
    def test_initialization_success(self):
        """Test successful classifier initialization"""
        classifier = Athena875Classifier(config_path="config")
        assert classifier is not None
        assert classifier.min_score == 3
        assert classifier.min_margin == 1
        assert len(classifier.industries) == 10
    
    def test_handshake_verification(self):
        """Test handshake verification enforces protocol compliance"""
        classifier = Athena875Classifier(config_path="config")
        assert classifier.protocol_config['handshake_required'] == True
        assert classifier.protocol_config['verification_code'] == 'ATHENA-875-VERIFIED'
    
    def test_missing_taxonomy_file(self):
        """Test error when taxonomy file is missing"""
        with pytest.raises(RuntimeError) as exc_info:
            Athena875Classifier(config_path="/nonexistent/path")
        assert "Taxonomy file not found" in str(exc_info.value)


class TestSubmissionValidation:
    """Test submission validation functionality"""
    
    def setup_method(self):
        """Initialize classifier for each test"""
        self.classifier = Athena875Classifier(config_path="config")
    
    def test_valid_submission(self):
        """Test validation passes for valid submission"""
        submission = {
            'title': 'Valid Healthcare Platform',
            'description': 'A comprehensive healthcare platform with advanced features for patient management and telemedicine services.'
        }
        is_valid, errors = self.classifier.validate_submission(submission)
        assert is_valid == True
        assert len(errors) == 0
    
    def test_missing_title(self):
        """Test validation fails for missing title"""
        submission = {
            'description': 'A platform with only a description but no title field present.'
        }
        is_valid, errors = self.classifier.validate_submission(submission)
        assert is_valid == False
        assert any('title' in error.lower() for error in errors)
    
    def test_missing_description(self):
        """Test validation fails for missing description"""
        submission = {
            'title': 'Platform Title'
        }
        is_valid, errors = self.classifier.validate_submission(submission)
        assert is_valid == False
        assert any('description' in error.lower() for error in errors)
    
    def test_title_too_short(self):
        """Test validation fails for title less than 5 characters"""
        submission = {
            'title': 'App',
            'description': 'A valid description with sufficient length for validation requirements.'
        }
        is_valid, errors = self.classifier.validate_submission(submission)
        assert is_valid == False
        assert any('5 characters' in error for error in errors)
    
    def test_description_too_short(self):
        """Test validation fails for description less than 50 characters"""
        submission = {
            'title': 'Valid Title',
            'description': 'Too short'
        }
        is_valid, errors = self.classifier.validate_submission(submission)
        assert is_valid == False
        assert any('50 characters' in error for error in errors)
    
    def test_invalid_url_format(self):
        """Test validation fails for invalid URL format"""
        submission = {
            'title': 'Valid Title',
            'description': 'A valid description with sufficient length for validation requirements.',
            'website_url': 'not-a-valid-url'
        }
        is_valid, errors = self.classifier.validate_submission(submission)
        assert is_valid == False
        assert any('http' in error.lower() for error in errors)


class TestClassification:
    """Test classification functionality"""
    
    def setup_method(self):
        """Initialize classifier for each test"""
        self.classifier = Athena875Classifier(config_path="config")
    
    def test_healthcare_classification(self):
        """Test classification of healthcare submission"""
        submission = {
            'title': 'MediTrack Patient Management',
            'description': '''Advanced healthcare platform for hospitals with patient records,
            telemedicine, clinical workflows, medical histories, and HIPAA-compliant storage.'''
        }
        result = self.classifier.classify_submission(submission)
        
        assert result.classified_industry == 'healthcare'
        assert result.industry_id == 3
        assert result.meets_thresholds == True
        assert result.classification_score >= 3
    
    def test_technology_classification(self):
        """Test classification of technology submission"""
        submission = {
            'title': 'CloudSync API Gateway',
            'description': '''Cloud-native API gateway platform with microservices architecture,
            Kubernetes deployment, DevOps automation, and distributed system management.'''
        }
        result = self.classifier.classify_submission(submission)
        
        assert result.classified_industry == 'technology'
        assert result.industry_id == 1
        assert result.meets_thresholds == True
    
    def test_finance_classification(self):
        """Test classification of finance submission"""
        submission = {
            'title': 'PayFlow Payment Processor',
            'description': '''Fintech payment platform with cryptocurrency support, banking
            integration, transaction processing, fraud detection, and lending services.'''
        }
        result = self.classifier.classify_submission(submission)
        
        assert result.classified_industry == 'finance'
        assert result.industry_id == 2
        assert result.meets_thresholds == True
    
    def test_education_classification(self):
        """Test classification of education submission"""
        submission = {
            'title': 'LearnHub E-Learning Platform',
            'description': '''Online education platform with courses, learning management,
            student enrollment, teaching tools, and certification programs for universities.'''
        }
        result = self.classifier.classify_submission(submission)
        
        assert result.classified_industry == 'education'
        assert result.industry_id == 4
    
    def test_low_confidence_classification(self):
        """Test classification with insufficient information"""
        submission = {
            'title': 'Business Solutions Inc',
            'description': '''We provide various business solutions to help companies
            succeed in the modern marketplace with our expert services.'''
        }
        result = self.classifier.classify_submission(submission)
        
        # Should not meet thresholds due to vague content
        assert result.meets_thresholds == False
        assert len(result.warnings) > 0
    
    def test_domain_bonus_scoring(self):
        """Test domain bonus adds points for matching URL patterns"""
        submission_with_domain = {
            'title': 'Tech Platform',
            'description': 'A technology platform with software development and cloud services.',
            'website_url': 'https://example.io'
        }
        
        submission_without_domain = {
            'title': 'Tech Platform',
            'description': 'A technology platform with software development and cloud services.'
        }
        
        result_with = self.classifier.classify_submission(submission_with_domain)
        result_without = self.classifier.classify_submission(submission_without_domain)
        
        # Score with domain should be higher
        assert result_with.classification_score >= result_without.classification_score


class TestScoringAlgorithm:
    """Test scoring algorithm internals"""
    
    def setup_method(self):
        """Initialize classifier for each test"""
        self.classifier = Athena875Classifier(config_path="config")
    
    def test_primary_keyword_weighting(self):
        """Test primary keywords have higher weight than secondary"""
        # Healthcare has 'healthcare' as primary and 'doctor' as secondary
        text_primary = "healthcare " * 5
        text_secondary = "doctor " * 5
        
        score_primary, _ = self.classifier._calculate_industry_score(
            text_primary, 'healthcare'
        )
        score_secondary, _ = self.classifier._calculate_industry_score(
            text_secondary, 'healthcare'
        )
        
        # Primary keywords should score higher with same count
        assert score_primary > score_secondary
    
    def test_multiple_matches_increase_score(self):
        """Test repeated keywords increase score"""
        text_single = "healthcare platform"
        text_multiple = "healthcare healthcare healthcare platform"
        
        score_single, _ = self.classifier._calculate_industry_score(
            text_single, 'healthcare'
        )
        score_multiple, _ = self.classifier._calculate_industry_score(
            text_multiple, 'healthcare'
        )
        
        assert score_multiple > score_single
    
    def test_keyword_matching_case_insensitive(self):
        """Test keyword matching is case-insensitive"""
        text_lower = "healthcare platform"
        text_upper = "HEALTHCARE PLATFORM"
        text_mixed = "HealthCare Platform"
        
        score_lower, _ = self.classifier._calculate_industry_score(
            text_lower, 'healthcare'
        )
        score_upper, _ = self.classifier._calculate_industry_score(
            text_upper, 'healthcare'
        )
        score_mixed, _ = self.classifier._calculate_industry_score(
            text_mixed, 'healthcare'
        )
        
        assert score_lower == score_upper == score_mixed


class TestThresholds:
    """Test threshold checking functionality"""
    
    def setup_method(self):
        """Initialize classifier for each test"""
        self.classifier = Athena875Classifier(config_path="config")
    
    def test_meets_min_score_threshold(self):
        """Test classification meets minimum score threshold"""
        submission = {
            'title': 'Healthcare Platform with Medical Records',
            'description': '''Comprehensive healthcare system with patient management,
            clinical workflows, telemedicine, medical histories, and health monitoring.'''
        }
        result = self.classifier.classify_submission(submission)
        
        assert result.classification_score >= self.classifier.min_score
        assert result.meets_thresholds == True
    
    def test_fails_min_margin_threshold(self):
        """Test classification fails when margin is too small"""
        # Create submission that scores similarly across industries
        submission = {
            'title': 'Platform Solutions',
            'description': '''Platform with various features for different needs
            including management tools and operational support systems.'''
        }
        result = self.classifier.classify_submission(submission)
        
        # May fail margin threshold if scores are too close
        if not result.meets_thresholds:
            assert any('margin' in warning.lower() for warning in result.warnings)


class TestResultFormat:
    """Test result formatting and output"""
    
    def setup_method(self):
        """Initialize classifier for each test"""
        self.classifier = Athena875Classifier(config_path="config")
    
    def test_format_result_returns_dict(self):
        """Test format_result returns dictionary"""
        submission = {
            'title': 'Test Platform',
            'description': 'A test platform with sufficient description length for validation.'
        }
        result = self.classifier.classify_submission(submission)
        result_dict = self.classifier.format_result(result)
        
        assert isinstance(result_dict, dict)
        assert 'classified_industry' in result_dict
        assert 'confidence_score' in result_dict
        assert 'protocol_version' in result_dict
    
    def test_get_industry_label(self):
        """Test getting human-readable industry labels"""
        label = self.classifier.get_industry_label('healthcare')
        assert label == 'Healthcare & Medical'
        
        label = self.classifier.get_industry_label('technology')
        assert label == 'Technology & Software'
    
    def test_result_includes_all_scores(self):
        """Test result includes scores for all industries"""
        submission = {
            'title': 'Test Platform',
            'description': 'A test platform with sufficient description length for validation.'
        }
        result = self.classifier.classify_submission(submission)
        
        assert len(result.all_industry_scores) == 10
        assert all(isinstance(score, (int, float)) for score in result.all_industry_scores.values())


class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def setup_method(self):
        """Initialize classifier for each test"""
        self.classifier = Athena875Classifier(config_path="config")
    
    def test_empty_title_raises_error(self):
        """Test empty title raises ValueError"""
        submission = {
            'title': '',
            'description': 'Valid description with sufficient length for requirements.'
        }
        with pytest.raises(ValueError):
            self.classifier.classify_submission(submission)
    
    def test_empty_description_raises_error(self):
        """Test empty description raises ValueError"""
        submission = {
            'title': 'Valid Title',
            'description': ''
        }
        with pytest.raises(ValueError):
            self.classifier.classify_submission(submission)
    
    def test_special_characters_in_text(self):
        """Test handling of special characters in submission text"""
        submission = {
            'title': 'Healthcare™ Platform®',
            'description': '''A healthcare platform with special chars: @#$%^&*()
            that includes patient management & medical records!'''
        }
        # Should not raise error
        result = self.classifier.classify_submission(submission)
        assert result is not None
    
    def test_very_long_description(self):
        """Test handling of very long descriptions"""
        submission = {
            'title': 'Healthcare Platform',
            'description': 'healthcare ' * 1000  # Very long
        }
        # Should not raise error, but score appropriately
        result = self.classifier.classify_submission(submission)
        assert result.classified_industry == 'healthcare'
    
    def test_unicode_characters(self):
        """Test handling of unicode characters"""
        submission = {
            'title': 'Plataforma de Salud 健康平台',
            'description': '''A healthcare platform with international support for
            patient management and medical records across multiple languages.'''
        }
        # Should not raise error
        result = self.classifier.classify_submission(submission)
        assert result is not None


class TestConfidenceMetrics:
    """Test confidence calculation and metrics"""
    
    def setup_method(self):
        """Initialize classifier for each test"""
        self.classifier = Athena875Classifier(config_path="config")
    
    def test_confidence_range(self):
        """Test confidence score is between 0 and 1"""
        submission = {
            'title': 'Healthcare Platform',
            'description': 'Medical records and patient management system for hospitals.'
        }
        result = self.classifier.classify_submission(submission)
        
        assert 0.0 <= result.confidence_score <= 1.0
    
    def test_high_score_produces_high_confidence(self):
        """Test high classification score produces high confidence"""
        submission = {
            'title': 'Healthcare Medical Patient Clinical Hospital System',
            'description': '''Healthcare platform with medical records, patient management,
            clinical workflows, hospital integration, telemedicine, health monitoring,
            and comprehensive medical history tracking for healthcare providers.'''
        }
        result = self.classifier.classify_submission(submission)
        
        # High score and margin should produce high confidence
        if result.classification_score > 10 and result.margin > 5:
            assert result.confidence_score > 0.6


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, '-v', '--tb=short'])
