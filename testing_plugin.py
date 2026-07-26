#!/usr/bin/env python3
"""
Heinz Announcer v3 — URDF-correct version
Root causes fixed from actual URDF/SDF analysis:
  1. STABLE_STAND: all leg joints = 0.0 (Gazebo zero pose IS stable, no fake bend)
  2. Walk recovery: 3-stage return that explicitly zeroes hip_pitch before standing
  3. hip_roll signs: corrected per URDF asymmetric limits
     left_hip_roll:  -0.43 (outward) to +3.14 (inward)
     right_hip_roll: -3.14 (inward)  to +0.43 (outward)
     → lean LEFT  = right_hip_roll NEGATIVE (right abducts)
     → lean RIGHT = left_hip_roll  NEGATIVE (left abducts) — wait, left lower=-0.43
     Actually per URDF axis xyz="1 0 0":
     left  positive roll = left leg goes inward  (body leans left)
     right negative roll = right leg goes inward (body leans right)
     Corrected in WALK_SEQUENCE below.
"""

import sys
import threading
import time
import random
import subprocess
from datetime import datetime

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64, String

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QGridLayout, QPushButton, QLabel, QTextEdit, QProgressBar
)
from PyQt5.QtCore import Qt, QObject, pyqtSignal
from PyQt5.QtGui import QFont

# ── Phrases ───────────────────────────────────────────────────────────────────
PHRASES = {
    "greet":      ["Hey! Hello there! Welcome!",
                   "Hi! Good to see you!",
                   "Hello human! I am H1, nice to meet you!",
                   "Greetings! How are you doing today?"],
    "wave_left":  ["Hello! I am waving at you!",
                   "Hey! Over here!",
                   "Hi there! Great to see you!"],
    "wave_right": ["Hello from my right hand!",
                   "Hey! I see you!",
                   "Greetings! Welcome aboard!"],
    "both_up":    ["Yahoo! Both hands up! Welcome!",
                   "Hey everyone! Hello hello!",
                   "Big welcome! So glad you are here!"],
    "salute":     ["I salute you, human! At your service!",
                   "Reporting for duty! How can I help?",
                   "Sir yes sir! Ready to go!"],
    "walk":       ["I am walking now! Look at me go!",
                   "Taking steps forward! One two one two!",
                   "On the move! Watch out I am coming!"],
    "walk_prog":  ["I have walked {n} steps so far!",
                   "Step number {n} complete! Feeling great!",
                   "That is {n} steps already! I am on a roll!"],
}

# ── FIX 1: TRUE ZERO POSE ─────────────────────────────────────────────────────
# SDF has no initial_position set → Gazebo starts all joints at 0.0
# Zero IS the stable standing pose for this H1 model.
# Previous versions added hip_pitch=0.05, knee=0.1 "for stability" — WRONG.
# Those small offsets caused position controller to constantly fight gravity
# and created instability when returning from walk.

STABLE_STAND = {
    "left_shoulder_pitch_joint":  0.0,
    "left_shoulder_roll_joint":   0.0,
    "left_shoulder_yaw_joint":    0.0,
    "left_elbow_joint":           0.0,
    "right_shoulder_pitch_joint": 0.0,
    "right_shoulder_roll_joint":  0.0,
    "right_shoulder_yaw_joint":   0.0,
    "right_elbow_joint":          0.0,
    # All leg joints at true zero — this is what Gazebo considers stable
    "left_hip_yaw_joint":         0.0,
    "left_hip_pitch_joint":       0.0,
    "left_hip_roll_joint":        0.0,
    "left_knee_joint":            0.0,
    "left_ankle_pitch_joint":     0.0,
    "left_ankle_roll_joint":      0.0,
    "right_hip_yaw_joint":        0.0,
    "right_hip_pitch_joint":      0.0,
    "right_hip_roll_joint":       0.0,
    "right_knee_joint":           0.0,
    "right_ankle_pitch_joint":    0.0,
    "right_ankle_roll_joint":     0.0,
    "torso_joint":                0.0,
}

