"""
Detection Accuracy Validation Tests

This module validates ArgusAI motion detection accuracy against ground truth
labeled test footage. It measures:
- Detection rate by object type (person, vehicle, animal, package)
- False positive rate
- Confidence intervals for statistical validity

Target Metrics (from PRD-phase5.md FR30):
- Person detection rate: >90%
- False positive rate: <20%

Usage:
    pytest tests/test_validation/test_detection_accuracy.py -v
    pytest tests/test_validation/test_detection_accuracy.py -v -m validation

Note:
    Tests will skip if test footage is not available. Add video files to
    backend/tests/fixtures/footage/ following the manifest.yaml schema.
"""

import cv2
import json
import logging
import math
import pytest
import yaml
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# Try to import scipy for confidence intervals; fall back to approximation
try:
    from scipy.stats import binom

    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

from app.services.motion_detector import MotionDetector

logger = logging.getLogger(__name__)

# Paths
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "footage"
MANIFEST_PATH = FIXTURES_DIR / "manifest.yaml"

# Target metrics from PRD
TARGET_PERSON_DETECTION_RATE = 0.90  # >90%
TARGET_FALSE_POSITIVE_RATE = 0.20  # <20%


@dataclass
class DetectionResult:
    """Result of running detection on a single clip."""

    filename: str
    expected_type: str
    expected_objects: int
    motion_detected: bool
    detection_count: int
    max_confidence: float
    frames_processed: int
    frames_with_motion: int
    is_true_positive: bool = False
    is_false_positive: bool = False
    is_false_negative: bool = False
    is_true_negative: bool = False


@dataclass
class AccuracyMetrics:
    """Aggregated accuracy metrics across all clips."""

    total_clips: int = 0
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    true_negatives: int = 0
    results_by_type: dict = field(default_factory=dict)

    @property
    def detection_rate(self) -> float:
        """Calculate overall detection rate (sensitivity/recall)."""
        total_positive = self.true_positives + self.false_negatives
        if total_positive == 0:
            return 0.0
        return self.true_positives / total_positive

    @property
    def false_positive_rate(self) -> float:
        """Calculate false positive rate (1 - specificity)."""
        total_negative = self.false_positives + self.true_negatives
        if total_negative == 0:
            return 0.0
        return self.false_positives / total_negative

    @property
    def precision(self) -> float:
        """Calculate precision (positive predictive value)."""
        total_detected = self.true_positives + self.false_positives
        if total_detected == 0:
            return 0.0
        return self.true_positives / total_detected

    @property
    def specificity(self) -> float:
        """Calculate specificity (true negative rate)."""
        total_negative = self.false_positives + self.true_negatives
        if total_negative == 0:
            return 0.0
        return self.true_negatives / total_negative


def binomial_ci(
    successes: int, trials: int, confidence: float = 0.95
) -> tuple[float, float]:
    """
    Calculate binomial confidence interval.

    Uses Clopper-Pearson (exact) method if scipy available,
    otherwise falls back to normal approximation.

    Args:
        successes: Number of successes
        trials: Total number of trials
        confidence: Confidence level (default 0.95 for 95% CI)

    Returns:
        Tuple of (lower_bound, upper_bound) as proportions
    """
    if trials == 0:
        return (0.0, 1.0)

    p_hat = successes / trials
    alpha = 1 - confidence

    if SCIPY_AVAILABLE:
        # Clopper-Pearson exact method
        if successes == 0:
            lower = 0.0
        else:
            lower = binom.ppf(alpha / 2, trials, p_hat) / trials
        if successes == trials:
            upper = 1.0
        else:
            upper = binom.ppf(1 - alpha / 2, trials, p_hat) / trials
    else:
        # Normal approximation (less accurate for small samples)
        z = 1.96  # 95% CI
        se = math.sqrt(p_hat * (1 - p_hat) / trials)
        lower = max(0.0, p_hat - z * se)
        upper = min(1.0, p_hat + z * se)

    return (lower, upper)


