# SmartBoot Classifier Test Artifact

## Purpose

Validate that the ATHENA 875 classifier categorizes the SmartBoot submission as Healthcare/MedTech.

## Dependencies

- `athena-orchestrator` classifier (`agents/athena_875_classifier.py`).
- `smartboot_submission.json` for input payload.

## Environment

- Python 3.8+ with `pyyaml` installed.

## Usage

1. Confirm handshake verification is configured (`ATHENA-875-VERIFIED`).
2. Load `smartboot_submission.json` as the submission payload.
3. Run the classifier and compare results against the expected outputs below.

## Tests

### Expected Classification

- **Expected Industry**: Healthcare/MedTech
- **Expected Industry Key**: `healthcare`
- **Expected Industry ID**: 3
- **Minimum Expected Score**: 3
- **Handshake Required**: Yes (`ATHENA-875-VERIFIED`)

### Suggested Test Runner (Pseudo-Workflow)

```python
import json
from agents.athena_875_classifier import Athena875Classifier

with open(
    "docs/athena_875_protocol/smartboot_healthcare_ip_package/smartboot_submission.json",
    "r",
    encoding="utf-8"
) as handle:
    submission = json.load(handle)

classifier = Athena875Classifier(config_path="./config")
result = classifier.classify_submission(submission)

assert result.classified_industry == "healthcare"
assert result.meets_thresholds is True
```

## Handshake Verification Notes

If handshake verification fails, the classifier must refuse to run. Confirm the taxonomy includes `ATHENA-875-VERIFIED` before executing the test.