# ── FIX 2: WALK NEUTRAL — explicit zero of swing joints before full stand ──────
# This is the intermediate pose used ONLY during walk recovery.
# Both legs pitched to zero, knees straight, weight centered.
# Not the same as STABLE_STAND — we publish only leg joints here
# so arms stay wherever they are during the recovery.
WALK_NEUTRAL_LEGS = {
    "left_hip_pitch_joint":   0.0,
    "left_hip_roll_joint":    0.0,
    "left_hip_yaw_joint":     0.0,
    "left_knee_joint":        0.0,
    "left_ankle_pitch_joint": 0.0,
    "left_ankle_roll_joint":  0.0,
    "right_hip_pitch_joint":  0.0,
    "right_hip_roll_joint":   0.0,
    "right_hip_yaw_joint":    0.0,
    "right_knee_joint":       0.0,
    "right_ankle_pitch_joint":0.0,
    "right_ankle_roll_joint": 0.0,
}

# ── Arm poses ─────────────────────────────────────────────────────────────────
WAVE_LEFT = {
    "left_shoulder_pitch_joint": -1.0,
    "left_shoulder_roll_joint":   0.3,
    "left_shoulder_yaw_joint":    0.1,
    "left_elbow_joint":          -0.5,
    "right_shoulder_pitch_joint": 0.1,
    "right_shoulder_roll_joint":  0.0,
    "right_shoulder_yaw_joint":   0.0,
    "right_elbow_joint":          0.0,
}

WAVE_RIGHT = {
    "left_shoulder_pitch_joint":  0.1,
    "left_shoulder_roll_joint":   0.0,
    "left_shoulder_yaw_joint":    0.0,
    "left_elbow_joint":           0.0,
    "right_shoulder_pitch_joint": -1.0,
    "right_shoulder_roll_joint":  -0.3,
    "right_shoulder_yaw_joint":   -0.1,
    "right_elbow_joint":          -0.5,
}

BOTH_UP = {
    "left_shoulder_pitch_joint":  -0.9,
    "left_shoulder_roll_joint":    0.2,
    "left_shoulder_yaw_joint":     0.0,
    "left_elbow_joint":           -0.3,
    "right_shoulder_pitch_joint": -0.9,
    "right_shoulder_roll_joint":  -0.2,
    "right_shoulder_yaw_joint":    0.0,
    "right_elbow_joint":          -0.3,
}

SALUTE = {
    "left_shoulder_pitch_joint":  0.0,
    "left_shoulder_roll_joint":   0.0,
    "left_shoulder_yaw_joint":    0.0,
    "left_elbow_joint":           0.0,
    "right_shoulder_pitch_joint": -0.8,
    "right_shoulder_roll_joint":  -0.1,
    "right_shoulder_yaw_joint":    0.0,
    "right_elbow_joint":          -1.1,
}

# ── FIX 3: WALK SEQUENCE with correct hip_roll signs ─────────────────────────
# URDF axis analysis:
#   left_hip_roll  axis xyz="1 0 0": positive = left leg rolls inward
#                  lower=-0.43 (outward limit), upper=3.14 (inward)
#   right_hip_roll axis xyz="1 0 0": positive = right leg rolls outward
#                  lower=-3.14 (inward), upper=0.43 (outward limit)
#
# To lean body LEFT (weight on left foot):
#   → left leg acts as pillar: left_hip_roll = 0.0 (neutral)
#   → right leg abducts (swings out): right_hip_roll = -0.1 (inward → body tilts left)
#
# To lean body RIGHT (weight on right foot):
#   → right leg acts as pillar: right_hip_roll = 0.0 (neutral)
#   → left leg abducts: left_hip_roll = -0.1 (outward direction)
#
# hip_pitch sign: negative = leg goes FORWARD (flexion), positive = backward (extension)
# knee lower=-0.12, so minimum knee bend is very small — keep knee positive (flexed)