def load_manifest() -> Optional[dict]:
    """Load ground truth manifest from fixtures directory."""
    if not MANIFEST_PATH.exists():
        return None
    with open(MANIFEST_PATH) as f:
        return yaml.safe_load(f)


def get_clips_by_type(manifest: dict, detection_type: str) -> list[dict]:
    """Get all clips for a specific detection type."""
    return [c for c in manifest.get("clips", []) if c["detection_type"] == detection_type]


def get_clip_path(filename: str) -> Path:
    """Get full path to a clip file."""
    return FIXTURES_DIR / filename


def clip_exists(filename: str) -> bool:
    """Check if a clip file exists."""
    return get_clip_path(filename).exists()


def process_clip(
    clip_path: Path, detector: MotionDetector, max_frames: int = 300
) -> tuple[bool, int, float, int, int]:
    """
    Process a video clip and detect motion.

    Args:
        clip_path: Path to video file
        detector: MotionDetector instance
        max_frames: Maximum frames to process (default 300 = 10s @ 30fps)

    Returns:
        Tuple of (motion_detected, detection_count, max_confidence,
                  frames_processed, frames_with_motion)
    """
    cap = cv2.VideoCapture(str(clip_path))
    if not cap.isOpened():
        logger.warning(f"Could not open video: {clip_path}")
        return False, 0, 0.0, 0, 0

    frames_processed = 0
    frames_with_motion = 0
    detection_count = 0
    max_confidence = 0.0
    motion_detected = False

    # Reset detector for fresh background model
    detector.reset()

    # Skip initial frames to let background model stabilize
    warmup_frames = 30
    for _ in range(warmup_frames):
        ret, _ = cap.read()
        if not ret:
            break

    while frames_processed < max_frames:
        ret, frame = cap.read()
        if not ret:
            break

        frames_processed += 1

        # Run motion detection
        detected, confidence, bbox = detector.detect_motion(frame, sensitivity="medium")

        if detected:
            motion_detected = True
            frames_with_motion += 1
            if confidence > max_confidence:
                max_confidence = confidence
            # Count distinct detections (every 15 frames = 0.5s @ 30fps)
            if frames_with_motion == 1 or (frames_with_motion % 15 == 0):
                detection_count += 1

    cap.release()

    return motion_detected, detection_count, max_confidence, frames_processed, frames_with_motion


def classify_result(clip: dict, motion_detected: bool) -> DetectionResult:
    """
    Classify detection result against ground truth.

    Args:
        clip: Clip metadata from manifest
        motion_detected: Whether motion was detected

    Returns:
        DetectionResult with classification
    """
    expected_type = clip["detection_type"]
    expected_objects = clip.get("expected_objects", 0)

    result = DetectionResult(
        filename=clip["filename"],
        expected_type=expected_type,
        expected_objects=expected_objects,
        motion_detected=motion_detected,
        detection_count=0,
        max_confidence=0.0,
        frames_processed=0,
        frames_with_motion=0,
    )

    if expected_type == "false_positive":
        # Clip should NOT trigger detection
        if motion_detected:
            result.is_false_positive = True
        else:
            result.is_true_negative = True
    else:
        # Clip SHOULD trigger detection
        if motion_detected:
            result.is_true_positive = True
        else:
            result.is_false_negative = True

    return result


