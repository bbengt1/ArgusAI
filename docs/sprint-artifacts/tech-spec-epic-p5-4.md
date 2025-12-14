# Epic Technical Specification: Quality & Performance Validation

Date: 2025-12-14
Author: Brent
Epic ID: P5-4
Status: Draft

---

## Overview

Epic P5-4 establishes performance baselines and validates detection accuracy for ArgusAI. This epic creates documentation of actual resource usage (CPU, memory) under various camera configurations, collects real-world test footage for detection validation, and measures motion detection accuracy against defined targets.

The goal is to provide users and developers with concrete performance expectations and validate that ArgusAI's AI-powered detection meets quality targets (>90% person detection, <20% false positives).

**PRD Reference:** docs/PRD-phase5.md (FR27-FR30)
**Backlog Items:** TD-003, TD-004

## Objectives and Scope

**In Scope:**
- CPU usage measurement for 1, 2, 4 cameras at various FPS (5, 15, 30)
- Memory usage documentation under normal operation
- Reference hardware specification
- Performance baselines document (docs/performance-baselines.md)
- Real camera test footage collection and organization
- Ground truth labeling for test footage
- Motion detection accuracy measurement
- Person detection rate validation (target: >90%)
- False positive rate measurement (target: <20%)
- Detection accuracy documentation with methodology

**Out of Scope:**
- Automated performance regression testing in CI
- Load testing with concurrent users
- Network bandwidth optimization
- GPU utilization metrics (CPU-only focus)
- Automated ground truth labeling (manual process)

## System Architecture Alignment

**Architecture Reference:** docs/architecture/phase-5-additions.md

This epic is documentation and validation focused. It produces:
- `docs/performance-baselines.md` - Performance reference document
- Test footage in `tests/fixtures/videos/` (or external storage)
- Accuracy results documented in baselines doc

**Integration Points:**
- Uses existing `camera_service.py` for capture testing
- Uses existing `motion_detection_service.py` for accuracy testing
- Uses existing `ai_service.py` for description accuracy

## Detailed Design

### Services and Modules

| Component | Purpose | Output |
|-----------|---------|--------|
| Performance test script | Measure CPU/memory | Raw metrics |
| performance-baselines.md | Document results | Reference doc |
| Test footage collection | Validation data | Video files |
| Accuracy test script | Measure detection rates | Accuracy metrics |

### Data Models and Contracts

**Performance Baselines Document Structure:**
```markdown
# ArgusAI Performance Baselines

## Reference Hardware
- CPU: [model]
- RAM: [size]
- OS: [version]

## Camera Configuration Tests

### 1 Camera @ 15 FPS
- CPU Usage (avg): X%
- CPU Usage (peak): X%
- Memory Usage: X MB
- Notes: [observations]

### 2 Cameras @ 15 FPS
...

## Recommendations
- Recommended: X cameras at Y FPS on [hardware class]
```

**Test Footage Organization:**
```
tests/fixtures/videos/
├── person/
│   ├── day/
│   │   ├── person_walking_day_01.mp4
│   │   └── person_walking_day_02.mp4
│   └── night/
│       └── person_walking_night_01.mp4
├── vehicle/
│   ├── car_driveway_01.mp4
│   └── delivery_truck_01.mp4
├── animal/
│   ├── dog_yard_01.mp4
│   └── cat_porch_01.mp4
├── package/
│   └── delivery_package_01.mp4
├── false_positives/
│   ├── tree_movement_01.mp4
│   └── shadow_01.mp4
└── ground_truth.json
```

**Ground Truth Schema:**
```json
{
  "videos": [
    {
      "filename": "person_walking_day_01.mp4",
      "category": "person",
      "expected_detections": [
        {
          "type": "person",
          "start_frame": 30,
          "end_frame": 150,
          "confidence": "high"
        }
      ],
      "lighting": "day",
      "camera_angle": "front_door",
      "notes": "Clear visibility, single person"
    }
  ]
}
```

### APIs and Interfaces

N/A - This epic is documentation and validation focused.

### Workflows and Sequencing

**Performance Measurement Workflow:**
```
1. Set up reference hardware environment
2. Configure ArgusAI with 1 camera at 5 FPS
3. Run for 5 minutes, collect metrics:
   - CPU: top/htop or psutil
   - Memory: psutil or /proc/meminfo
4. Record results
5. Repeat for all configurations:
   - 1 camera: 5, 15, 30 FPS
   - 2 cameras: 5, 15, 30 FPS
   - 4 cameras: 5, 15, 30 FPS
6. Document in performance-baselines.md
7. Add recommendations based on results
```

**Detection Accuracy Workflow:**
```
1. Collect test footage (or use existing security footage)
2. Organize by category (person, vehicle, animal, package)
3. Create ground truth labels:
   - What should be detected
   - Frame ranges for detections
4. Run detection pipeline on each video
5. Compare detected vs expected:
   - True Positives: Correctly detected
   - False Positives: Incorrectly detected
   - False Negatives: Missed detections
6. Calculate metrics:
   - Detection Rate = TP / (TP + FN)
   - False Positive Rate = FP / Total Frames
7. Document results with methodology
```