WALK_SEQUENCE = [
    # ── Phase 0: LEFT stance, RIGHT swing ──────────────────────────────────
    {
        # Stance leg (left) — support pillar, slight knee bend to absorb load
        "left_hip_pitch_joint":    0.05,   # very slight extension (stable)
        "left_hip_roll_joint":     0.0,    # neutral, upright
        "left_knee_joint":         0.08,   # slight bend — within limits (lower=-0.12)
        "left_ankle_pitch_joint":  0.0,    # flat foot
        "left_ankle_roll_joint":   0.0,

        # Weight shift: right leg abducts slightly to tilt CoM left
        "right_hip_roll_joint":   -0.08,   # NEGATIVE = inward = body leans left ✓

        # Swing leg (right) steps forward
        "right_hip_pitch_joint":  -0.25,   # forward step (negative = forward)
        "right_knee_joint":        0.15,   # lift and bend
        "right_ankle_pitch_joint": -0.08,  # toe up while swinging
        "right_ankle_roll_joint":  0.0,
        "right_hip_yaw_joint":     0.0,

        # Arm swing (opposite to legs — natural gait)
        "left_shoulder_pitch_joint":   0.2,   # left arm swings back
        "right_shoulder_pitch_joint": -0.2,   # right arm swings forward
        "left_shoulder_roll_joint":    0.0,
        "right_shoulder_roll_joint":   0.0,
        "torso_joint":                 0.0,
    },
    # ── Phase 1: RIGHT stance, LEFT swing ──────────────────────────────────
    {
        # Stance leg (right)
        "right_hip_pitch_joint":   0.05,
        "right_hip_roll_joint":    0.0,    # neutral
        "right_knee_joint":        0.08,
        "right_ankle_pitch_joint": 0.0,
        "right_ankle_roll_joint":  0.0,

        # Weight shift: left leg abducts to tilt CoM right
        "left_hip_roll_joint":    -0.08,   # NEGATIVE = outward = body leans right ✓
                                            # (left lower=-0.43, so -0.08 is valid)

        # Swing leg (left)
        "left_hip_pitch_joint":   -0.25,
        "left_knee_joint":         0.15,
        "left_ankle_pitch_joint":  -0.08,
        "left_ankle_roll_joint":   0.0,
        "left_hip_yaw_joint":      0.0,

        # Arm swing
        "right_shoulder_pitch_joint":  0.2,
        "left_shoulder_pitch_joint":  -0.2,
        "left_shoulder_roll_joint":    0.0,
        "right_shoulder_roll_joint":   0.0,
        "torso_joint":                 0.0,
    },
]

# Walk timing — tuned for Gazebo stability
WALK_STEPS         = 10    # interpolation steps per phase
WALK_DT            = 0.03  # seconds per step → ~0.3s per phase
SETTLE_STEPS       = 5     # brief settle between phases
SETTLE_DT          = 0.03

BTN_STYLE = """
QPushButton {{
    background: {bg};
    color: white;
    border: none;
    border-radius: 16px;
    font-size: 20px;
    font-weight: bold;
}}
QPushButton:hover    {{ background: {hv}; }}
QPushButton:pressed  {{ background: {pr}; }}
QPushButton:disabled {{ background: #374151; color: #6b7280; }}
"""

# ── Signals ───────────────────────────────────────────────────────────────────
class Sig(QObject):
    log   = pyqtSignal(str, str)
    speak = pyqtSignal(str)
    prog  = pyqtSignal(int)
    busy  = pyqtSignal(bool)


