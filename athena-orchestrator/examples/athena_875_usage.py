#!/usr/bin/env python3
"""
ATHENA 875 Protocol - Classifier Usage Examples

This script demonstrates various use cases for the ATHENA 875 submission classifier
including basic classification, validation, batch processing, and integration patterns.

Run this script from the athena-orchestrator directory:
    python examples/athena_875_usage.py
"""

import sys
import os
import json

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.athena_875_classifier import Athena875Classifier


def example_1_basic_classification():
    """Example 1: Basic submission classification"""
    print("\n" + "=" * 80)
    print("EXAMPLE 1: Basic Classification")
    print("=" * 80)
    
    classifier = Athena875Classifier(config_path="config")
    
    submission = {
        'title': 'FinanceFlow - Payment Processing Platform',
        'description': '''FinanceFlow is a modern payment processing and fintech
        platform for businesses. Features include multi-currency transactions,
        fraud detection, cryptocurrency support, automated invoicing, and 
        real-time financial analytics. Designed for banks, merchants, and 
        payment service providers.''',
        'tags': ['fintech', 'payment', 'banking', 'cryptocurrency'],
        'website_url': 'https://financeflow.pay'
    }
    
    result = classifier.classify_submission(submission)
    
    print(f"\nSubmission: {submission['title']}")
    print(f"Classified as: {classifier.get_industry_label(result.classified_industry)}")
    print(f"Industry ID: {result.industry_id}")
    print(f"Confidence Score: {result.confidence_score}")
    print(f"Classification Score: {result.classification_score}")
    print(f"Margin: {result.margin}")
    print(f"Meets Thresholds: {'✅ Yes' if result.meets_thresholds else '❌ No'}")
    print(f"Matched Keywords: {', '.join(result.matched_keywords[:10])}")


def example_2_validation():
    """Example 2: Validation before classification"""
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Validation Before Classification")
    print("=" * 80)
    
    classifier = Athena875Classifier(config_path="config")
    
    # Invalid submission (title too short)
    invalid_submission = {
        'title': 'App',
        'description': 'Short description that is not long enough for validation'
    }
    
    print("\nValidating invalid submission...")
    is_valid, errors = classifier.validate_submission(invalid_submission)
    
    if not is_valid:
        print("❌ Validation failed:")
        for error in errors:
            print(f"   - {error}")
    
    # Valid submission
    valid_submission = {
        'title': 'LearnHub - Online Education Platform',
        'description': '''LearnHub is an innovative e-learning platform that connects
        students with expert instructors worldwide. Features include live video classes,
        interactive courses, certification programs, learning analytics, and AI-powered
        personalized learning paths. Serves universities, schools, and corporate training.''',
        'tags': ['education', 'elearning', 'courses'],
        'website_url': 'https://learnhub.edu'
    }
    
    print("\nValidating valid submission...")
    is_valid, errors = classifier.validate_submission(valid_submission)
    
    if is_valid:
        print("✅ Validation passed - proceeding with classification")
        result = classifier.classify_submission(valid_submission)
        print(f"Classified as: {classifier.get_industry_label(result.classified_industry)}")
        print(f"Confidence: {result.confidence_score}")


def example_3_low_confidence():
    """Example 3: Handling low-confidence classifications"""
    print("\n" + "=" * 80)
    print("EXAMPLE 3: Low-Confidence Classification Handling")
    print("=" * 80)
    
    classifier = Athena875Classifier(config_path="config")
    
    # Vague submission with minimal information
    vague_submission = {
        'title': 'GlobalTech Solutions',
        'description': '''We provide comprehensive business solutions to help
        companies succeed in the modern marketplace. Our team of experts works
        with clients to deliver results and improve operational efficiency.'''
    }
    
    result = classifier.classify_submission(vague_submission)
    
    print(f"\nSubmission: {vague_submission['title']}")
    print(f"Classified as: {classifier.get_industry_label(result.classified_industry)}")
    print(f"Confidence Score: {result.confidence_score}")
    print(f"Classification Score: {result.classification_score}")
    print(f"Margin: {result.margin}")
    print(f"Meets Thresholds: {'✅ Yes' if result.meets_thresholds else '❌ No'}")
    
    if not result.meets_thresholds:
        print("\n⚠️  LOW CONFIDENCE WARNING")
        print("This submission did not meet classification thresholds:")
        for warning in result.warnings:
            print(f"   - {warning}")
        print("\nRecommendation: Request more detailed description from submitter")


