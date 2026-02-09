# ATHENA 875 Protocol - Submission Classifier

## Overview

The ATHENA 875 Protocol-compliant submission classifier is a deterministic classification system for categorizing marketplace submissions into 10 industry categories. It uses configurable YAML taxonomy with keyword matching, weighted scoring, and confidence thresholds to ensure reliable classification results.

## Protocol Specification

- **Protocol Name**: ATHENA 875
- **Version**: 1.0.0
- **Compliance Date**: 2026-02-09
- **Classification Algorithm**: Deterministic keyword-based scoring
- **Handshake Verification**: Required

## Features

✅ **10-Industry Taxonomy**: Technology, Finance, Healthcare, Education, Retail, Manufacturing, Media, Real Estate, Transportation, Professional Services

✅ **Configurable YAML Configuration**: Easy-to-update taxonomy without code changes

✅ **Deterministic Scoring**: Consistent, reproducible classification results

✅ **Confidence Thresholds**: Configurable minimum score (default: 3) and margin (default: 1)

✅ **Handshake Verification**: Protocol compliance checks on initialization

✅ **Domain Bonus Scoring**: URL pattern matching for additional context

✅ **Comprehensive Logging**: Detailed classification metrics and matched keywords

## Architecture

```
athena-orchestrator/
├── agents/
│   └── athena_875_classifier.py    # Main classifier module
├── config/
│   └── athena_875_taxonomy.yaml    # Industry taxonomy configuration
├── templates/
│   └── submission_schema.yaml      # Submission format template
└── docs/
    └── ATHENA_875_CLASSIFIER.md    # This document
```

## Installation & Setup

### 1. Dependencies

The classifier requires Python 3.8+ and the following dependencies:

```bash
pip install pyyaml>=6.0.1
```

All dependencies are included in the main `requirements.txt`:

```bash
cd athena-orchestrator
pip install -r requirements.txt
```

### 2. Configuration

The classifier uses `config/athena_875_taxonomy.yaml` for industry definitions and scoring rules. This file includes:

- Protocol metadata and handshake verification
- 10 industry categories with primary/secondary keywords
- Scoring weights (primary: 2.0, secondary: 1.0, domain bonus: 1.5)
- Domain patterns for URL-based bonus scoring
- Classification thresholds (min_score: 3, min_margin: 1)

**No additional configuration required** - defaults work out of the box.

## Usage

### Basic Classification

```python
from agents.athena_875_classifier import Athena875Classifier

# Initialize classifier (config_path defaults to "./config")
classifier = Athena875Classifier(config_path="./config")

# Prepare submission data
submission = {
    'title': 'MediTrack - Patient Management Platform',
    'description': '''MediTrack is a comprehensive healthcare platform designed 
    for hospitals and clinics to manage patient records, appointments, and 
    medical histories. Features include HIPAA-compliant storage, telemedicine 
    integration, electronic health records (EHR), and real-time patient 
    monitoring dashboards.''',
    'tags': ['healthcare', 'patient management', 'telemedicine', 'EHR'],
    'website_url': 'https://meditrack.health'
}

# Classify
result = classifier.classify_submission(submission)

# Check results
if result.meets_thresholds:
    print(f"Industry: {classifier.get_industry_label(result.classified_industry)}")
    print(f"Confidence: {result.confidence_score}")
    print(f"Score: {result.classification_score}")
else:
    print("Classification confidence too low")
    print(f"Warnings: {result.warnings}")
```

### Validation Before Classification

```python
# Validate submission structure
is_valid, errors = classifier.validate_submission(submission)

if not is_valid:
    print(f"Validation errors: {errors}")
else:
    result = classifier.classify_submission(submission)
```

### Getting Formatted Output

```python
# Get dictionary output (JSON-serializable)
result_dict = classifier.format_result(result)

import json
print(json.dumps(result_dict, indent=2))
```

### Checking All Industry Scores

```python
result = classifier.classify_submission(submission)

print("All industry scores:")
for industry, score in sorted(result.all_industry_scores.items(), 
                              key=lambda x: x[1], reverse=True):
    label = classifier.get_industry_label(industry)
    print(f"  {label}: {score}")
```

## Submission Data Format

### Required Fields

- **title** (string, 5-200 chars): Short name/title of the submission
- **description** (string, 50-5000 chars): Detailed description

### Optional Fields

- **tags** (list of strings): User-provided keywords
- **website_url** (string): URL for domain bonus scoring
- **additional_context** (string): Extra context information
- **submission_id** (string): Unique identifier
- **submitter_info** (object): Submitter details

See `templates/submission_schema.yaml` for complete schema definition.

