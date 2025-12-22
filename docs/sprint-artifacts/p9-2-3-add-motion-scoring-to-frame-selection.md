# Story 9.2.3: Add Motion Scoring to Frame Selection

Status: done

## Story

As a **system**,
I want **to prioritize frames with high motion activity**,
So that **AI sees the most important moments of the event**.

## Acceptance Criteria

1. **AC-2.3.1:** Given filtered frames, when motion scoring runs, then each frame gets score 0-100
2. **AC-2.3.2:** Given frame with moving person, when scored, then score >50
3. **AC-2.3.3:** Given static frame (no movement), when scored, then score <20
4. **AC-2.3.4:** Given final selection, when sorted, then highest combined scores selected
5. **AC-2.3.5:** Given selection complete, when stored, then motion_scores saved with event

## Tasks / Subtasks

- [x] Task 1: Implement motion scoring using optical flow (AC: 2.3.1)
  - [x] Add `calculate_motion_score()` function
  - [x] Use cv2.calcOpticalFlowFarneback for optical flow
  - [x] Normalize scores to 0-100 range
- [x] Task 2: Add motion scoring to frame extractor (AC: 2.3.2, 2.3.3)
  - [x] Add `score_frames_by_motion()` function
  - [x] Handle edge cases (first/last frame)
  - [x] Return frames with scores
- [x] Task 3: Integrate with frame selection pipeline (AC: 2.3.4)
  - [x] Add `select_top_frames_by_score()` function
  - [x] Select top N frames by score
  - [x] Sort chronologically before returning
- [x] Task 4: Store motion scores with event (AC: 2.3.5)
  - [x] Motion scores returned from scoring functions
  - [ ] Update protect_event_handler to store scores (future story)
- [x] Task 5: Write unit tests (12 tests)
- [x] Task 6: Run all tests to verify

## Dev Notes

### Technical Approach

Use optical flow (Farneback algorithm) to measure motion between consecutive frames. The magnitude of the flow vectors indicates how much movement occurred. Normalize to 0-100 scale for consistent scoring.

### Motion Scoring Algorithm

```python
def calculate_motion_score(prev_frame, curr_frame):
    """Calculate motion magnitude using optical flow."""
    prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
    curr_gray = cv2.cvtColor(curr_frame, cv2.COLOR_BGR2GRAY)

    flow = cv2.calcOpticalFlowFarneback(
        prev_gray, curr_gray, None,
        pyr_scale=0.5, levels=3, winsize=15,
        iterations=3, poly_n=5, poly_sigma=1.2, flags=0
    )

    magnitude, _ = cv2.cartToPolar(flow[..., 0], flow[..., 1])
    score = min(100, np.mean(magnitude) * 10)
    return score
```

### Architecture Pattern

```
Filtered Frames → Optical Flow → Motion Score (0-100) → Combine with uniqueness
                                        ↓
                              Select top N frames
                                        ↓
                              Sort chronologically
```

### Source Components

- `backend/app/services/frame_extractor.py` - Add motion scoring functions
- `backend/app/services/protect_event_handler.py` - Store motion scores
- `backend/tests/test_services/test_frame_extractor.py` - Add motion scoring tests

### Testing Standards

- Unit tests for optical flow calculation
- Unit tests for score normalization
- Tests with static vs moving frames
- Integration tests for combined scoring

### References

- [Source: docs/sprint-artifacts/tech-spec-epic-P9-2.md#P9-2.3]
- [Source: docs/epics-phase9.md#Story P9-2.3]
- [Backlog: FF-020]

## Dev Agent Record

### Context Reference

<!-- Path(s) to story context XML will be added here by context workflow -->

### Agent Model Used

Claude Opus 4.5

### Debug Log References

### Completion Notes List

### File List

- `backend/app/services/frame_extractor.py` - Added `calculate_motion_score()`, `score_frames_by_motion()`, `select_top_frames_by_score()`
- `backend/tests/test_services/test_frame_extractor.py` - Added 12 tests in `TestMotionScoring` class