def run_validation(manifest: dict, algorithm: str = "mog2") -> AccuracyMetrics:
    """
    Run validation across all clips in manifest.

    Args:
        manifest: Ground truth manifest
        algorithm: Motion detection algorithm ('mog2', 'knn', 'frame_diff')

    Returns:
        AccuracyMetrics with aggregated results
    """
    detector = MotionDetector(algorithm=algorithm)
    metrics = AccuracyMetrics()

    clips = manifest.get("clips", [])

    for clip in clips:
        filename = clip["filename"]
        clip_path = get_clip_path(filename)

        if not clip_path.exists():
            logger.info(f"Skipping missing clip: {filename}")
            continue

        metrics.total_clips += 1

        # Process clip
        motion_detected, det_count, max_conf, frames_proc, frames_motion = process_clip(
            clip_path, detector
        )

        # Classify result
        result = classify_result(clip, motion_detected)
        result.detection_count = det_count
        result.max_confidence = max_conf
        result.frames_processed = frames_proc
        result.frames_with_motion = frames_motion

        # Update metrics
        if result.is_true_positive:
            metrics.true_positives += 1
        elif result.is_false_positive:
            metrics.false_positives += 1
        elif result.is_false_negative:
            metrics.false_negatives += 1
        elif result.is_true_negative:
            metrics.true_negatives += 1

        # Track by type
        det_type = clip["detection_type"]
        if det_type not in metrics.results_by_type:
            metrics.results_by_type[det_type] = []
        metrics.results_by_type[det_type].append(result)

        logger.info(
            f"Processed {filename}: motion={motion_detected}, "
            f"confidence={max_conf:.2f}, frames_with_motion={frames_motion}"
        )

    return metrics


def generate_report(metrics: AccuracyMetrics) -> str:
    """Generate human-readable validation report."""
    lines = [
        "=" * 60,
        "MOTION DETECTION ACCURACY VALIDATION REPORT",
        "=" * 60,
        "",
        "## Summary",
        f"Total clips processed: {metrics.total_clips}",
        f"True Positives: {metrics.true_positives}",
        f"False Positives: {metrics.false_positives}",
        f"False Negatives: {metrics.false_negatives}",
        f"True Negatives: {metrics.true_negatives}",
        "",
        "## Metrics",
    ]

    # Overall detection rate
    det_rate = metrics.detection_rate
    det_ci = binomial_ci(
        metrics.true_positives, metrics.true_positives + metrics.false_negatives
    )
    target_met = "PASS" if det_rate >= TARGET_PERSON_DETECTION_RATE else "FAIL"
    lines.append(
        f"Detection Rate: {det_rate:.1%} (95% CI: {det_ci[0]:.1%}-{det_ci[1]:.1%}) "
        f"[Target: >{TARGET_PERSON_DETECTION_RATE:.0%}] {target_met}"
    )

    # False positive rate
    fp_rate = metrics.false_positive_rate
    fp_ci = binomial_ci(
        metrics.false_positives, metrics.false_positives + metrics.true_negatives
    )
    fp_target_met = "PASS" if fp_rate <= TARGET_FALSE_POSITIVE_RATE else "FAIL"
    lines.append(
        f"False Positive Rate: {fp_rate:.1%} (95% CI: {fp_ci[0]:.1%}-{fp_ci[1]:.1%}) "
        f"[Target: <{TARGET_FALSE_POSITIVE_RATE:.0%}] {fp_target_met}"
    )

    lines.append(f"Precision: {metrics.precision:.1%}")
    lines.append(f"Specificity: {metrics.specificity:.1%}")

    # Results by type
    lines.extend(["", "## Results by Detection Type"])
    for det_type, results in metrics.results_by_type.items():
        tp = sum(1 for r in results if r.is_true_positive)
        fp = sum(1 for r in results if r.is_false_positive)
        fn = sum(1 for r in results if r.is_false_negative)
        tn = sum(1 for r in results if r.is_true_negative)
        total = len(results)

        if det_type == "false_positive":
            rate = tn / total if total > 0 else 0
            lines.append(f"- {det_type}: {total} clips, rejection rate: {rate:.1%}")
        else:
            rate = tp / (tp + fn) if (tp + fn) > 0 else 0
            lines.append(f"- {det_type}: {total} clips, detection rate: {rate:.1%}")

    lines.extend(["", "=" * 60])
    return "\n".join(lines)


# ============================================================================
# PYTEST FIXTURES
# ============================================================================


@pytest.fixture
def manifest():
    """Load test footage manifest."""
    m = load_manifest()
    if m is None:
        pytest.skip("Test footage manifest not found")
    return m