## Classification Result Structure

```python
@dataclass
class ClassificationResult:
    classified_industry: str          # Industry key (e.g., "healthcare")
    industry_id: int                  # Numeric ID (1-10)
    confidence_score: float           # Confidence metric (0.0-1.0)
    classification_score: float       # Raw score from keyword matching
    margin: float                     # Score difference: top - second
    meets_thresholds: bool            # True if meets min_score & min_margin
    all_industry_scores: Dict         # Scores for all 10 industries
    matched_keywords: List[str]       # Keywords that matched
    protocol_version: str             # "1.0.0"
    timestamp: str                    # ISO-8601 timestamp
    handshake_verified: bool          # Handshake status
    warnings: List[str]               # Any warnings or issues
```

## Scoring Algorithm

### 1. Keyword Matching

The classifier uses regex word-boundary matching to find keywords in the combined text (title + description + tags + context).

**Primary Keywords** (weight: 2.0):
- Core industry terms
- Direct industry indicators
- Specialized terminology

**Secondary Keywords** (weight: 1.0):
- Related terms
- Supporting concepts
- Adjacent terminology

### 2. Domain Bonus

If a `website_url` is provided, the classifier checks for industry-specific domain patterns:

- Technology: `.io`, `.dev`, `.tech`, `.ai`, `.app`
- Finance: `bank`, `pay`, `fin`, `capital`
- Healthcare: `health`, `med`, `care`, `clinic`
- [etc.]

**Domain bonus weight**: 1.5 points

### 3. Score Calculation

```
Industry Score = 
  (Primary Keyword Matches × 2.0) + 
  (Secondary Keyword Matches × 1.0) + 
  (Domain Match Bonus × 1.5)
```

### 4. Confidence Calculation

```
Confidence = (Score Strength × 0.6) + (Margin Ratio × 0.4)

Where:
- Score Strength = min(top_score / (total_possible × 0.3), 1.0)
- Margin Ratio = min((top_score - second_score) / top_score, 1.0)
```

### 5. Threshold Checks

Classification passes if **both** conditions are met:

- **min_score**: Top industry score ≥ 3 (configurable)
- **min_margin**: Score difference (top - second) ≥ 1 (configurable)

## Configuration

### Adjusting Thresholds

Edit `config/athena_875_taxonomy.yaml`:

```yaml
classification:
  min_score: 3          # Minimum classification score
  min_margin: 1         # Minimum margin between top two scores
  confidence_threshold: 0.65  # Minimum confidence for high-confidence flag
```

### Adding Keywords

Add keywords to industry definitions:

```yaml
industries:
  technology:
    keywords:
      primary:
        - software
        - technology
        - cloud
        # Add more here
      secondary:
        - app
        - system
        # Add more here
```

### Adjusting Weights

Modify scoring weights per industry:

```yaml
industries:
  technology:
    scoring:
      primary_weight: 2.0      # Weight for primary keywords
      secondary_weight: 1.0    # Weight for secondary keywords
      domain_bonus: 1.5        # Weight for domain pattern match
```

## Testing

### Run Built-in Tests

```bash
cd athena-orchestrator
python agents/athena_875_classifier.py
```

This runs three test cases:
1. High-confidence healthcare classification
2. High-confidence technology classification
3. Low-confidence ambiguous classification

### Test Output

```
================================================================================
ATHENA 875 Protocol - Classifier Test Suite
================================================================================
[ATHENA-875] Taxonomy loaded from config/athena_875_taxonomy.yaml
[ATHENA-875] Handshake verified: ATHENA-875-VERIFIED
[ATHENA-875] Classifier initialized
[ATHENA-875] Protocol: ATHENA 875 v1.0.0
[ATHENA-875] Thresholds - min_score: 3, min_margin: 1
[ATHENA-875] Industries loaded: 10

--------------------------------------------------------------------------------
TEST 1: Healthcare Submission
--------------------------------------------------------------------------------

Classified as: Healthcare & Medical
Industry ID: 3
Score: 18.0
Confidence: 0.897
Margin: 12.5
Meets Thresholds: True
Matched Keywords: healthcare, patient, medical, clinical, telemedicine
...
```

## Handshake Verification

The classifier implements mandatory handshake verification per ATHENA 875 protocol:

### Verification Checks

1. **Handshake Required Flag**: `protocol.handshake_required` must be `true`
2. **Verification Code**: Must match `ATHENA-875-VERIFIED`
3. **Protocol Name**: Must match `ATHENA 875`

### Failure Behavior

If handshake verification fails, the classifier raises `RuntimeError` and **refuses to initialize**:

```python
RuntimeError: ATHENA-875 HANDSHAKE FAILURE: Invalid verification code
Expected: ATHENA-875-VERIFIED
Received: [incorrect_code]
Classifier will refuse to operate.
```

This ensures protocol compliance and prevents operation with misconfigured taxonomy files.

## Error Handling

### Common Errors

**Missing Required Fields**:
```python
ValueError: ATHENA-875 ERROR: Missing required field 'title'
```

**Taxonomy Not Found**:
```python
RuntimeError: ATHENA-875 CRITICAL: Taxonomy file not found at config/athena_875_taxonomy.yaml
Classifier cannot operate without taxonomy configuration.
```

**Handshake Failure**:
```python
RuntimeError: ATHENA-875 HANDSHAKE FAILURE: handshake_required not set to true
Protocol compliance requires explicit handshake verification.
```

### Validation Errors

Use `validate_submission()` to catch errors before classification:

```python
is_valid, errors = classifier.validate_submission(submission)
# errors = ["Title must be at least 5 characters", ...]
```

## Integration Examples

### With Notion Database

```python
from notion.notion_client import NotionClient
from agents.athena_875_classifier import Athena875Classifier

notion = NotionClient()
classifier = Athena875Classifier()

# Get submissions from Notion
submissions = notion.query_database("submission_db_id")

for submission_page in submissions:
    # Extract data
    submission = {
        'title': submission_page['properties']['Title'],
        'description': submission_page['properties']['Description'],
        'website_url': submission_page['properties']['URL']
    }
    
    # Classify
    result = classifier.classify_submission(submission)
    
    # Update Notion page with classification
    notion.update_page(submission_page['id'], {
        'Industry': classifier.get_industry_label(result.classified_industry),
        'Confidence': result.confidence_score,
        'Classification Score': result.classification_score
    })
```

### REST API Endpoint

```python
from flask import Flask, request, jsonify
from agents.athena_875_classifier import Athena875Classifier

app = Flask(__name__)
classifier = Athena875Classifier()

@app.route('/classify', methods=['POST'])
def classify():
    submission = request.json
    
    # Validate
    is_valid, errors = classifier.validate_submission(submission)
    if not is_valid:
        return jsonify({'error': 'Validation failed', 'details': errors}), 400
    
    # Classify
    result = classifier.classify_submission(submission)
    
    return jsonify(classifier.format_result(result))

if __name__ == '__main__':
    app.run(port=5000)
```

### Batch Processing

```python
import json
from agents.athena_875_classifier import Athena875Classifier

classifier = Athena875Classifier()

# Load submissions
with open('submissions.json', 'r') as f:
    submissions = json.load(f)

results = []

for submission in submissions:
    try:
        result = classifier.classify_submission(submission)
        results.append({
            'submission_id': submission.get('submission_id'),
            'classification': classifier.format_result(result)
        })
    except Exception as e:
        results.append({
            'submission_id': submission.get('submission_id'),
            'error': str(e)
        })

# Save results
with open('classification_results.json', 'w') as f:
    json.dump(results, f, indent=2)
```

## Ledger-Style Change Summary

### Version 1.0.0 - 2026-02-09

**ADDITIONS**:
- ✅ Created ATHENA 875 Protocol classifier module (`agents/athena_875_classifier.py`)
- ✅ Created 10-industry taxonomy configuration (`config/athena_875_taxonomy.yaml`)
- ✅ Created submission schema template (`templates/submission_schema.yaml`)
- ✅ Implemented deterministic keyword-based scoring algorithm
- ✅ Implemented handshake verification system
- ✅ Implemented confidence calculation with thresholds
- ✅ Added domain bonus scoring for URL patterns
- ✅ Created comprehensive documentation (`docs/ATHENA_875_CLASSIFIER.md`)

**CONFIGURATION**:
- min_score: 3 (minimum classification score threshold)
- min_margin: 1 (minimum margin between top two scores)
- confidence_threshold: 0.65 (confidence metric threshold)
- primary_weight: 2.0 (primary keyword weight)
- secondary_weight: 1.0 (secondary keyword weight)
- domain_bonus: 1.5 (URL pattern match bonus)

**INDUSTRIES DEFINED**:
1. Technology & Software (id: 1)
2. Finance & Banking (id: 2)
3. Healthcare & Medical (id: 3)
4. Education & Training (id: 4)
5. Retail & E-commerce (id: 5)
6. Manufacturing & Industry (id: 6)
7. Media & Entertainment (id: 7)
8. Real Estate & Property (id: 8)
9. Transportation & Logistics (id: 9)
10. Professional Services (id: 10)

