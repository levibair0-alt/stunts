# SmartBoot Healthcare IP Package Template

## Purpose

Provide a structured ATHENA 875 protocol template for the SmartBoot Healthcare/MedTech IP package, including core metadata and the embedded bill of materials.

## Dependencies

- None for template use.
- Optional: ATHENA 875 classifier for validation.

## Environment

- Data-only template. Compatible with ATHENA 875 metadata schema.

## Usage

- Populate required submission fields using `smartboot_submission.json` as the base.
- Update BOM entries when hardware or firmware revisions ship.
- Ensure handshake verification is enforced before classifier runs.

## Tests

- Validate classification with `smartboot_classifier_test.md` (expected Healthcare/MedTech industry).

## Overview

SmartBoot is a clinical gait analytics platform combining sensorized smart footwear, embedded firmware, and cloud analytics for patient mobility monitoring. The package is designed for hospitals, rehabilitation clinics, and MedTech research teams, with HL7/FHIR integration for EHR workflows.

## Handshake Verification

ATHENA 875 handshake verification must be enabled. Use verification code `ATHENA-875-VERIFIED` in classifier configuration before processing this submission.

## Key Metadata

- **Package ID**: SB-HC-IP-2026
- **Industry Focus**: Healthcare / MedTech
- **Primary Use Cases**: Patient monitoring, gait anomaly detection, fall-risk scoring, rehabilitation tracking
- **Compliance**: HIPAA-ready workflows, de-identified analytics pipeline

## Embedded Bill of Materials (BOM)

| Component ID | Component Name | Version | Description | Supplier | License | Criticality | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| SB-HW-001 | SmartBoot Sensor Module | 2.3 | Foot pressure sensor array for gait analytics | SmartBoot Labs | Proprietary | High | Calibrated for clinical gait baselining |
| SB-FW-002 | Embedded Firmware | 1.8.5 | MCU firmware for sensor fusion and OTA updates | SmartBoot Labs | Proprietary | High | Includes encrypted bootloader |
| SB-SW-003 | Cloud Analytics Engine | 4.1.0 | ML analytics service for patient mobility trends | SmartBoot Labs | Apache-2.0 | Medium | Supports multi-tenant clinic dashboards |
| SB-ALG-004 | Gait Classification Model | 2026.02 | Model for anomaly detection and fall risk scoring | SmartBoot Labs | Proprietary | High | Validated on de-identified clinical dataset |
| SB-DATA-005 | Reference Dataset | 2026Q1 | De-identified gait dataset from partner clinics | Partner Clinics | CC-BY-4.0 | Medium | IRB-reviewed data collection |
| SB-API-006 | Integration API | 1.2 | HL7/FHIR bridge for EHR integration | SmartBoot Labs | MIT | Medium | Supports SMART on FHIR workflow |
| SB-UI-007 | Clinician Dashboard | 3.5 | Web UI for clinician review and alerts | SmartBoot Labs | MIT | Low | Accessible WCAG 2.1 AA |
| SB-HW-008 | Charging Dock | 1.1 | Charging station and sync hub | SmartBoot Labs | Proprietary | Low | Ships with medical-grade power supply |
| SB-COM-009 | Secure Comms Stack | 2.0 | TLS stack for device-to-cloud transport | OpenSSL | Apache-2.0 | High | FIPS-aligned configuration profile |

## Submission Notes

- Ensure clinical keywords (patient, clinical, gait, rehabilitation) remain in the description to maintain Healthcare/MedTech classification confidence.
- Keep submission metadata aligned to `templates/submission_schema.yaml`.