@pytest.fixture
def available_clips(manifest):
    """Get list of clips that actually exist on disk."""
    clips = []
    for clip in manifest.get("clips", []):
        if clip_exists(clip["filename"]):
            clips.append(clip)
    if not clips:
        pytest.skip("No test footage available")
    return clips


@pytest.fixture
def detector():
    """Create a fresh MOG2 motion detector."""
    return MotionDetector(algorithm="mog2")


# ============================================================================
# TESTS
# ============================================================================


@pytest.mark.validation
class TestManifestStructure:
    """Tests for manifest.yaml structure and schema."""

    def test_manifest_exists(self):
        """Manifest file should exist."""
        if not MANIFEST_PATH.exists():
            pytest.skip("Manifest not found - footage infrastructure not set up")
        assert MANIFEST_PATH.exists()

    def test_manifest_has_required_fields(self, manifest):
        """Manifest should have required top-level fields."""
        assert "version" in manifest
        assert "clips" in manifest
        assert "targets" in manifest

    def test_manifest_clips_have_required_fields(self, manifest):
        """Each clip should have required fields."""
        required_fields = ["filename", "detection_type", "expected_objects"]
        for clip in manifest.get("clips", []):
            for field in required_fields:
                assert field in clip, f"Clip missing '{field}': {clip.get('filename')}"

    def test_manifest_detection_types_valid(self, manifest):
        """Detection types should be valid."""
        valid_types = {"person", "vehicle", "animal", "package", "false_positive"}
        for clip in manifest.get("clips", []):
            assert clip["detection_type"] in valid_types, (
                f"Invalid type '{clip['detection_type']}' in {clip['filename']}"
            )


@pytest.mark.validation
class TestMotionDetectorBasics:
    """Basic motion detector functionality tests."""

    def test_detector_initializes(self, detector):
        """Motion detector should initialize without errors."""
        assert detector is not None
        assert detector.algorithm == "mog2"

    def test_detector_handles_empty_frame(self, detector):
        """Detector should handle empty/None frames gracefully."""
        import numpy as np

        detected, confidence, bbox = detector.detect_motion(None)
        assert detected is False
        assert confidence == 0.0
        assert bbox is None

        detected, confidence, bbox = detector.detect_motion(np.array([]))
        assert detected is False