def tts(text):
    try:
        subprocess.Popen(["espeak-ng", "-v", "en", "-s", "140", "-p", "55", text],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        try:
            subprocess.Popen(["espeak", "-v", "en", "-s", "140", text],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except FileNotFoundError:
            pass


# ── ROS2 Node ─────────────────────────────────────────────────────────────────
class Announcer(Node):
    def __init__(self, sig: Sig):
        super().__init__("heinz_announcer")
        self.sig   = sig
        self._busy = False
        self._cur  = dict(STABLE_STAND)

        all_joints = list(STABLE_STAND.keys())
        self._jp = {
            j: self.create_publisher(Float64, f"/h1/{j}/cmd_pos", 10)
            for j in all_joints
        }
        self._sp = self.create_publisher(String, "/robot/speak", 10)
        self.create_subscription(String, "/robot/speak", lambda m: tts(m.data), 10)

        threading.Thread(target=self._init_robot, daemon=True).start()
        self.sig.log.emit("✅ ROS2 connected!", "#4ade80")

    def _init_robot(self):
        time.sleep(1.5)
        self.sig.log.emit("🦾 Commanding zero pose (stable stand)...", "#fbbf24")
        # Send all zeros — matches Gazebo's natural zero pose exactly
        self._goto(STABLE_STAND, steps=25, dt=0.04)
        self.sig.log.emit("✅ Robot at zero pose — ready!", "#4ade80")

    # ── Core movement ─────────────────────────────────────────────────────────
    def _pub(self, joints: dict):
        for n, v in joints.items():
            if n in self._jp:
                m = Float64(); m.data = float(v)
                self._jp[n].publish(m)
        self._cur.update(joints)

    def _goto(self, target: dict, steps: int = 15, dt: float = 0.04):
        """Smoothly interpolate current → target. Only moves joints in target dict."""
        start = {k: self._cur.get(k, 0.0) for k in target}
        for s in range(1, steps + 1):
            t = s / steps
            interp = {k: start[k] + (target[k] - start[k]) * t for k in target}
            self._pub(interp)
            time.sleep(dt)

    def _say(self, text: str):
        m = String(); m.data = text
        self._sp.publish(m)
        self.sig.speak.emit(text)
        self.sig.log.emit(f"🔊 {text}", "#60a5fa")

    def _run(self, fn, *a):
        if self._busy:
            self.sig.log.emit("⚠️ Busy — wait a moment", "#f59e0b"); return
        threading.Thread(target=fn, args=a, daemon=True).start()

    def _start(self, label, color):
        self._busy = True; self.sig.busy.emit(True)
        self.sig.log.emit(label, color); self.sig.prog.emit(10)

    def _done(self):
        """Return to zero pose after arm-only actions."""
        self._goto(STABLE_STAND, steps=25, dt=0.04)
        self.sig.prog.emit(100)
        self.sig.log.emit("✅ Done!", "#4ade80")
        time.sleep(0.3); self.sig.prog.emit(0)
        self._busy = False; self.sig.busy.emit(False)

    def _safe_return_from_walk(self):
        """
        3-stage walk recovery — prevents the post-walk fall.

        Why this works:
        Stage 1: Neutralize ONLY hip_pitch and knee on BOTH legs simultaneously.
                 This kills the forward momentum from the last swing phase.
                 We do this SLOWLY (20 steps) so Gazebo physics can settle.
                 We do NOT touch hip_roll here — let it return naturally.

        Stage 2: Short pause — let Gazebo physics fully settle with both
                 feet flat. No command sent, just time.sleep.

        Stage 3: Full STABLE_STAND (all zeros). By now CoM is centered and
                 legs are already at zero pitch/knee, so this is a tiny
                 correction — not a large jump. No fall.
        """
        self.sig.log.emit("🛑 Stage 1: Crouch to absorb momentum...", "#fbbf24")

        # Stage 1: Crouch FIRST — both legs slightly bent, hip_pitch positive
        # Why: last walk phase has hip_pitch=-0.25 (forward lean).
        # Going directly to 0.0 reverses that too fast → backward fall.
        # Positive hip_pitch (0.1) counters the forward lean gradually.
        crouch = {
            "left_hip_pitch_joint":   0.1,   # slight forward lean to counter momentum
            "left_knee_joint":        0.18,  # bent knee absorbs CoM drop
            "left_ankle_pitch_joint": 0.05,  # slight toe down
            "left_hip_roll_joint":    0.0,
            "right_hip_pitch_joint":  0.1,
            "right_knee_joint":       0.18,
            "right_ankle_pitch_joint":0.05,
            "right_hip_roll_joint":   0.0,
        }
        self._goto(crouch, steps=12, dt=0.04)

        # Stage 2: Slowly straighten from crouch to zero
        self.sig.log.emit("🛑 Stage 2: Straightening...", "#fbbf24")
        leg_neutral = {
            "left_hip_pitch_joint":   0.0,
            "left_knee_joint":        0.0,
            "left_ankle_pitch_joint": 0.0,
            "left_hip_roll_joint":    0.0,
            "right_hip_pitch_joint":  0.0,
            "right_knee_joint":       0.0,
            "right_ankle_pitch_joint":0.0,
            "right_hip_roll_joint":   0.0,
        }
        self._goto(leg_neutral, steps=20, dt=0.05)  # slow = safe

        # Stage 3: Physics settle pause
        self.sig.log.emit("🛑 Stage 3: Settling...", "#fbbf24")
        time.sleep(0.4)

        # Stage 4: Full zero — all joints
        self.sig.log.emit("🛑 Stage 4: Full stand...", "#fbbf24")
        self._goto(STABLE_STAND, steps=20, dt=0.04)

        self.sig.prog.emit(100)
        self.sig.log.emit("✅ Done — standing stable!", "#4ade80")
        time.sleep(0.3); self.sig.prog.emit(0)
        self._busy = False; self.sig.busy.emit(False)

    # ── Behaviors ─────────────────────────────────────────────────────────────
    def greet(self):      self._run(self._greet)
    def wave_left(self):  self._run(self._wave_side, "left")
    def wave_right(self): self._run(self._wave_side, "right")
    def both_up(self):    self._run(self._both_up)
    def salute(self):     self._run(self._salute)
    def walk(self, n=6):  self._run(self._walk, n)

    def _greet(self):
        self._start("👋 GREET", "#a78bfa")
        self._goto(BOTH_UP, steps=18, dt=0.05);       self.sig.prog.emit(30)
        self._say(random.choice(PHRASES["greet"]));    self.sig.prog.emit(45); time.sleep(1.0)
        self._wave_arm("left", cycles=2);              self.sig.prog.emit(65)
        self._wave_arm("right", cycles=2);             self.sig.prog.emit(85)
        self._done()

    def _wave_side(self, side):
        self._start(f"🤚 WAVE {side.upper()}", "#f472b6")
        pose = WAVE_LEFT if side == "left" else WAVE_RIGHT
        self._goto(pose, steps=15, dt=0.05);                       self.sig.prog.emit(35)
        self._say(random.choice(PHRASES[f"wave_{side}"]));         self.sig.prog.emit(50)
        self._wave_arm(side, cycles=3);                            self.sig.prog.emit(85)
        self._done()

    def _both_up(self):
        self._start("🙌 BOTH UP", "#fb923c")
        self._goto(BOTH_UP, steps=18, dt=0.05);       self.sig.prog.emit(35)
        self._say(random.choice(PHRASES["both_up"]));  self.sig.prog.emit(55); time.sleep(1.0)
        self._wave_arm("left", cycles=2);              self.sig.prog.emit(72)
        self._wave_arm("right", cycles=2);             self.sig.prog.emit(88)
        self._done()

    def _salute(self):
        self._start("🫡 SALUTE", "#34d399")
        self._goto(SALUTE, steps=15, dt=0.05);        self.sig.prog.emit(45)
        self._say(random.choice(PHRASES["salute"]));  self.sig.prog.emit(75); time.sleep(1.5)
        self._done()

    def _wave_arm(self, side: str, cycles: int = 3):
        j = f"{side}_shoulder_pitch_joint"
        base = self._cur.get(j, -0.9)
        for i in range(cycles * 2):
            target_val = base + (0.2 if i % 2 == 0 else -0.2)
            self._goto({j: target_val}, steps=6, dt=0.04)

    def _walk(self, n: int):
        self._start(f"🚶 WALK x{n}", "#fbbf24")
        self._say(random.choice(PHRASES["walk"])); time.sleep(0.4)

        for i in range(n):
            phase = WALK_SEQUENCE[i % 2]

            # Publish ONLY the joints in this walk phase.
            # DO NOT merge with STABLE_STAND — that resets joints mid-step.
            self._goto(phase, steps=WALK_STEPS, dt=WALK_DT)

            # Brief settle between phases — dono feet briefly centered
            # We only zero the roll joints here (the lean joints) so
            # there's no sudden pitch correction between steps
            settle = {
                "left_hip_roll_joint":  0.0,
                "right_hip_roll_joint": 0.0,
            }
            self._goto(settle, steps=SETTLE_STEPS, dt=SETTLE_DT)

            self.sig.prog.emit(int((i + 1) / n * 85))
            self.sig.log.emit(f"  👣 Step {i+1}/{n}", "#e5e7eb")

            if (i + 1) % 2 == 0:
                self._say(random.choice(PHRASES["walk_prog"]).format(n=i + 1))

        # Use safe 3-stage return — NOT _done()
        self._safe_return_from_walk()


# ── GUI ───────────────────────────────────────────────────────────────────────
class GUI(QMainWindow):
    def __init__(self, node: Announcer):
        super().__init__()
        self.node = node
        self.setWindowTitle("🤖Announcer")
        self.setMinimumSize(780, 660)
        self.setStyleSheet("background:#111827; color:#f9fafb;")

        root = QVBoxLayout()
        root.setSpacing(12)
        root.setContentsMargins(20, 20, 20, 20)

        t = QLabel("🤖 Announcer")
        t.setFont(QFont("Arial", 18, QFont.Bold))
        t.setAlignment(Qt.AlignCenter)
        t.setStyleSheet("color:#a78bfa;")
        root.addWidget(t)

        sub = QLabel("Zero pose stable • hip_roll signs fixed • 3-stage walk recovery")
        sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet("color:#9ca3af; font-size:12px;")
        root.addWidget(sub)

        self.pb = QProgressBar()
        self.pb.setRange(0, 100); self.pb.setValue(0)
        self.pb.setFixedHeight(7); self.pb.setTextVisible(False)
        self.pb.setStyleSheet(
            "QProgressBar{background:#1f2937;border-radius:4px;}"
            "QProgressBar::chunk{background:#7c3aed;border-radius:4px;}")
        root.addWidget(self.pb)

        BTNS = [
            ("👋\nGREET",      node.greet,           "#7c3aed","#6d28d9","#5b21b6"),
            ("🤚\nWAVE LEFT",  node.wave_left,       "#db2777","#be185d","#9d174d"),
            ("🤚\nWAVE RIGHT", node.wave_right,      "#0284c7","#0369a1","#075985"),
            ("🙌\nBOTH UP",    node.both_up,         "#ea580c","#c2410c","#9a3412"),
            ("🫡\nSALUTE",     node.salute,          "#059669","#047857","#065f46"),
            ("🚶\nWALK x4",    lambda: node.walk(4), "#d97706","#b45309","#92400e"),
            ("🚶\nWALK x8",    lambda: node.walk(8), "#b45309","#92400e","#78350f"),
        ]
        grid = QGridLayout(); grid.setSpacing(12)
        self._btns = []
        for i, (lbl, fn, bg, hv, pr) in enumerate(BTNS):
            b = QPushButton(lbl)
            b.setFixedHeight(105)
            b.setStyleSheet(BTN_STYLE.format(bg=bg, hv=hv, pr=pr))
            b.setFont(QFont("Arial", 13, QFont.Bold))
            b.clicked.connect(fn)
            grid.addWidget(b, i // 4, i % 4)
            self._btns.append(b)
        root.addLayout(grid)

        self.sb = QLabel("💬  Ready...")
        self.sb.setWordWrap(True)
        self.sb.setAlignment(Qt.AlignCenter)
        self.sb.setStyleSheet(
            "background:#1e1b4b; color:#c4b5fd; border-radius:12px;"
            "padding:14px; font-size:16px; font-weight:bold;"
            "border:1px solid #4c1d95;")
        self.sb.setMinimumHeight(60)
        root.addWidget(self.sb)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumHeight(150)
        self.log.setStyleSheet(
            "background:#0f172a; color:#94a3b8; border:1px solid #1e293b;"
            "border-radius:8px; font-family:monospace; font-size:12px; padding:6px;")
        root.addWidget(self.log)

        tip = QLabel(
            "Walk tuning: WALK_STEPS / WALK_DT  |  "
            "Recovery tuning: steps=20/dt=0.05 in _safe_return_from_walk()"
        )
        tip.setAlignment(Qt.AlignCenter)
        tip.setStyleSheet("color:#374151; font-size:11px;")
        root.addWidget(tip)

        w = QWidget(); w.setLayout(root)
        self.setCentralWidget(w)

        node.sig.log.connect(self._on_log)
        node.sig.speak.connect(lambda t: self.sb.setText(f'💬  "{t}"'))
        node.sig.prog.connect(self.pb.setValue)
        node.sig.busy.connect(lambda b: [x.setEnabled(not b) for x in self._btns])

    def _on_log(self, msg, color):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log.append(f'<span style="color:{color}">[{ts}] {msg}</span>')


def main():
    rclpy.init()
    sig  = Sig()
    node = Announcer(sig)
    threading.Thread(target=lambda: rclpy.spin(node), daemon=True).start()
    app = QApplication(sys.argv)
    win = GUI(node)
    win.show()
    ret = app.exec_()
    node.destroy_node()
    rclpy.shutdown()
    sys.exit(ret)

if __name__ == "__main__":
    main()