**TESTING**:
- ✅ Built-in test suite with 3 test cases
- ✅ Healthcare classification test (high confidence)
- ✅ Technology classification test (high confidence)
- ✅ Ambiguous classification test (low confidence detection)

## Risks & Mitigations

### Risk 1: Keyword Overlap Between Industries

**Risk**: Some keywords may be relevant to multiple industries, causing ambiguous classifications.

**Example**: "platform" could apply to Technology, Healthcare, or E-commerce.

**Mitigation**:
- Use `min_margin` threshold to detect close scores
- Require score separation of at least 1 point between top two industries
- Warn users when confidence is below threshold
- Allow manual review of low-confidence classifications

**Impact**: Low - margin threshold effectively flags ambiguous cases

---

### Risk 2: Evolving Industry Terminology

**Risk**: Industry keywords and terminology change over time, reducing classification accuracy.

**Example**: New buzzwords like "Web3", "quantum computing", or "metaverse" may not be in initial taxonomy.

**Mitigation**:
- Externalized YAML configuration for easy updates
- No code changes required to add/modify keywords
- Version tracking in taxonomy file
- Regular taxonomy reviews and updates

**Impact**: Low - YAML configuration enables rapid updates

---

### Risk 3: Domain Bonus Overweighting

**Risk**: URL patterns might overly influence classification if domain doesn't match actual business.

**Example**: A finance company using `.io` domain gets technology bonus.

**Mitigation**:
- Domain bonus weight (1.5) is lower than primary keywords (2.0)
- Requires significant keyword matches to reach threshold
- Domain bonus is only one factor in total score
- Can be adjusted per industry in taxonomy

**Impact**: Low - domain bonus is supplementary, not primary signal

---

### Risk 4: Insufficient Description Quality

**Risk**: Vague or minimal descriptions may result in low scores across all industries.

**Example**: "We provide business solutions" - too generic to classify.

**Mitigation**:
- Minimum description length requirement (50 characters)
- `min_score` threshold rejects low-quality classifications
- Validation checks before classification
- Clear warnings when thresholds not met
- Returns confidence metrics for downstream decision-making

**Impact**: Medium - addressed by validation and thresholds

---

### Risk 5: Single-Language Support (English)

**Risk**: Classifier currently only supports English keywords.

**Example**: Submissions in other languages will not match keywords.

**Mitigation** (Future):
- Add multi-language keyword lists to taxonomy
- Implement translation layer before classification
- Add language detection

**Current Impact**: High - non-English submissions will not classify
**Mitigation Status**: Documented limitation, future enhancement

---

### Risk 6: Handshake Verification Bypass

**Risk**: If handshake verification is disabled or bypassed, protocol compliance is compromised.

**Mitigation**:
- Handshake verification is mandatory and cannot be disabled
- Classifier refuses to initialize if verification fails
- Clear error messages explain compliance requirements
- Verification code must match exactly

**Impact**: None - verification is enforced at runtime

---

## Performance Considerations

**Time Complexity**: O(k × n × m)
- k = number of industries (10)
- n = number of keywords per industry (~30-50)
- m = length of submission text

**Typical Classification Time**: 5-20ms per submission

**Memory Usage**: ~1-2 MB (taxonomy + classifier state)

**Scalability**: Suitable for real-time API usage and batch processing

## Future Enhancements

- [ ] Multi-language support (Spanish, French, German, etc.)
- [ ] Machine learning confidence calibration
- [ ] Automatic keyword extraction from training data
- [ ] Industry co-occurrence patterns (e.g., "fintech" = finance + technology)
- [ ] Time-based keyword weighting (trending terms)
- [ ] Custom industry definitions via API
- [ ] A/B testing framework for taxonomy changes

## Support & Maintenance

### Updating the Taxonomy

1. Edit `config/athena_875_taxonomy.yaml`
2. Add/modify keywords in appropriate industry sections
3. Adjust weights if needed
4. Update protocol version if breaking changes
5. Test with representative submissions

### Monitoring Classification Quality

Track these metrics:
- % of submissions meeting thresholds
- Average confidence scores
- Distribution of industries
- Keyword match rates
- Low-confidence classification reviews

### Common Adjustments

**Increase Precision** (fewer false positives):
- Increase `min_score` threshold
- Increase `min_margin` threshold
- Add more specific primary keywords

**Increase Recall** (fewer rejections):
- Decrease `min_score` threshold
- Decrease `min_margin` threshold
- Add more secondary keywords

---

**Document Version**: 1.0.0  
**Last Updated**: 2026-02-09  
**Maintained By**: Athena Orchestrator Team
