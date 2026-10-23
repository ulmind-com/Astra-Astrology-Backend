r"""Named indices into MediaPipe's 21-point hand landmark set.

MediaPipe returns a bare list, so every access by raw index is a chance to pick the
wrong joint. Naming them once means the measurement code reads as anatomy rather
than as arithmetic, and a mistake shows up as a wrong name instead of a plausible
wrong number.

Layout, as MediaPipe orders them:

      8   12  16          8  = index tip        12 = middle tip
      |   |   |   20      16 = ring tip         20 = pinky tip
      7   11  15  |
      |   |   |   19      Each finger runs MCP -> PIP -> DIP -> TIP,
      6   10  14  18      base to fingertip.
       \  |   |  /
    4   5  9  13 17       5, 9, 13, 17 are the knuckles across the palm.
     \   \ | | /
      3    \|//           The thumb has one joint fewer, so its chain is
       \    |             CMC(1) -> MCP(2) -> IP(3) -> TIP(4).
        2   |
         \  |
          1 |
           \|
            0             wrist
"""

from __future__ import annotations

from typing import Final

WRIST: Final = 0

THUMB_CMC: Final = 1
THUMB_MCP: Final = 2
THUMB_IP: Final = 3
THUMB_TIP: Final = 4

INDEX_MCP: Final = 5
INDEX_PIP: Final = 6
INDEX_DIP: Final = 7
INDEX_TIP: Final = 8

MIDDLE_MCP: Final = 9
MIDDLE_PIP: Final = 10
MIDDLE_DIP: Final = 11
MIDDLE_TIP: Final = 12

RING_MCP: Final = 13
RING_PIP: Final = 14
RING_DIP: Final = 15
RING_TIP: Final = 16

PINKY_MCP: Final = 17
PINKY_PIP: Final = 18
PINKY_DIP: Final = 19
PINKY_TIP: Final = 20

# Classical names, which is how the client's documents refer to them.
JUPITER_FINGER: Final = "index"
SATURN_FINGER: Final = "middle"
SUN_FINGER: Final = "ring"
MERCURY_FINGER: Final = "pinky"

#: Finger name -> (MCP, PIP, DIP, TIP). The thumb is kept separate because it has
#: three joints rather than four and its measurements differ in kind.
FINGER_CHAINS: Final[dict[str, tuple[int, int, int, int]]] = {
    "index": (INDEX_MCP, INDEX_PIP, INDEX_DIP, INDEX_TIP),
    "middle": (MIDDLE_MCP, MIDDLE_PIP, MIDDLE_DIP, MIDDLE_TIP),
    "ring": (RING_MCP, RING_PIP, RING_DIP, RING_TIP),
    "pinky": (PINKY_MCP, PINKY_PIP, PINKY_DIP, PINKY_TIP),
}

THUMB_CHAIN: Final[tuple[int, int, int, int]] = (
    THUMB_CMC,
    THUMB_MCP,
    THUMB_IP,
    THUMB_TIP,
)

#: Classical name for each finger, used when a rule is phrased that way.
FINGER_CLASSICAL: Final[dict[str, str]] = {
    "index": "Jupiter",
    "middle": "Saturn",
    "ring": "Sun",
    "pinky": "Mercury",
}

#: The knuckle row, left to right across the palm.
KNUCKLES: Final[tuple[int, int, int, int]] = (
    INDEX_MCP,
    MIDDLE_MCP,
    RING_MCP,
    PINKY_MCP,
)

#: Boundary of the palm proper, excluding the fingers. Used to build the region
#: the crease tracing runs inside.
PALM_BOUNDARY: Final[tuple[int, ...]] = (
    WRIST,
    THUMB_CMC,
    THUMB_MCP,
    INDEX_MCP,
    MIDDLE_MCP,
    RING_MCP,
    PINKY_MCP,
)

#: Skeleton for drawing the overlay.
HAND_CONNECTIONS: Final[tuple[tuple[int, int], ...]] = (
    (WRIST, THUMB_CMC), (THUMB_CMC, THUMB_MCP), (THUMB_MCP, THUMB_IP), (THUMB_IP, THUMB_TIP),
    (WRIST, INDEX_MCP), (INDEX_MCP, INDEX_PIP), (INDEX_PIP, INDEX_DIP), (INDEX_DIP, INDEX_TIP),
    (INDEX_MCP, MIDDLE_MCP), (MIDDLE_MCP, MIDDLE_PIP), (MIDDLE_PIP, MIDDLE_DIP), (MIDDLE_DIP, MIDDLE_TIP),
    (MIDDLE_MCP, RING_MCP), (RING_MCP, RING_PIP), (RING_PIP, RING_DIP), (RING_DIP, RING_TIP),
    (RING_MCP, PINKY_MCP), (PINKY_MCP, PINKY_PIP), (PINKY_PIP, PINKY_DIP), (PINKY_DIP, PINKY_TIP),
    (WRIST, PINKY_MCP),
)