def example_4_all_scores():
    """Example 4: Viewing all industry scores"""
    print("\n" + "=" * 80)
    print("EXAMPLE 4: All Industry Scores")
    print("=" * 80)
    
    classifier = Athena875Classifier(config_path="config")
    
    submission = {
        'title': 'SmartFactory - Industrial IoT Platform',
        'description': '''SmartFactory provides IoT solutions for manufacturing
        facilities including production line automation, quality control systems,
        inventory management, predictive maintenance, and supply chain optimization.
        Designed for industrial operations and factory management.''',
        'tags': ['manufacturing', 'iot', 'automation', 'industry'],
        'website_url': 'https://smartfactory.industrial'
    }
    
    result = classifier.classify_submission(submission)
    
    print(f"\nSubmission: {submission['title']}")
    print(f"\nTop Classification: {classifier.get_industry_label(result.classified_industry)}")
    print(f"Confidence: {result.confidence_score}\n")
    
    print("All Industry Scores (sorted):")
    print("-" * 60)
    sorted_scores = sorted(
        result.all_industry_scores.items(),
        key=lambda x: x[1],
        reverse=True
    )
    
    for industry, score in sorted_scores:
        label = classifier.get_industry_label(industry)
        bar = "█" * int(score)
        print(f"  {label:30s} {score:5.1f}  {bar}")


def example_5_batch_processing():
    """Example 5: Batch processing multiple submissions"""
    print("\n" + "=" * 80)
    print("EXAMPLE 5: Batch Processing")
    print("=" * 80)
    
    classifier = Athena875Classifier(config_path="config")
    
    submissions = [
        {
            'submission_id': 'SUB-001',
            'title': 'ShopHub - E-commerce Platform',
            'description': 'Online shopping platform with cart, checkout, and inventory management',
            'tags': ['retail', 'ecommerce', 'shopping']
        },
        {
            'submission_id': 'SUB-002',
            'title': 'MediaStream - Content Platform',
            'description': 'Video streaming service with live broadcast and on-demand content',
            'tags': ['media', 'streaming', 'entertainment']
        },
        {
            'submission_id': 'SUB-003',
            'title': 'FleetTracker - Logistics System',
            'description': 'Transportation and fleet management with GPS tracking and route optimization',
            'tags': ['logistics', 'transportation', 'fleet']
        }
    ]
    
    print(f"\nProcessing {len(submissions)} submissions...\n")
    
    results = []
    for submission in submissions:
        try:
            result = classifier.classify_submission(submission)
            results.append({
                'submission_id': submission['submission_id'],
                'title': submission['title'],
                'industry': classifier.get_industry_label(result.classified_industry),
                'confidence': result.confidence_score,
                'meets_thresholds': result.meets_thresholds
            })
        except Exception as e:
            results.append({
                'submission_id': submission['submission_id'],
                'error': str(e)
            })
    
    print("Batch Results:")
    print("-" * 80)
    for r in results:
        if 'error' in r:
            print(f"❌ {r['submission_id']}: ERROR - {r['error']}")
        else:
            status = "✅" if r['meets_thresholds'] else "⚠️"
            print(f"{status} {r['submission_id']}: {r['title']}")
            print(f"   → {r['industry']} (confidence: {r['confidence']:.3f})")


def example_6_json_output():
    """Example 6: JSON output for API integration"""
    print("\n" + "=" * 80)
    print("EXAMPLE 6: JSON Output for API Integration")
    print("=" * 80)
    
    classifier = Athena875Classifier(config_path="config")
    
    submission = {
        'submission_id': 'SUB-2026-999',
        'title': 'PropManager - Real Estate Platform',
        'description': '''PropManager is a comprehensive property management solution
        for landlords, tenants, and real estate agents. Features include lease management,
        rent collection, maintenance tracking, property listings, and tenant screening.''',
        'tags': ['real estate', 'property management', 'rental'],
        'website_url': 'https://propmanager.properties'
    }
    
    result = classifier.classify_submission(submission)
    result_dict = classifier.format_result(result)
    
    # Add submission info to result
    output = {
        'submission_id': submission['submission_id'],
        'submission_title': submission['title'],
        'classification': result_dict
    }
    
    print("\nJSON Output:")
    print(json.dumps(output, indent=2))


def main():
    """Run all examples"""
    print("\n" + "#" * 80)
    print("#" + " " * 78 + "#")
    print("#" + "  ATHENA 875 Protocol - Classifier Usage Examples".center(78) + "#")
    print("#" + " " * 78 + "#")
    print("#" * 80)
    
    try:
        example_1_basic_classification()
        example_2_validation()
        example_3_low_confidence()
        example_4_all_scores()
        example_5_batch_processing()
        example_6_json_output()
        
        print("\n" + "=" * 80)
        print("All examples completed successfully!")
        print("=" * 80 + "\n")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