## Non-Functional Requirements

### Performance (Targets to Validate)

| Metric | Target | Notes |
|--------|--------|-------|
| Person detection rate | >90% | Across varied footage |
| False positive rate | <20% | Motion triggers without objects |
| Test coverage | 4+ scenarios | Person, vehicle, animal, package |
| Day/night coverage | Both | Validate IR/low-light |

### Documentation Quality

- Clear methodology description
- Reproducible test procedures
- Hardware specifications included
- Confidence intervals for accuracy metrics

## Dependencies and Integrations

### Test Script Dependencies

| Package | Purpose |
|---------|---------|
| psutil | CPU/memory measurement |
| matplotlib | (Optional) Visualization of results |

### Test Footage Sources

- Personal security camera recordings (preferred)
- Public datasets (if needed): UCF Crime Dataset, VIRAT
- Synthetic test videos (last resort)

## Acceptance Criteria (Authoritative)

**Story P5-4.1: Document CPU/Memory Performance Baselines**
1. Performance test conducted on documented reference hardware
2. CPU usage measured for 1 camera at 5, 15, 30 FPS
3. CPU usage measured for 2 cameras at 15 FPS
4. CPU usage measured for 4 cameras at 15 FPS
5. Memory usage measured for each configuration
6. Results documented in docs/performance-baselines.md
7. Recommendations included for different hardware classes

**Story P5-4.2: Acquire and Organize Real Camera Test Footage**
1. Test footage includes person detection scenarios
2. Test footage includes vehicle detection scenarios
3. Test footage includes animal detection scenarios
4. Test footage includes package detection scenarios
5. Day and night/low-light footage included
6. Footage organized in structured directory
7. Ground truth JSON created with expected detections

**Story P5-4.3: Validate Motion Detection Accuracy Metrics**
1. Detection pipeline run on all test footage
2. Results compared against ground truth
3. Person detection rate calculated (target: >90%)
4. False positive rate calculated (target: <20%)
5. Results documented with methodology
6. Areas for improvement identified and noted
7. Confidence intervals or sample sizes documented

## Traceability Mapping

| AC | Spec Section | Component | Test Idea |
|----|--------------|-----------|-----------|
| P5-4.1-1 | Data Models | Reference hardware | Hardware doc verification |
| P5-4.1-2 | Workflows | Performance test | 1-cam measurements |
| P5-4.1-3 | Workflows | Performance test | 2-cam measurements |
| P5-4.1-4 | Workflows | Performance test | 4-cam measurements |
| P5-4.1-5 | Workflows | Memory measurement | Memory metric verification |
| P5-4.1-6 | Data Models | performance-baselines.md | Document existence |
| P5-4.1-7 | Data Models | Recommendations | Content verification |
| P5-4.2-1 | Data Models | Test footage | Person videos exist |
| P5-4.2-2 | Data Models | Test footage | Vehicle videos exist |
| P5-4.2-3 | Data Models | Test footage | Animal videos exist |
| P5-4.2-4 | Data Models | Test footage | Package videos exist |
| P5-4.2-5 | Data Models | Test footage | Day/night coverage |
| P5-4.2-6 | Data Models | Directory structure | Organization verification |
| P5-4.2-7 | Data Models | ground_truth.json | JSON schema validation |
| P5-4.3-1 | Workflows | Detection pipeline | All footage processed |
| P5-4.3-2 | Workflows | Comparison | Ground truth comparison |
| P5-4.3-3 | NFR | Detection rate | >90% person detection |
| P5-4.3-4 | NFR | FP rate | <20% false positive |
| P5-4.3-5 | Data Models | Results doc | Methodology documented |
| P5-4.3-6 | Data Models | Results doc | Improvements noted |
| P5-4.3-7 | Data Models | Results doc | Confidence intervals |

## Risks, Assumptions, Open Questions

**Risks:**
- **R1: Footage availability** - May be difficult to acquire diverse footage; use personal cameras
- **R2: Hardware variance** - Results only valid for tested hardware; document clearly
- **R3: Subjectivity** - Ground truth labeling has inherent subjectivity; use conservative labels

**Assumptions:**
- **A1:** Reference hardware is a typical development machine (8GB+ RAM, modern CPU)
- **A2:** Test footage can be acquired from personal security cameras or public datasets
- **A3:** Detection targets (>90%, <20%) are achievable with current AI providers
- **A4:** Manual ground truth labeling is acceptable (not automated)

**Open Questions:**
- **Q1:** Should test footage be committed to repo? → No, too large; store externally or .gitignore
- **Q2:** How many test videos per category? → Minimum 3-5 per category for statistical validity
- **Q3:** Include edge cases (partial visibility, etc.)? → Yes, note them in ground truth

## Test Strategy Summary

**Validation Tests:**
- Performance tests run manually on reference hardware
- Detection accuracy tests run manually with ground truth comparison
- Results reviewed for statistical validity

**Documentation Review:**
- Performance baselines document complete and clear
- Methodology reproducible by others
- Recommendations actionable

**No Automated Tests:**
- This epic produces documentation and validation data
- Automated performance regression could be future enhancement
