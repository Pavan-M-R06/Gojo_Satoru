"""
PROJECT LIMITLESS: Cursed Energy AR Engine

Flow:
  1. Real World Mode — fullscreen webcam with hand tracking
  2. Cross right-hand fingers → Domain Expansion transition (with SFX)
  3. Infinity Void — cursed energy techniques (Blue, Red, Purple)

Techniques:
  - BLUE (Lapse)  — Left crossed fingers spawn, left hand control, left fist dismiss
  - RED (Reversal) — Hands-apart spawn, right hand control, right fist dismiss
  - PURPLE (Hollow) — Blue+Red collision, cinematic merge, right hand control
  - DOMAIN EXPANSION — Right crossed fingers destroys Purple (when active)

  - 'q' to quit
"""

import cv2
import numpy as np
import mediapipe as mp
import sys
import os
import time
import math
import random
import pygame


# ──────────────────────────────────────────────
# CONFIGURATION
# ──────────────────────────────────────────────
CANVAS_WIDTH = 1280
CANVAS_HEIGHT = 720

# PiP (Picture-in-Picture) Controller Window
PIP_WIDTH = 280
PIP_HEIGHT = 210
PIP_MARGIN = 15
PIP_BORDER_WIDTH = 2
PIP_BORDER_COLOR = (80, 80, 80)
PIP_OPACITY = 0.9

# Default PiP position (bottom-left corner)
PIP_X = PIP_MARGIN
PIP_Y = CANVAS_HEIGHT - PIP_HEIGHT - PIP_MARGIN

# Webcam settings
CAMERA_INDEX = 1       # External webcam
CAMERA_FALLBACK = 0    # Built-in webcam fallback
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480

# MediaPipe settings — tuned for robust detection
MAX_HANDS = 2
MODEL_COMPLEXITY = 1
MIN_DETECTION_CONFIDENCE = 0.5     # Lower for better detection in tricky poses
MIN_TRACKING_CONFIDENCE = 0.4      # Lower for smoother tracking between frames

# Delta tracking
DELTA_SMOOTHING = 0.5        # Smoothing factor (0 = raw, 1 = max smooth)
VOID_MOVE_SPEED = 2.5        # Movement amplification (tuned for natural feel)
FINGER_WEIGHT = 0.6          # How much finger movement contributes (vs palm)
PALM_WEIGHT = 0.6            # How much palm movement contributes

# ──────────────────────────────────────────────
# GESTURE DETECTION CONFIG
# ──────────────────────────────────────────────
NAMASTE_THRESHOLD = 0.14         # Max normalized distance for namaste
APART_THRESHOLD = 0.45           # Min normalized distance for hands-apart
FIST_CURL_RATIO = 0.85           # Fingertip must be this % closer to wrist than MCP
CROSSED_FINGER_THRESHOLD = 0.04  # How close index/middle tips must cross
FIST_FRAMES_REQUIRED = 3         # Consecutive fist frames before triggering
CROSSED_FRAMES_REQUIRED = 5      # Consecutive crossed-finger frames before trigger

# ──────────────────────────────────────────────
# CURSED ENERGY CONFIG
# ──────────────────────────────────────────────
ENERGY_MAX_RADIUS = 55           # Max radius for Blue/Red energy
ENERGY_PARTICLE_COUNT = 16       # Number of orbiting particles
ENERGY_SPIN_SPEED_BLUE = -0.08   # Negative = inward spin (attraction)
ENERGY_SPIN_SPEED_RED = 0.06     # Positive = outward spin (repulsion)
PURPLE_RADIUS = 80               # Purple is larger
PURPLE_PARTICLE_COUNT = 24       # More particles
PURPLE_BLEND_FRAMES = 90         # Frames for cinematic blend (~3 sec at 30fps)
COLLISION_THRESHOLD = 80         # Pixel distance for Blue+Red to trigger Purple
SPAWN_SCALE_SPEED = 0.04         # How fast energy scales up during spawning
EXPLOSION_FRAMES = 60            # Duration of explosion effect (~2 sec)
EXPLOSION_MAX_RADIUS = 500       # How big the shockwave expands
EXPLOSION_RING_COUNT = 4         # Number of expanding rings

# ── Scene Transition ──
SCENE_REAL_WORLD = 0
SCENE_TRANSITION = 1
SCENE_VOID = 2
TRANSITION_FRAMES = 100          # ~3.3 sec at 30fps
SFX_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "domain_expansion.wav")