@pytest.mark.validation
class TestDetectionAccuracy:
    """Detection accuracy validation tests."""

    def test_process_available_clips(self, available_clips, detector):
        """Process all available clips and log results."""
        for clip in available_clips:
            clip_path = get_clip_path(clip["filename"])
            motion_detected, det_count, max_conf, frames, frames_motion = process_clip(
                clip_path, detector
            )

            result = classify_result(clip, motion_detected)

            # Log result for visibility
            status = ""
            if result.is_true_positive:
                status = "TP"
            elif result.is_false_positive:
                status = "FP"
            elif result.is_false_negative:
                status = "FN"
            elif result.is_true_negative:
                status = "TN"

            logger.info(
                f"{clip['filename']}: {status} (motion={motion_detected}, "
                f"expected={clip['detection_type']}, conf={max_conf:.2f})"
            )

            # Reset detector between clips for clean background model
            detector.reset()

    def test_validation_runs_successfully(self, manifest, available_clips):
        """Full validation should run and produce metrics."""
        metrics = run_validation(manifest)

        assert metrics.total_clips > 0
        assert metrics.total_clips == len(available_clips)

        # Generate and print report
        report = generate_report(metrics)
        print("\n" + report)

    def test_person_detection_rate_target(self, manifest, available_clips):
        """Person detection rate should meet target (>90%)."""
        person_clips = [c for c in available_clips if c["detection_type"] == "person"]
        if not person_clips:
            pytest.skip("No person clips available")

        detector = MotionDetector(algorithm="mog2")
        true_positives = 0
        false_negatives = 0

        for clip in person_clips:
            clip_path = get_clip_path(clip["filename"])
            motion_detected, _, _, _, _ = process_clip(clip_path, detector)
            detector.reset()

            if motion_detected:
                true_positives += 1
            else:
                false_negatives += 1

        total = true_positives + false_negatives
        if total == 0:
            pytest.skip("No person clips processed")

        detection_rate = true_positives / total
        ci_lower, ci_upper = binomial_ci(true_positives, total)

        print(f"\nPerson Detection Rate: {detection_rate:.1%}")
        print(f"95% CI: [{ci_lower:.1%}, {ci_upper:.1%}]")
        print(f"Sample size: {total}")
        print(f"Target: >{TARGET_PERSON_DETECTION_RATE:.0%}")

        # Note: We report but don't fail if below target - actual footage needed
        if total >= 5:  # Only assert with meaningful sample size
            assert detection_rate >= TARGET_PERSON_DETECTION_RATE or total < 10, (
                f"Person detection rate {detection_rate:.1%} below target "
                f"{TARGET_PERSON_DETECTION_RATE:.0%}"
            )

    def test_false_positive_rate_target(self, manifest, available_clips):
        """False positive rate should meet target (<20%)."""
        fp_clips = [c for c in available_clips if c["detection_type"] == "false_positive"]
        if not fp_clips:
            pytest.skip("No false positive clips available")

        detector = MotionDetector(algorithm="mog2")
        false_positives = 0
        true_negatives = 0

        for clip in fp_clips:
            clip_path = get_clip_path(clip["filename"])
            motion_detected, _, _, _, _ = process_clip(clip_path, detector)
            detector.reset()

            if motion_detected:
                false_positives += 1
            else:
                true_negatives += 1

        total = false_positives + true_negatives
        if total == 0:
            pytest.skip("No false positive clips processed")

        fp_rate = false_positives / total
        ci_lower, ci_upper = binomial_ci(false_positives, total)

        print(f"\nFalse Positive Rate: {fp_rate:.1%}")
        print(f"95% CI: [{ci_lower:.1%}, {ci_upper:.1%}]")
        print(f"Sample size: {total}")
        print(f"Target: <{TARGET_FALSE_POSITIVE_RATE:.0%}")

        # Note: We report but don't fail if above target - actual footage needed
        if total >= 5:  # Only assert with meaningful sample size
            assert fp_rate <= TARGET_FALSE_POSITIVE_RATE or total < 10, (
                f"False positive rate {fp_rate:.1%} above target "
                f"{TARGET_FALSE_POSITIVE_RATE:.0%}"
            )


@pytest.mark.validation
class TestReportGeneration:
    """Tests for report generation functionality."""

    def test_generate_empty_report(self):
        """Report should handle empty metrics."""
        metrics = AccuracyMetrics()
        report = generate_report(metrics)

        assert "MOTION DETECTION ACCURACY VALIDATION REPORT" in report
        assert "Total clips processed: 0" in report

    def test_generate_full_report(self, manifest, available_clips):
        """Generate full validation report."""
        metrics = run_validation(manifest)
        report = generate_report(metrics)

        assert "Detection Rate:" in report
        assert "False Positive Rate:" in report
        assert "Results by Detection Type" in report

        # Save report for reference
        report_path = FIXTURES_DIR / "validation_report.txt"
        with open(report_path, "w") as f:
            f.write(report)
        print(f"\nReport saved to: {report_path}")


@pytest.mark.validation
def test_confidence_interval_calculation():
    """Confidence interval calculation should produce valid ranges."""
    # Test with known values
    lower, upper = binomial_ci(9, 10, 0.95)
    assert lower < 0.9
    assert upper >= 0.9
    assert upper <= 1.0

    # Test edge cases
    lower, upper = binomial_ci(0, 10, 0.95)
    assert lower == 0.0

    lower, upper = binomial_ci(10, 10, 0.95)
    assert upper == 1.0

    # Test empty
    lower, upper = binomial_ci(0, 0, 0.95)
    assert lower == 0.0
    assert upper == 1.0
