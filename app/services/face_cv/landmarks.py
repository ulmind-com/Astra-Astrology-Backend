"""Canonical 478-point MediaPipe Face Landmarker topology and index constants.

Reference: Google Edge AI / MediaPipe Face Mesh canonical model
Every index in this file corresponds directly to the official 478-point mesh
and is thoroughly documented for geometric facial measurements.
"""

from typing import Final


class LandmarkIndex:
    """Documented landmark indices from the canonical 478-point face mesh."""

    # Midline & Vertical Frame
    FOREHEAD_TOP: Final[int] = 10         # Trichion / upper forehead boundary
    CHIN_BOTTOM: Final[int] = 152         # Gnathion / lower chin edge
    GLABELLA: Final[int] = 9              # Point between eyebrows
    NOSE_BRIDGE_TOP: Final[int] = 168     # Nasion / bridge origin
    NOSE_TIP: Final[int] = 1              # Pronasale / nasal tip
    NOSE_BASE: Final[int] = 2             # Subnasale / junction of columella and lip

    # Cheeks & Jaw Width (Horizontal Frame)
    CHEEK_RIGHT: Final[int] = 234         # Right zygomatic arch (subject's right)
    CHEEK_LEFT: Final[int] = 454          # Left zygomatic arch (subject's left)
    JAW_RIGHT: Final[int] = 172           # Right gonion / jaw angle
    JAW_LEFT: Final[int] = 397            # Left gonion / jaw angle
    BROW_RIDGE_RIGHT: Final[int] = 103    # Right lateral forehead boundary
    BROW_RIDGE_LEFT: Final[int] = 332     # Left lateral forehead boundary
    CHEEK_LINE_RIGHT: Final[int] = 215    # Right cheek at mouth height
    CHEEK_LINE_LEFT: Final[int] = 435     # Left cheek at mouth height

    # Right Eye (Subject's right, viewer's left in unmirrored frame)
    R_EYE_OUTER: Final[int] = 33          # Right lateral canthus
    R_EYE_INNER: Final[int] = 133         # Right medial canthus
    R_EYE_TOP: Final[int] = 159           # Right superior eyelid margin
    R_EYE_BOTTOM: Final[int] = 145        # Right inferior eyelid margin
    R_PUPIL: Final[int] = 468             # Right iris / pupil center (available in 478 mesh)

    # Left Eye (Subject's left, viewer's right)
    L_EYE_INNER: Final[int] = 362         # Left medial canthus
    L_EYE_OUTER: Final[int] = 263         # Left lateral canthus
    L_EYE_TOP: Final[int] = 386           # Left superior eyelid margin
    L_EYE_BOTTOM: Final[int] = 374        # Left inferior eyelid margin
    L_PUPIL: Final[int] = 473             # Left iris / pupil center

    # Right Eyebrow
    R_BROW_INNER: Final[int] = 55         # Right medial eyebrow
    R_BROW_PEAK: Final[int] = 105         # Right superior arch peak
    R_BROW_PEAK_LOWER: Final[int] = 52    # Right inferior arch peak margin
    R_BROW_OUTER: Final[int] = 46         # Right lateral eyebrow tail

    # Left Eyebrow
    L_BROW_INNER: Final[int] = 285        # Left medial eyebrow
    L_BROW_PEAK: Final[int] = 334         # Left superior arch peak
    L_BROW_PEAK_LOWER: Final[int] = 282   # Left inferior arch peak margin
    L_BROW_OUTER: Final[int] = 276        # Left lateral eyebrow tail

    # Nose Details
    NOSE_RIGHT_WING: Final[int] = 49      # Right alar crest
    NOSE_LEFT_WING: Final[int] = 279      # Left alar crest
    NOSTRIL_RIGHT: Final[int] = 98        # Right nostril border
    NOSTRIL_LEFT: Final[int] = 327        # Left nostril border

    # Lips & Mouth
    MOUTH_CORNER_RIGHT: Final[int] = 61   # Right oral commissure
    MOUTH_CORNER_LEFT: Final[int] = 291   # Left oral commissure
    LIP_UPPER_TOP: Final[int] = 0         # Labrale superius (upper vermilion border)
    LIP_LOWER_BOTTOM: Final[int] = 17     # Labrale inferius (lower vermilion border)
    LIP_INNER_TOP: Final[int] = 13        # Upper stomion (inner mouth opening)
    LIP_INNER_BOTTOM: Final[int] = 14     # Lower stomion (inner mouth opening)


# Canonical face oval contour indices for drawing and bounding box calculation
FACE_OVAL_INDICES = [
    10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288,
    397, 365, 379, 378, 400, 377, 152, 148, 176, 149, 150, 136,
    172, 58, 132, 93, 234, 127, 162, 21, 54, 103, 67, 109, 10
]

# Eyebrow contours
RIGHT_EYEBROW_INDICES = [70, 63, 105, 66, 107, 55, 65, 52, 53, 46]
LEFT_EYEBROW_INDICES = [336, 296, 334, 293, 300, 285, 295, 282, 283, 276]

# Eye contours
RIGHT_EYE_INDICES = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246, 33]
LEFT_EYE_INDICES = [263, 249, 390, 373, 374, 380, 381, 382, 362, 398, 384, 385, 386, 387, 388, 466, 263]

# Lips outer contour
LIPS_OUTER_INDICES = [61, 146, 91, 181, 84, 17, 314, 405, 321, 375, 291, 308, 324, 318, 402, 317, 14, 87, 178, 88, 95, 78, 61]

# Nose contours
NOSE_INDICES = [168, 6, 197, 195, 5, 4, 1, 19, 94, 2]

# Standard 3D anthropometric face model coordinates (in millimetres) for solvePnP head pose estimation
# Order matches: [Nose tip, Chin, Right eye corner, Left eye corner, Right mouth corner, Left mouth corner]
CANONICAL_3D_FACE_MODEL = [
    [0.0, 0.0, 0.0],          # Nose tip (index 1)
    [0.0, -330.0, -65.0],     # Chin (index 152)
    [-225.0, 170.0, -135.0],   # Right eye outer corner (index 33)
    [225.0, 170.0, -135.0],    # Left eye outer corner (index 263)
    [-150.0, -150.0, -125.0],  # Right mouth corner (index 61)
    [150.0, -150.0, -125.0],   # Left mouth corner (index 291)
]

HEAD_POSE_LANDMARK_INDICES = [
    LandmarkIndex.NOSE_TIP,
    LandmarkIndex.CHIN_BOTTOM,
    LandmarkIndex.R_EYE_OUTER,
    LandmarkIndex.L_EYE_OUTER,
    LandmarkIndex.MOUTH_CORNER_RIGHT,
    LandmarkIndex.MOUTH_CORNER_LEFT,
]