# ──────────────────────────────────────────────
# GESTURE DETECTOR CLASS
# ──────────────────────────────────────────────
class GestureDetector:
    """
    Analyzes hand landmarks to detect gestures:
    - Namaste / Crush (hands close together)
    - Hands Apart (hands far apart)
    - Closed Fist (per hand)
    - Crossed Fingers (index + middle cross on right hand)
    - Continuous hand distance for dynamic energy scaling
    """

    # MediaPipe landmark indices
    WRIST = 0
    INDEX_MCP = 5
    INDEX_TIP = 8
    MIDDLE_MCP = 9
    MIDDLE_TIP = 12
    RING_MCP = 13
    RING_TIP = 16
    PINKY_MCP = 17
    PINKY_TIP = 20

    def __init__(self):
        # Debounce counters for fist detection
        self.left_fist_frames = 0
        self.right_fist_frames = 0

        # Debounce counters for crossed fingers
        self.left_crossed_frames = 0
        self.right_crossed_frames = 0

        # Store previous gesture state for edge detection
        self.prev_state = self._empty_state()

    def _empty_state(self):
        """Default gesture state — nothing detected."""
        return {
            "hand_distance": -1.0,    # -1 means not calculable (need both hands)
            "namaste": False,
            "hands_apart": False,
            "left_fist": False,
            "right_fist": False,
            "crossed_fingers": False,       # Right hand crossed
            "left_crossed_fingers": False,   # Left hand crossed
            "left_open": False,
            "right_open": False,
        }

    def _landmark_dist(self, lm_a, lm_b):
        """Euclidean distance between two landmarks (normalized coords)."""
        return math.sqrt((lm_a.x - lm_b.x)**2 + (lm_a.y - lm_b.y)**2)

    def _is_fist(self, landmarks):
        """
        Detect closed fist: all 4 fingertips closer to wrist than their MCP joints.
        Returns True if hand is making a fist.
        """
        wrist = landmarks.landmark[self.WRIST]

        finger_pairs = [
            (self.INDEX_TIP, self.INDEX_MCP),
            (self.MIDDLE_TIP, self.MIDDLE_MCP),
            (self.RING_TIP, self.RING_MCP),
            (self.PINKY_TIP, self.PINKY_MCP),
        ]

        curled_count = 0
        for tip_idx, mcp_idx in finger_pairs:
            tip = landmarks.landmark[tip_idx]
            mcp = landmarks.landmark[mcp_idx]

            tip_dist = self._landmark_dist(tip, wrist)
            mcp_dist = self._landmark_dist(mcp, wrist)

            # Tip closer to wrist than MCP → finger is curled
            if tip_dist < mcp_dist * FIST_CURL_RATIO:
                curled_count += 1

        return curled_count >= 4

    def _is_open_hand(self, landmarks):
        """
        Detect open hand: all 4 fingers extended (tips far from wrist).
        Opposite of fist — used for spawn gesture readiness.
        """
        wrist = landmarks.landmark[self.WRIST]

        finger_tips = [self.INDEX_TIP, self.MIDDLE_TIP, self.RING_TIP, self.PINKY_TIP]
        finger_mcps = [self.INDEX_MCP, self.MIDDLE_MCP, self.RING_MCP, self.PINKY_MCP]

        extended = 0
        for tip_idx, mcp_idx in zip(finger_tips, finger_mcps):
            tip = landmarks.landmark[tip_idx]
            mcp = landmarks.landmark[mcp_idx]
            if self._landmark_dist(tip, wrist) > self._landmark_dist(mcp, wrist):
                extended += 1

        return extended >= 3  # At least 3 fingers extended

    def _is_crossed_fingers(self, landmarks):
        """
        Detect crossed index + middle fingers.
        Strict detection: index & middle extended, ring & pinky curled,
        AND the fingertips have physically crossed over in the x-axis.
        """
        index_tip = landmarks.landmark[self.INDEX_TIP]
        middle_tip = landmarks.landmark[self.MIDDLE_TIP]
        index_mcp = landmarks.landmark[self.INDEX_MCP]
        middle_mcp = landmarks.landmark[self.MIDDLE_MCP]
        ring_tip = landmarks.landmark[self.RING_TIP]
        ring_mcp = landmarks.landmark[self.RING_MCP]
        pinky_tip = landmarks.landmark[self.PINKY_TIP]
        pinky_mcp = landmarks.landmark[self.PINKY_MCP]
        wrist = landmarks.landmark[self.WRIST]

        # 1. Index and middle MUST be extended
        index_extended = self._landmark_dist(index_tip, wrist) > self._landmark_dist(index_mcp, wrist)
        middle_extended = self._landmark_dist(middle_tip, wrist) > self._landmark_dist(middle_mcp, wrist)
        if not (index_extended and middle_extended):
            return False

        # 2. Ring and pinky MUST be curled (not extended) — this is the key filter
        #    A proper crossed-fingers pose has only index+middle out
        ring_dist = self._landmark_dist(ring_tip, wrist)
        ring_mcp_dist = self._landmark_dist(ring_mcp, wrist)
        pinky_dist = self._landmark_dist(pinky_tip, wrist)
        pinky_mcp_dist = self._landmark_dist(pinky_mcp, wrist)

        ring_curled = ring_dist < ring_mcp_dist * 1.1   # Slightly relaxed
        pinky_curled = pinky_dist < pinky_mcp_dist * 1.1
        if not (ring_curled or pinky_curled):  # At least one must be curled
            return False

        # 3. Tips must have crossed over in x-axis (sign flip)
        mcp_gap = index_mcp.x - middle_mcp.x  # Natural gap direction
        tip_gap = index_tip.x - middle_tip.x   # Current gap

        # Sign must flip AND tips must be close together
        if mcp_gap * tip_gap < 0 and abs(tip_gap) < CROSSED_FINGER_THRESHOLD * 3:
            return True

        # 4. Tips are touching/overlapping (very close in both x and y)
        tip_dist = self._landmark_dist(index_tip, middle_tip)
        if tip_dist < CROSSED_FINGER_THRESHOLD * 0.5:
            return True

        return False

    def detect(self, left_landmarks, right_landmarks):
        """
        Run all gesture detections. Returns a gesture_state dict.
        Called every frame with current landmark data.
        """
        state = self._empty_state()

        # ── Inter-hand distance (needs both hands) ──
        if left_landmarks is not None and right_landmarks is not None:
            left_wrist = left_landmarks.landmark[self.WRIST]
            right_wrist = right_landmarks.landmark[self.WRIST]
            dist = self._landmark_dist(left_wrist, right_wrist)
            state["hand_distance"] = dist

            # Namaste: hands very close
            state["namaste"] = dist < NAMASTE_THRESHOLD

            # Hands apart: hands far from each other
            state["hands_apart"] = dist > APART_THRESHOLD

        # ── Left hand gestures ──
        if left_landmarks is not None:
            raw_left_fist = self._is_fist(left_landmarks)
            state["left_open"] = self._is_open_hand(left_landmarks)

            # Debounce fist (prevent flickering)
            if raw_left_fist:
                self.left_fist_frames += 1
            else:
                self.left_fist_frames = 0
            state["left_fist"] = self.left_fist_frames >= FIST_FRAMES_REQUIRED

            # Crossed fingers on left hand (Blue trigger) — with debounce
            raw_left_crossed = self._is_crossed_fingers(left_landmarks)
            if raw_left_crossed:
                self.left_crossed_frames += 1
            else:
                self.left_crossed_frames = 0
            state["left_crossed_fingers"] = self.left_crossed_frames >= CROSSED_FRAMES_REQUIRED
        else:
            self.left_fist_frames = 0
            self.left_crossed_frames = 0

        # ── Right hand gestures ──
        if right_landmarks is not None:
            raw_right_fist = self._is_fist(right_landmarks)
            state["right_open"] = self._is_open_hand(right_landmarks)

            # Debounce fist
            if raw_right_fist:
                self.right_fist_frames += 1
            else:
                self.right_fist_frames = 0
            state["right_fist"] = self.right_fist_frames >= FIST_FRAMES_REQUIRED

            # Crossed fingers (right hand) — with debounce
            raw_right_crossed = self._is_crossed_fingers(right_landmarks)
            if raw_right_crossed:
                self.right_crossed_frames += 1
            else:
                self.right_crossed_frames = 0
            state["crossed_fingers"] = self.right_crossed_frames >= CROSSED_FRAMES_REQUIRED
        else:
            self.right_fist_frames = 0
            self.right_crossed_frames = 0

        self.prev_state = state
        return state


# ──────────────────────────────────────────────
# CURSED ENERGY CLASS
# ──────────────────────────────────────────────
class CursedEnergy:
    """
    A single cursed energy entity with procedural vortex rendering.
    Supports INACTIVE, SPAWNING, ACTIVE states.
    """
    INACTIVE = 0
    SPAWNING = 1
    ACTIVE = 2

    def __init__(self, energy_type="blue"):
        self.energy_type = energy_type  # "blue", "red", or "purple"
        self.state = self.INACTIVE
        self.pos = [CANVAS_WIDTH // 2, CANVAS_HEIGHT // 2]
        self.scale = 0.0        # 0.0 to 1.0 during spawning
        self.rotation = 0.0     # Current rotation angle
        self.breath_phase = 0.0 # Sine wave for breathing effect
        self.spawn_pos = None   # Where it first spawned

        # Type-specific settings
        if energy_type == "blue":
            self.color_core = (255, 180, 50)       # BGR warm blue
            self.color_glow = (255, 100, 0)        # BGR deep blue
            self.color_particle = (255, 220, 100)   # Bright blue
            self.max_radius = ENERGY_MAX_RADIUS
            self.particle_count = ENERGY_PARTICLE_COUNT
            self.spin_speed = ENERGY_SPIN_SPEED_BLUE
        elif energy_type == "red":
            self.color_core = (50, 80, 255)         # BGR warm red
            self.color_glow = (0, 30, 255)          # BGR deep red
            self.color_particle = (80, 120, 255)     # Bright red
            self.max_radius = ENERGY_MAX_RADIUS
            self.particle_count = ENERGY_PARTICLE_COUNT
            self.spin_speed = ENERGY_SPIN_SPEED_RED
        else:  # purple
            self.color_core = (200, 50, 200)         # BGR purple
            self.color_glow = (180, 0, 180)          # BGR deep purple
            self.color_particle = (220, 100, 255)     # Bright purple
            self.max_radius = PURPLE_RADIUS
            self.particle_count = PURPLE_PARTICLE_COUNT
            self.spin_speed = 0.04

    def spawn(self, x, y):
        """Begin spawning at position."""
        self.state = self.SPAWNING
        self.pos = [x, y]
        self.spawn_pos = [x, y]
        self.scale = 0.0
        self.rotation = 0.0

    def activate(self):
        """Transition from SPAWNING to ACTIVE."""
        self.state = self.ACTIVE
        self.scale = 1.0

    def dismiss(self):
        """Destroy the energy."""
        self.state = self.INACTIVE
        self.scale = 0.0

    def move(self, dx, dy):
        """Apply delta movement (from hand tracking)."""
        if self.state == self.ACTIVE:
            self.pos[0] += int(dx)
            self.pos[1] += int(dy)
            # Clamp to canvas
            margin = 40
            self.pos[0] = max(margin, min(CANVAS_WIDTH - margin, self.pos[0]))
            self.pos[1] = max(margin, min(CANVAS_HEIGHT - margin, self.pos[1]))

    def update(self):
        """Per-frame animation update."""
        if self.state == self.INACTIVE:
            return
        self.rotation += self.spin_speed
        self.breath_phase += 0.1

    def render(self, canvas):
        """Draw the procedural vortex effect. Optimized: single overlay blend."""
        if self.state == self.INACTIVE:
            return

        cx, cy = int(self.pos[0]), int(self.pos[1])
        s = max(0.05, self.scale)  # Minimum visible scale
        r = int(self.max_radius * s)

        # Breathing opacity pulse
        breath = 0.7 + 0.3 * math.sin(self.breath_phase)

        # Draw everything on a single overlay, blend once
        overlay = np.zeros_like(canvas)

        # ── Outer glow layers ──
        for glow_r, glow_a in [(r + 20, 0.4), (r + 10, 0.7), (r, 1.0)]:
            glow_radius = int(glow_r * breath)
            if glow_radius < 2:
                continue
            cv2.circle(overlay, (cx, cy), glow_radius, self.color_glow, -1)

        # ── Orbiting particles ──
        for i in range(self.particle_count):
            angle = self.rotation + (2 * math.pi * i / self.particle_count)

            # Vary orbit radius for chaotic feel
            orbit_base = r * (0.5 + 0.5 * ((i % 3) / 2.0))
            orbit_jitter = random.uniform(-3, 3) * s
            orbit_r = orbit_base + orbit_jitter

            px = cx + int(orbit_r * math.cos(angle))
            py = cy + int(orbit_r * math.sin(angle))

            # Particle size varies
            p_size = max(1, int((2 + (i % 3)) * s))
            cv2.circle(overlay, (px, py), p_size, self.color_particle, -1)

        # ── Inner core ──
        core_r = max(2, int(r * 0.35))
        cv2.circle(overlay, (cx, cy), core_r, self.color_core, -1)

        # Blend the entire overlay at once
        blend_alpha = 0.35 * s * breath
        cv2.addWeighted(overlay, blend_alpha, canvas, 1.0, 0, canvas)

        # Core bright center (drawn directly — fully opaque)
        center_r = max(1, int(core_r * 0.5))
        cv2.circle(canvas, (cx, cy), center_r, (255, 255, 255), -1)

        # ── Label ──
        label_map = {"blue": "BLUE", "red": "RED", "purple": "PURPLE"}
        if self.state == self.ACTIVE:
            lbl = label_map.get(self.energy_type, "")
            cv2.putText(canvas, lbl, (cx - 15, cy - int(r * 1.2)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.35, self.color_core, 1)


# ──────────────────────────────────────────────
# TECHNIQUE MANAGER
# ──────────────────────────────────────────────
class TechniqueManager:
    """
    Orchestrates Blue, Red, and Purple cursed energy techniques.
    Handles state transitions based on gesture input.
    """

    def __init__(self):
        self.blue = CursedEnergy("blue")
        self.red = CursedEnergy("red")
        self.purple = CursedEnergy("purple")

        # Track edge states for gesture transitions
        self.was_namaste = False
        self.was_apart = False
        self.was_left_crossed = False
        self.was_right_crossed = False

        # Purple blending
        self.blend_timer = 0
        self.blending = False

        # Domain Expansion explosion
        self.exploding = False
        self.explosion_timer = 0
        self.explosion_pos = [0, 0]

    def update(self, gesture_state, tracker):
        """
        State machine logic. Called every frame.
        """
        gs = gesture_state

        # ──────────────────────────────
        # DOMAIN EXPANSION EXPLOSION (locks out everything)
        # ──────────────────────────────
        if self.exploding:
            self.explosion_timer += 1
            progress = self.explosion_timer / EXPLOSION_FRAMES

            # Shrink purple during explosion
            if self.purple.state != CursedEnergy.INACTIVE:
                self.purple.scale = max(0.0, 1.0 - progress * 2)  # Shrinks fast
                if progress > 0.3:
                    self.purple.dismiss()

            if self.explosion_timer >= EXPLOSION_FRAMES:
                self.exploding = False
                self.explosion_timer = 0

            return

        # ──────────────────────────────
        # PURPLE BLENDING (locks out everything)
        # ──────────────────────────────
        if self.blending:
            self.blend_timer += 1
            # Vibrate Blue and Red towards each other
            if self.blue.state != CursedEnergy.INACTIVE:
                mid_x = (self.blue.pos[0] + self.red.pos[0]) // 2
                mid_y = (self.blue.pos[1] + self.red.pos[1]) // 2
                progress = self.blend_timer / PURPLE_BLEND_FRAMES

                # Move towards midpoint with jitter
                self.blue.pos[0] += int((mid_x - self.blue.pos[0]) * 0.05)
                self.blue.pos[1] += int((mid_y - self.blue.pos[1]) * 0.05)
                self.blue.pos[0] += random.randint(-4, 4)
                self.blue.pos[1] += random.randint(-4, 4)

                self.red.pos[0] += int((mid_x - self.red.pos[0]) * 0.05)
                self.red.pos[1] += int((mid_y - self.red.pos[1]) * 0.05)
                self.red.pos[0] += random.randint(-4, 4)
                self.red.pos[1] += random.randint(-4, 4)

                # Fade out Blue/Red, fade in Purple
                self.blue.scale = max(0.0, 1.0 - progress)
                self.red.scale = max(0.0, 1.0 - progress)
                self.purple.scale = min(1.0, progress)
                self.purple.pos = [mid_x, mid_y]

            if self.blend_timer >= PURPLE_BLEND_FRAMES:
                # Blending complete → Purple ACTIVE
                self.blue.dismiss()
                self.red.dismiss()
                self.purple.activate()
                self.blending = False

            # Update animations
            self.blue.update()
            self.red.update()
            self.purple.update()
            return

        # ──────────────────────────────
        # BLUE TECHNIQUE (Lapse)
        # ──────────────────────────────
        if self.blue.state == CursedEnergy.INACTIVE:
            # Spawn trigger: Left hand crossed fingers
            if gs["left_crossed_fingers"] and not self.was_left_crossed and self.purple.state != CursedEnergy.ACTIVE:
                self.blue.spawn(CANVAS_WIDTH // 2, CANVAS_HEIGHT // 2)

        elif self.blue.state == CursedEnergy.SPAWNING:
            # Scale up smoothly
            self.blue.scale += SPAWN_SCALE_SPEED

            if self.blue.scale >= 0.95:
                self.blue.activate()

        elif self.blue.state == CursedEnergy.ACTIVE:
            # Movement: left hand delta
            move_x = -tracker.left_dx * CANVAS_WIDTH * VOID_MOVE_SPEED
            move_y = tracker.left_dy * CANVAS_HEIGHT * VOID_MOVE_SPEED
            self.blue.move(move_x, move_y)

            # Dismiss: left fist
            if gs["left_fist"]:
                self.blue.dismiss()

        # ──────────────────────────────
        # RED TECHNIQUE (Reversal)
        # ──────────────────────────────
        if self.red.state == CursedEnergy.INACTIVE:
            # Spawn trigger: Hands apart
            if gs["hands_apart"] and not self.was_apart and not self.purple.state == CursedEnergy.ACTIVE:
                self.red.spawn(CANVAS_WIDTH // 2, CANVAS_HEIGHT // 2)

        elif self.red.state == CursedEnergy.SPAWNING:
            # Scale up based on how far apart hands are
            dist = gs["hand_distance"]
            if dist >= 0:
                target_scale = (dist - NAMASTE_THRESHOLD) / (APART_THRESHOLD - NAMASTE_THRESHOLD)
                target_scale = max(0.0, min(1.0, target_scale))
                self.red.scale += (target_scale - self.red.scale) * 0.15
            else:
                self.red.scale += SPAWN_SCALE_SPEED

            if self.red.scale >= 0.95:
                self.red.activate()

            # If hands come too close during spawning, cancel
            if dist >= 0 and dist < NAMASTE_THRESHOLD:
                self.red.dismiss()

        elif self.red.state == CursedEnergy.ACTIVE:
            # Movement: right hand delta
            move_x = -tracker.right_dx * CANVAS_WIDTH * VOID_MOVE_SPEED
            move_y = tracker.right_dy * CANVAS_HEIGHT * VOID_MOVE_SPEED
            self.red.move(move_x, move_y)

            # Dismiss: right fist
            if gs["right_fist"]:
                self.red.dismiss()

        # ──────────────────────────────
        # PURPLE TECHNIQUE (Hollow)
        # ──────────────────────────────
        if (self.blue.state == CursedEnergy.ACTIVE and
            self.red.state == CursedEnergy.ACTIVE and
            self.purple.state == CursedEnergy.INACTIVE):
            # Check collision
            dx = self.blue.pos[0] - self.red.pos[0]
            dy = self.blue.pos[1] - self.red.pos[1]
            dist = math.sqrt(dx*dx + dy*dy)
            if dist < COLLISION_THRESHOLD:
                # Begin cinematic blend!
                self.blending = True
                self.blend_timer = 0
                mid_x = (self.blue.pos[0] + self.red.pos[0]) // 2
                mid_y = (self.blue.pos[1] + self.red.pos[1]) // 2
                self.purple.spawn(mid_x, mid_y)

        # Purple active — controlled by right hand
        if self.purple.state == CursedEnergy.ACTIVE:
            move_x = -tracker.right_dx * CANVAS_WIDTH * VOID_MOVE_SPEED
            move_y = tracker.right_dy * CANVAS_HEIGHT * VOID_MOVE_SPEED
            self.purple.move(move_x, move_y)

            # Domain Expansion: right hand crossed fingers → EXPLODE!
            if gs["crossed_fingers"] and not self.was_right_crossed:
                self.exploding = True
                self.explosion_timer = 0
                self.explosion_pos = list(self.purple.pos)

        # Track edge states
        self.was_namaste = gs["namaste"]
        self.was_apart = gs["hands_apart"]
        self.was_left_crossed = gs["left_crossed_fingers"]
        self.was_right_crossed = gs["crossed_fingers"]

        # Update animations
        self.blue.update()
        self.red.update()
        self.purple.update()

    def render(self, canvas):
        """Draw all active energies and explosion onto the canvas."""
        self.blue.render(canvas)
        self.red.render(canvas)
        self.purple.render(canvas)

        # Domain Expansion explosion effect
        if self.exploding:
            self._render_explosion(canvas)

        # Void ambient text
        cv2.putText(canvas, "I N F I N I T Y   V O I D",
                     (CANVAS_WIDTH // 2 - 150, CANVAS_HEIGHT - 15),
                     cv2.FONT_HERSHEY_SIMPLEX, 0.6, (25, 25, 25), 1)

    def _render_explosion(self, canvas):
        """Render Domain Expansion shockwave explosion."""
        progress = self.explosion_timer / EXPLOSION_FRAMES
        cx, cy = int(self.explosion_pos[0]), int(self.explosion_pos[1])

        # Expanding shockwave rings
        for ring in range(EXPLOSION_RING_COUNT):
            ring_delay = ring * 0.15  # Stagger rings
            ring_progress = max(0.0, progress - ring_delay) / (1.0 - ring_delay) if progress > ring_delay else 0.0

            if ring_progress <= 0:
                continue

            radius = int(EXPLOSION_MAX_RADIUS * ring_progress)
            alpha = max(0.0, (1.0 - ring_progress) * 0.4)
            thickness = max(1, int(8 * (1.0 - ring_progress)))

            # Alternate purple and white rings
            if ring % 2 == 0:
                color = (200 + int(55 * ring_progress), 50, 200 + int(55 * ring_progress))
            else:
                color = (255, 220, 255)

            overlay = canvas.copy()
            cv2.circle(overlay, (cx, cy), radius, color, thickness)
            cv2.addWeighted(overlay, alpha, canvas, 1 - alpha, 0, canvas)

        # Center flash (bright white that fades)
        if progress < 0.4:
            flash_alpha = 0.6 * (1.0 - progress / 0.4)
            flash_r = int(80 * (1.0 - progress / 0.4))
            overlay = canvas.copy()
            cv2.circle(overlay, (cx, cy), flash_r, (255, 255, 255), -1)
            cv2.addWeighted(overlay, flash_alpha, canvas, 1 - flash_alpha, 0, canvas)

        # Scatter particles
        if progress < 0.7:
            for _ in range(int(20 * (1.0 - progress))):
                angle = random.uniform(0, 2 * math.pi)
                dist = random.uniform(20, EXPLOSION_MAX_RADIUS * progress)
                px = cx + int(dist * math.cos(angle))
                py = cy + int(dist * math.sin(angle))
                p_size = random.randint(1, 3)
                p_color = random.choice([
                    (200, 50, 200), (255, 100, 255), (180, 0, 180), (255, 255, 255)
                ])
                cv2.circle(canvas, (px, py), p_size, p_color, -1)

        # "DOMAIN EXPANSION" text flash
        if progress < 0.5:
            text_alpha = max(0.0, 1.0 - progress * 2)
            overlay = canvas.copy()
            text = "D O M A I N   E X P A N S I O N"
            text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)[0]
            tx = CANVAS_WIDTH // 2 - text_size[0] // 2
            ty = CANVAS_HEIGHT // 2
            cv2.putText(overlay, text, (tx, ty),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (220, 80, 255), 2)
            cv2.addWeighted(overlay, text_alpha, canvas, 1 - text_alpha, 0, canvas)

    def get_status(self):
        """Return current technique status for debug."""
        state_names = {0: "OFF", 1: "SPAWN", 2: "ACTIVE"}
        return {
            "blue": state_names[self.blue.state],
            "red": state_names[self.red.state],
            "purple": state_names[self.purple.state],
            "blending": self.blending,
            "exploding": self.exploding,
        }


# ──────────────────────────────────────────────
# HAND TRACKER CLASS
# ──────────────────────────────────────────────
class HandTracker:
    """
    Robust hand tracker with finger-level precision.
    Uses a blended tracking point: palm center + index/middle fingertip.
    Handles label disambiguation, hand persistence, and gesture detection.
    """

    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.mp_draw = mp.solutions.drawing_utils

        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=MAX_HANDS,
            model_complexity=MODEL_COMPLEXITY,
            min_detection_confidence=MIN_DETECTION_CONFIDENCE,
            min_tracking_confidence=MIN_TRACKING_CONFIDENCE,
        )

        # Tracking positions (blended palm + finger)
        self.left_hand_pos = None
        self.right_hand_pos = None

        # Previous frame positions
        self.prev_left_pos = None
        self.prev_right_pos = None

        # Deltas
        self.left_dx = 0.0
        self.left_dy = 0.0
        self.right_dx = 0.0
        self.right_dy = 0.0

        # Smoothed deltas
        self.smooth_left_dx = 0.0
        self.smooth_left_dy = 0.0
        self.smooth_right_dx = 0.0
        self.smooth_right_dy = 0.0

        # Full landmarks
        self.left_landmarks = None
        self.right_landmarks = None

        # Persistence: keep tracking for many frames to handle namaste/close hands
        self.left_lost_frames = 0
        self.right_lost_frames = 0
        self.LOST_THRESHOLD = 15  # High threshold — prevents loss during namaste

        # Position history for spatial disambiguation
        self.last_known_left_x = None
        self.last_known_right_x = None

        # Flag: are both hands close together? (namaste zone)
        self.hands_close = False
        self.CLOSE_THRESHOLD = 0.15  # Normalized distance to consider hands 'close'

        # Gesture detection
        self.gesture_detector = GestureDetector()
        self.gesture_state = self.gesture_detector._empty_state()

    def _get_tracking_point(self, hand_landmarks):
        """
        Calculate the blended tracking point from palm + fingertips.
        Uses palm center + index tip + middle tip for responsive control.
        This lets finger movements also control the energy position.
        """
        wrist = hand_landmarks.landmark[0]
        mid_mcp = hand_landmarks.landmark[9]
        index_tip = hand_landmarks.landmark[8]
        middle_tip = hand_landmarks.landmark[12]

        # Palm center
        palm_x = (wrist.x + mid_mcp.x) / 2.0
        palm_y = (wrist.y + mid_mcp.y) / 2.0

        # Finger center (average of index + middle fingertips)
        finger_x = (index_tip.x + middle_tip.x) / 2.0
        finger_y = (index_tip.y + middle_tip.y) / 2.0

        # Blended tracking point
        track_x = PALM_WEIGHT * palm_x + FINGER_WEIGHT * finger_x
        track_y = PALM_WEIGHT * palm_y + FINGER_WEIGHT * finger_y

        return (track_x, track_y)

    def process_frame(self, frame):
        """
        Process a RAW (unflipped) frame through MediaPipe.
        MediaPipe labels from camera's perspective, so we SWAP:
        - MediaPipe 'Left' → user's RIGHT hand
        - MediaPipe 'Right' → user's LEFT hand
        """
        h, w, _ = frame.shape

        # Convert BGR → RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb_frame.flags.writeable = False
        results = self.hands.process(rgb_frame)
        rgb_frame.flags.writeable = True

        found_left = False
        found_right = False

        if results.multi_hand_landmarks and results.multi_handedness:
            for hand_landmarks, handedness in zip(
                results.multi_hand_landmarks, results.multi_handedness
            ):
                # SWAP MediaPipe's label — it labels from camera perspective
                mp_label = handedness.classification[0].label
                label = "Right" if mp_label == "Left" else "Left"
                pos = self._get_tracking_point(hand_landmarks)

                if label == "Left":
                    self.left_hand_pos = pos
                    self.left_landmarks = hand_landmarks
                    self.left_lost_frames = 0
                    found_left = True
                elif label == "Right":
                    self.right_hand_pos = pos
                    self.right_landmarks = hand_landmarks
                    self.right_lost_frames = 0
                    found_right = True

                # Draw landmarks with correct colors
                self._draw_hand(frame, hand_landmarks, label)



        # Handle persistence
        if not found_left:
            self.left_lost_frames += 1
            if self.left_lost_frames > self.LOST_THRESHOLD:
                self.left_hand_pos = None
                self.left_landmarks = None

        if not found_right:
            self.right_lost_frames += 1
            if self.right_lost_frames > self.LOST_THRESHOLD:
                self.right_hand_pos = None
                self.right_landmarks = None

        # Calculate deltas
        self._calculate_deltas()

        # Detect gestures
        self.gesture_state = self.gesture_detector.detect(
            self.left_landmarks, self.right_landmarks
        )

        return frame

    def _draw_hand(self, frame, hand_landmarks, label):
        """Draw hand landmarks with color coding."""
        if label == "Left":
            dot_color = (255, 200, 50)    # Warm blue (BGR) for left
            line_color = (200, 150, 0)
        else:
            dot_color = (50, 80, 255)     # Warm red (BGR) for right
            line_color = (0, 50, 200)

        self.mp_draw.draw_landmarks(
            frame,
            hand_landmarks,
            self.mp_hands.HAND_CONNECTIONS,
            mp.solutions.drawing_utils.DrawingSpec(color=dot_color, thickness=2, circle_radius=2),
            mp.solutions.drawing_utils.DrawingSpec(color=line_color, thickness=1, circle_radius=1),
        )

        # Draw hand label near wrist
        h, w, _ = frame.shape
        wrist = hand_landmarks.landmark[0]
        wx, wy = int(wrist.x * w), int(wrist.y * h)
        cv2.putText(frame, label[0], (wx - 5, wy - 10),
                     cv2.FONT_HERSHEY_SIMPLEX, 0.4, dot_color, 1)

    def _calculate_deltas(self):
        """
        Calculate frame-over-frame velocity (delta) for each hand.
        Clamps extreme deltas to prevent wild jumps.
        """
        MAX_DELTA = 0.05  # Maximum single-frame delta (prevents jumps)

        # ── Left Hand Delta ──
        if self.left_hand_pos is not None and self.prev_left_pos is not None:
            raw_dx = self.left_hand_pos[0] - self.prev_left_pos[0]
            raw_dy = self.left_hand_pos[1] - self.prev_left_pos[1]

            # Clamp extreme values (hand swap / detection jump)
            raw_dx = max(-MAX_DELTA, min(MAX_DELTA, raw_dx))
            raw_dy = max(-MAX_DELTA, min(MAX_DELTA, raw_dy))

            self.smooth_left_dx = (DELTA_SMOOTHING * self.smooth_left_dx +
                                   (1 - DELTA_SMOOTHING) * raw_dx)
            self.smooth_left_dy = (DELTA_SMOOTHING * self.smooth_left_dy +
                                   (1 - DELTA_SMOOTHING) * raw_dy)
            self.left_dx = self.smooth_left_dx
            self.left_dy = self.smooth_left_dy
        else:
            self.left_dx = 0.0
            self.left_dy = 0.0
            self.smooth_left_dx = 0.0
            self.smooth_left_dy = 0.0

        # ── Right Hand Delta ──
        if self.right_hand_pos is not None and self.prev_right_pos is not None:
            raw_dx = self.right_hand_pos[0] - self.prev_right_pos[0]
            raw_dy = self.right_hand_pos[1] - self.prev_right_pos[1]

            raw_dx = max(-MAX_DELTA, min(MAX_DELTA, raw_dx))
            raw_dy = max(-MAX_DELTA, min(MAX_DELTA, raw_dy))

            self.smooth_right_dx = (DELTA_SMOOTHING * self.smooth_right_dx +
                                    (1 - DELTA_SMOOTHING) * raw_dx)
            self.smooth_right_dy = (DELTA_SMOOTHING * self.smooth_right_dy +
                                    (1 - DELTA_SMOOTHING) * raw_dy)
            self.right_dx = self.smooth_right_dx
            self.right_dy = self.smooth_right_dy
        else:
            self.right_dx = 0.0
            self.right_dy = 0.0
            self.smooth_right_dx = 0.0
            self.smooth_right_dy = 0.0

        # Store current as previous
        self.prev_left_pos = self.left_hand_pos
        self.prev_right_pos = self.right_hand_pos


# ──────────────────────────────────────────────
# LIMITLESS ENGINE
# ──────────────────────────────────────────────
class LimitlessEngine:
    """
    Main engine:
      1. Real World — fullscreen webcam, hand tracking, await cross gesture
      2. Transition — cinematic distortion + DOMAIN EXPANSION text + SFX
      3. Infinity Void — cursed energy techniques with PiP controller
    """

    def __init__(self):
        self.tracker = HandTracker()
        self.techniques = TechniqueManager()
        self.cap = None
        self.running = False

        # Scene state
        self.scene = SCENE_REAL_WORLD
        self.transition_frame = 0
        self.last_camera_frame = None  # Store last frame for transition
        self.was_right_crossed = False  # Edge detection for real-world trigger

        # FPS tracking
        self.fps = 0
        self.frame_count = 0
        self.fps_timer = time.time()

        # Sound
        self._init_sound()

    def _init_sound(self):
        """Initialize pygame mixer for sound effects."""
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=512)
            if os.path.exists(SFX_FILE):
                self.domain_sfx = pygame.mixer.Sound(SFX_FILE)
                print(f"[LIMITLESS] Sound loaded: {SFX_FILE}")
            else:
                self.domain_sfx = None
                print(f"[LIMITLESS] Warning: {SFX_FILE} not found — no sound.")
        except Exception as e:
            self.domain_sfx = None
            print(f"[LIMITLESS] Warning: Sound init failed ({e}) — no sound.")

    def _init_camera(self):
        """Initialize webcam with fallback support."""
        print(f"[LIMITLESS] Attempting to open camera index {CAMERA_INDEX}...")
        self.cap = cv2.VideoCapture(CAMERA_INDEX)

        if not self.cap.isOpened():
            print(f"[LIMITLESS] Camera {CAMERA_INDEX} not found. Trying fallback {CAMERA_FALLBACK}...")
            self.cap = cv2.VideoCapture(CAMERA_FALLBACK)

        if not self.cap.isOpened():
            print("[LIMITLESS] ERROR: No camera found! Exiting.")
            sys.exit(1)

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        print("[LIMITLESS] Camera initialized successfully.")

    def _build_real_world_frame(self, tracked_frame):
        """Build the Real World view — fullscreen webcam with hand tracking."""
        # Resize tracked frame to full canvas size
        canvas = cv2.resize(tracked_frame, (CANVAS_WIDTH, CANVAS_HEIGHT))

        # Subtle hint text
        font = cv2.FONT_HERSHEY_SIMPLEX
        hint = "Cross right fingers to enter the Void..."
        text_size = cv2.getTextSize(hint, font, 0.5, 1)[0]
        tx = CANVAS_WIDTH // 2 - text_size[0] // 2
        cv2.putText(canvas, hint, (tx, CANVAS_HEIGHT - 20),
                    font, 0.5, (180, 180, 180), 1)

        # FPS
        cv2.putText(canvas, f"FPS: {self.fps:.0f}", (15, 25),
                    font, 0.4, (0, 180, 180), 1)

        return canvas

    def _build_transition_frame(self, tracked_frame):
        """
        Build the Domain Expansion transition:
        Progressive distortion + darkening + DOMAIN EXPANSION text → Void.
        """
        progress = self.transition_frame / TRANSITION_FRAMES  # 0.0 → 1.0

        # Start with the camera frame resized to canvas
        if tracked_frame is not None:
            self.last_camera_frame = cv2.resize(tracked_frame, (CANVAS_WIDTH, CANVAS_HEIGHT))

        if self.last_camera_frame is not None:
            canvas = self.last_camera_frame.copy()
        else:
            canvas = np.zeros((CANVAS_HEIGHT, CANVAS_WIDTH, 3), dtype=np.uint8)

        # ── Phase 1 (0.0-0.4): Darken + add noise ──
        if progress < 0.4:
            p = progress / 0.4  # 0→1 within this phase
            darken = max(0.2, 1.0 - p * 0.8)
            canvas = (canvas * darken).astype(np.uint8)

            # Add noise/distortion
            noise_intensity = int(30 * p)
            if noise_intensity > 0:
                noise = np.random.randint(-noise_intensity, noise_intensity,
                                          canvas.shape, dtype=np.int16)
                canvas = np.clip(canvas.astype(np.int16) + noise, 0, 255).astype(np.uint8)

        # ── Phase 2 (0.3-0.7): DOMAIN EXPANSION text ──
        if 0.15 < progress < 0.7:
            text_p = (progress - 0.15) / 0.55  # 0→1 within this phase
            font = cv2.FONT_HERSHEY_SIMPLEX

            overlay = canvas.copy()

            # Main text grows in
            scale = 0.6 + text_p * 0.6
            text = "D O M A I N   E X P A N S I O N"
            text_size = cv2.getTextSize(text, font, scale, 2)[0]
            tx = CANVAS_WIDTH // 2 - text_size[0] // 2
            ty = CANVAS_HEIGHT // 2

            # Glow behind text
            cv2.putText(overlay, text, (tx, ty), font, scale, (180, 50, 220), 4)
            cv2.putText(overlay, text, (tx, ty), font, scale, (255, 255, 255), 2)

            alpha = min(1.0, text_p * 2) * max(0.0, 1.0 - (text_p - 0.7) / 0.3) if text_p > 0.7 else min(1.0, text_p * 2)
            cv2.addWeighted(overlay, alpha, canvas, 1 - alpha, 0, canvas)

        # ── Phase 3 (0.4-0.8): Camera dissolves into black ──
        if progress >= 0.4:
            p = min(1.0, (progress - 0.4) / 0.4)  # 0→1
            void = np.zeros_like(canvas)
            cv2.addWeighted(canvas, 1.0 - p, void, p, 0, canvas)

        # ── Phase 4 (0.7-1.0): Purple flash ──
        if 0.7 < progress < 0.9:
            flash_p = (progress - 0.7) / 0.2
            flash_alpha = 0.3 * (1.0 - abs(flash_p - 0.5) * 2)
            overlay = np.full_like(canvas, (80, 20, 100))  # Purple tint
            cv2.addWeighted(overlay, flash_alpha, canvas, 1 - flash_alpha, 0, canvas)

        return canvas

    def _build_canvas(self, controller_frame):
        """Build fullscreen Void with cursed energy techniques and PiP overlay."""
        canvas = np.zeros((CANVAS_HEIGHT, CANVAS_WIDTH, 3), dtype=np.uint8)

        # Update and render cursed energy techniques
        self.techniques.update(self.tracker.gesture_state, self.tracker)
        self.techniques.render(canvas)

        # Overlay PiP controller
        self._overlay_pip(canvas, controller_frame)

        return canvas

    def _overlay_pip(self, canvas, controller_frame):
        """Overlay the floating PiP webcam controller window."""
        pip_frame = cv2.resize(controller_frame, (PIP_WIDTH, PIP_HEIGHT))
        pip_frame = (pip_frame * PIP_OPACITY).astype(np.uint8)

        y1, y2 = PIP_Y, PIP_Y + PIP_HEIGHT
        x1, x2 = PIP_X, PIP_X + PIP_WIDTH

        y1 = max(0, y1)
        y2 = min(CANVAS_HEIGHT, y2)
        x1 = max(0, x1)
        x2 = min(CANVAS_WIDTH, x2)

        pip_h = y2 - y1
        pip_w = x2 - x1
        canvas[y1:y2, x1:x2] = pip_frame[:pip_h, :pip_w]

        # Border
        cv2.rectangle(canvas, (x1, y1), (x2, y2), PIP_BORDER_COLOR, PIP_BORDER_WIDTH)

        # Labels
        cv2.putText(canvas, "CONTROLLER", (x1 + 5, y1 + 15),
                     cv2.FONT_HERSHEY_SIMPLEX, 0.4, (120, 120, 120), 1)

        # Debug info to the right of PiP
        self._draw_debug_info(canvas, x2 + 10, y1)

    def _draw_debug_info(self, canvas, x_start, y_start):
        """Draw debug info below PiP: hand tracking + gesture state."""
        font = cv2.FONT_HERSHEY_SIMPLEX
        fs = 0.33
        y = y_start + 12
        gs = self.tracker.gesture_state

        # FPS
        cv2.putText(canvas, f"FPS: {self.fps:.0f}", (x_start, y),
                     font, fs, (0, 180, 180), 1)
        y += 14

        # Hand distance
        dist = gs["hand_distance"]
        if dist >= 0:
            dist_color = (0, 255, 255) if dist < NAMASTE_THRESHOLD else (100, 100, 100)
            cv2.putText(canvas, f"DIST: {dist:.3f}", (x_start, y),
                         font, fs, dist_color, 1)
        else:
            cv2.putText(canvas, "DIST: ---", (x_start, y),
                         font, fs, (60, 60, 60), 1)
        y += 14

        # ── Gesture indicators ──
        # Namaste
        if gs["namaste"]:
            cv2.putText(canvas, "NAMASTE", (x_start, y),
                         font, fs, (0, 255, 200), 1)
        y += 14

        # Hands apart
        if gs["hands_apart"]:
            cv2.putText(canvas, "APART", (x_start, y),
                         font, fs, (0, 200, 255), 1)
        y += 14

        # Left fist
        l_fist_color = (0, 255, 100) if gs["left_fist"] else (50, 50, 50)
        l_label = "L_FIST" if gs["left_fist"] else ("L_OPEN" if gs["left_open"] else "L: ---")
        cv2.putText(canvas, l_label, (x_start, y), font, fs, l_fist_color, 1)
        y += 14

        # Right fist
        r_fist_color = (0, 100, 255) if gs["right_fist"] else (50, 50, 50)
        r_label = "R_FIST" if gs["right_fist"] else ("R_OPEN" if gs["right_open"] else "R: ---")
        cv2.putText(canvas, r_label, (x_start, y), font, fs, r_fist_color, 1)
        y += 14

        # Crossed fingers
        if gs["crossed_fingers"]:
            cv2.putText(canvas, "CROSSED!", (x_start, y),
                         font, 0.4, (200, 0, 255), 1)
        y += 18

        # ── Technique status ──
        tech = self.techniques.get_status()

        # Blue state
        b_color = (255, 180, 50) if tech["blue"] != "OFF" else (50, 50, 50)
        cv2.putText(canvas, f"BLUE: {tech['blue']}", (x_start, y),
                     font, fs, b_color, 1)
        y += 14

        # Red state
        r_color = (50, 80, 255) if tech["red"] != "OFF" else (50, 50, 50)
        cv2.putText(canvas, f"RED: {tech['red']}", (x_start, y),
                     font, fs, r_color, 1)
        y += 14

        # Purple state
        p_color = (200, 50, 200) if tech["purple"] != "OFF" or tech["exploding"] else (50, 50, 50)
        if tech["exploding"]:
            p_label = "DOMAIN EXPANSION!"
            p_color = (220, 80, 255)
        elif tech["blending"]:
            p_label = "PURPLE: BLENDING"
        else:
            p_label = f"PURPLE: {tech['purple']}"
        cv2.putText(canvas, p_label, (x_start, y),
                     font, fs, p_color, 1)

    def _update_fps(self):
        """Calculate FPS."""
        self.frame_count += 1
        elapsed = time.time() - self.fps_timer
        if elapsed >= 1.0:
            self.fps = self.frame_count / elapsed
            self.frame_count = 0
            self.fps_timer = time.time()

    def run(self):
        """Main application loop with scene state machine."""
        self._init_camera()
        self.running = True

        print("\n" + "=" * 50)
        print("  PROJECT LIMITLESS — Cursed Energy Engine")
        print("  Real World → Domain Expansion → Infinity Void")
        print("=" * 50)
        print("\n  Phase 1: Real World")
        print("  - Camera is live. Hand tracking active.")
        print("  - Cross right-hand fingers → Enter the Void")
        print("\n  Phase 2: Infinity Void")
        print("  - Cross fingers (L) → Spawn BLUE")
        print("  - Hands apart → Spawn RED")
        print("  - Move Blue+Red together → PURPLE merge")
        print("  - Left fist → Dismiss Blue")
        print("  - Right fist → Dismiss Red")
        print("  - Cross fingers (R) while Purple → DOMAIN EXPANSION!")
        print("  - Press 'q' to quit")
        print("=" * 50 + "\n")

        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                continue

            # Process hand tracking on RAW frame
            tracked_frame = self.tracker.process_frame(frame)

            # Flip for mirror-like display
            tracked_frame = cv2.flip(tracked_frame, 1)

            # Update FPS
            self._update_fps()

            # ── Scene Router ──
            if self.scene == SCENE_REAL_WORLD:
                canvas = self._build_real_world_frame(tracked_frame)

                # Check for right-hand crossed fingers to trigger transition
                gs = self.tracker.gesture_state
                if gs["crossed_fingers"] and not self.was_right_crossed:
                    print("[LIMITLESS] Domain Expansion triggered!")
                    self.scene = SCENE_TRANSITION
                    self.transition_frame = 0
                    # Play sound
                    if self.domain_sfx:
                        self.domain_sfx.play()
                self.was_right_crossed = gs["crossed_fingers"]

            elif self.scene == SCENE_TRANSITION:
                canvas = self._build_transition_frame(tracked_frame)
                self.transition_frame += 1

                if self.transition_frame >= TRANSITION_FRAMES:
                    self.scene = SCENE_VOID
                    print("[LIMITLESS] Welcome to the Infinity Void.")

            elif self.scene == SCENE_VOID:
                canvas = self._build_canvas(tracked_frame)

            # Display
            cv2.imshow("PROJECT LIMITLESS", canvas)

            # Key handling
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                print("\n[LIMITLESS] Shutting down...")
                self.running = False

        self.cap.release()
        cv2.destroyAllWindows()
        pygame.mixer.quit()
        print("[LIMITLESS] Engine terminated. See you in the Void.")


# ──────────────────────────────────────────────
# ENTRY POINT
# ──────────────────────────────────────────────
if __name__ == "__main__":
    engine = LimitlessEngine()
    engine.run()
