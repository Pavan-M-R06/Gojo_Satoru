<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=0,2,2,5,30&height=300&section=header&text=PROJECT%20LIMITLESS&fontSize=80&fontAlignY=35&desc=%E2%88%9E%20Gojo%20Satoru%27s%20Cursed%20Energy%20%E2%80%A2%20Real-Time%20AR&descAlignY=55&descSize=20&fontColor=ffffff&animation=fadeIn" width="100%"/>
</p>

<p align="center">
  <a href="#-techniques"><img src="https://img.shields.io/badge/BLUE-Lapse_%E8%A1%93%E5%BC%8F-0096FF?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PGNpcmNsZSBjeD0iMTIiIGN5PSIxMiIgcj0iMTAiIGZpbGw9IiMwMDk2RkYiLz48L3N2Zz4=" alt="Blue"/></a>
  <a href="#-techniques"><img src="https://img.shields.io/badge/RED-Reversal_%E5%8F%8D%E8%BD%89-FF2020?style=for-the-badge" alt="Red"/></a>
  <a href="#-techniques"><img src="https://img.shields.io/badge/PURPLE-Hollow_%E8%99%9A%E5%BC%8F-9B30FF?style=for-the-badge" alt="Purple"/></a>
  <a href="#-domain-expansion"><img src="https://img.shields.io/badge/DOMAIN-Expansion_%F0%9F%92%A5-FF00FF?style=for-the-badge" alt="Domain"/></a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/OpenCV-4.x-5C3EE8?style=flat-square&logo=opencv&logoColor=white" alt="OpenCV"/>
  <img src="https://img.shields.io/badge/MediaPipe-Hands-00A67E?style=flat-square&logo=google&logoColor=white" alt="MediaPipe"/>
  <img src="https://img.shields.io/badge/NumPy-Array%20Engine-013243?style=flat-square&logo=numpy&logoColor=white" alt="NumPy"/>
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=flat-square" alt="License"/>
</p>

<br/>

<div align="center">

> _"Throughout Heaven and Earth, I alone am the honored one."_
>
> — **Gojo Satoru**

</div>

<br/>

---

## 🌀 What is Project Limitless?

**Project Limitless** is a real-time augmented reality engine that brings **Gojo Satoru's Cursed Energy techniques** from _Jujutsu Kaisen_ to life using nothing but a webcam, your hands, and pure Python.

Using **MediaPipe hand tracking** and **OpenCV procedural rendering**, your hand gestures are translated into living, breathing cursed energy that you control inside an **Infinity Void** — a fullscreen dark canvas where your techniques manifest.

```
🤞 Cross your fingers → Summon the power
✊ Clench your fist → Destroy what you created
💥 Domain Expansion → Obliterate everything
```

---

## ✨ Features

<table>
<tr>
<td width="50%">

### 🎯 Hand Tracking

- **Dual-hand finger-level tracking** via MediaPipe
- **Anatomical hand detection** — knows your left from right
- **Delta-velocity engine** — smooth, proportional movement
- **Spatial memory** — energy freezes when your hand leaves frame

</td>
<td width="50%">

### 🔮 Cursed Energy Engine

- **Procedural vortex rendering** — spinning particles, glow, breathing
- **State machine** per technique (INACTIVE → SPAWNING → ACTIVE)
- **Collision detection** — Blue + Red merge into Purple
- **Performance optimized** — single-overlay alpha blending

</td>
</tr>
<tr>
<td width="50%">

### 🎮 Gesture Recognition

- **Crossed fingers** (left/right hand detection)
- **Fist detection** with 3-frame debounce
- **Open hand** recognition
- **Inter-hand distance** calculation
- **Namaste / Hands apart** detection

</td>
<td width="50%">

### 🖥️ Display System

- **Fullscreen Infinity Void** (1280×720 pure black canvas)
- **Floating PiP** webcam overlay (bottom-left)
- **Real-time debug overlay** — gesture + technique status
- **FPS counter** and hand distance readout

</td>
</tr>
</table>

---

## 🔵🔴🟣 Techniques

### 💙 Blue — Lapse `術式`

> _The power of attraction. Cursed energy that draws everything inward._

| Property    | Detail                                              |
| ----------- | --------------------------------------------------- |
| **Spawn**   | Cross index + middle finger on **LEFT** hand        |
| **Control** | Move with your left hand                            |
| **Dismiss** | Close left fist ✊                                  |
| **Visual**  | Inward-spinning blue vortex with orbiting particles |

```
State: INACTIVE → 🤞 Left Cross → SPAWNING (scale up) → ACTIVE → ✊ Left Fist → INACTIVE
```

---

### ❤️ Red — Reversal `反轉`

> _The power of repulsion. Cursed energy that pushes everything away._

| Property    | Detail                                              |
| ----------- | --------------------------------------------------- |
| **Spawn**   | Pull both hands **apart**                           |
| **Control** | Move with your right hand                           |
| **Dismiss** | Close right fist ✊                                 |
| **Visual**  | Outward-spinning red vortex with orbiting particles |

```
State: INACTIVE → 🤚 Hands Apart → SPAWNING (scale up) → ACTIVE → ✊ Right Fist → INACTIVE
```

---

### 💜 Purple — Hollow `虚式`

> _The collision of attraction and repulsion. The ultimate technique._

| Property    | Detail                                                     |
| ----------- | ---------------------------------------------------------- |
| **Trigger** | Move Blue and Red **into each other** in the Void          |
| **Blend**   | 3-second cinematic merge animation (vibrating convergence) |
| **Control** | Right hand controls Purple after merge                     |
| **Visual**  | Massive dual-color vortex — larger than Blue or Red        |

```
State: Blue ACTIVE + Red ACTIVE → 💥 Collision → BLENDING (3s cinematic) → Purple ACTIVE
```

---

## 💥 Domain Expansion

> _"Unlimited Void."_

When **Purple is active**, cross your **RIGHT** hand's index and middle fingers to trigger the **Domain Expansion** — a devastating blast that:

```
🟣 Purple shrinks and vanishes
⭕ Expanding shockwave rings radiate outward
⚡ Bright white flash at the epicenter
✨ Scattered purple particles explode outward
📝 "D O M A I N   E X P A N S I O N" flashes across the Void
🌑 Everything clears — the Void is empty once more
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- A webcam (external or built-in)

### Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/GOJO-SATORU.git
cd GOJO-SATORU

# Create virtual environment
python -m venv .venv

# Activate it
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Run

```bash
python main.py
```

Press `q` to quit.

---

## 🎮 Controls Reference

<div align="center">

|   Gesture    | Action                          | Result                      |
| :----------: | :------------------------------ | :-------------------------- |
|   🤞 Left    | Cross index + middle finger (L) | Spawn **BLUE**              |
|     🤚🤚     | Pull both hands apart           | Spawn **RED**               |
| ← Left hand  | Move left hand                  | Control **BLUE** position   |
| → Right hand | Move right hand                 | Control **RED** position    |
|   ✊ Left    | Close left fist                 | Dismiss **BLUE**            |
|   ✊ Right   | Close right fist                | Dismiss **RED**             |
| 💥 Collision | Move Blue + Red together        | Trigger **PURPLE** merge    |
| → Right hand | Move right hand                 | Control **PURPLE** position |
|   🤞 Right   | Cross index + middle finger (R) | **DOMAIN EXPANSION** 💥     |

</div>

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                   LimitlessEngine                    │
│  ┌──────────────┐  ┌────────────────────────────┐   │
│  │  HandTracker  │  │    TechniqueManager         │   │
│  │  ┌──────────┐│  │  ┌───────┐ ┌───────┐       │   │
│  │  │ MediaPipe ││  │  │ Blue  │ │  Red  │       │   │
│  │  │  Hands   ││  │  └───┬───┘ └───┬───┘       │   │
│  │  └──────────┘│  │      │  Collide │           │   │
│  │  ┌──────────┐│  │      └────┬─────┘           │   │
│  │  │ Gesture  ││  │     ┌─────▼─────┐           │   │
│  │  │ Detector ││  │     │  Purple   │           │   │
│  │  └──────────┘│  │     └─────┬─────┘           │   │
│  └──────────────┘  │     ┌─────▼─────┐           │   │
│                    │     │ Domain    │           │   │
│  ┌──────────────┐  │     │ Expansion │           │   │
│  │   PiP + Debug │  │     └───────────┘           │   │
│  └──────────────┘  └────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

### Key Classes

| Class              | Responsibility                                                   |
| ------------------ | ---------------------------------------------------------------- |
| `LimitlessEngine`  | Main loop, canvas rendering, PiP overlay, FPS                    |
| `HandTracker`      | MediaPipe processing, delta tracking, hand persistence           |
| `GestureDetector`  | Fist/open/crossed detection, distance, debouncing                |
| `CursedEnergy`     | Single energy entity — position, state, procedural vortex render |
| `TechniqueManager` | State machine for Blue/Red/Purple, collision, explosion          |

---

## 📁 Project Structure

```
GOJO-SATORU/
├── main.py              # Everything — 1150 lines of cursed energy
├── requirements.txt     # opencv-python, mediapipe, numpy
├── .gitignore
└── README.md            # You are here
```

---

## 📦 Dependencies

```
opencv-python    → Canvas rendering, webcam capture, alpha blending
mediapipe        → Real-time hand landmark detection (21 points per hand)
numpy            → Array operations for canvas and coordinate math
```

---

## 🧠 How It Works

<details>
<summary><b>1. Hand Tracking Pipeline</b></summary>

```
Raw Camera Frame → MediaPipe (21 landmarks per hand) → Label Swap
→ Blended Tracking Point (palm + fingertips) → Delta Calculation
→ Frame Flip (mirror display) → PiP Overlay
```

MediaPipe processes the **raw unflipped frame** for accurate anatomical chirality detection. Labels are swapped (MediaPipe labels from camera perspective). Frame is then flipped for mirror-like display.

</details>

<details>
<summary><b>2. Gesture Detection</b></summary>

- **Fist**: All 4 fingertips closer to wrist than their MCP joints (3-frame debounce)
- **Open hand**: At least 3 fingers extended
- **Crossed fingers**: Index and middle finger tips swap their natural x-axis order
- **Inter-hand distance**: Euclidean distance between wrist landmarks

</details>

<details>
<summary><b>3. Procedural Vortex Rendering</b></summary>

Each energy is rendered in a single pass:

1. Create blank overlay (`np.zeros_like`)
2. Draw concentric glow circles (3 layers)
3. Draw orbiting particles (16-24 points, rotating each frame)
4. Draw inner core
5. Blend entire overlay onto canvas once (`addWeighted`)
6. Add bright center point and label

Blue spins **inward** (negative rotation), Red spins **outward** (positive rotation).

</details>

<details>
<summary><b>4. State Machine</b></summary>

```
Each frame:
  1. Check explosion state (locks everything)
  2. Check blending state (locks everything)
  3. Process Blue: gesture trigger → spawn → scale → activate → move → dismiss
  4. Process Red: gesture trigger → spawn → scale → activate → move → dismiss
  5. Check Blue+Red collision → trigger Purple blend
  6. Process Purple: move → Domain Expansion check
  7. Update edge states for next frame
```

</details>

---

## 💡 Inspired By

<div align="center">

**Jujutsu Kaisen** by Gege Akutami

_Gojo Satoru's Infinity (無下限) and his mastery of the Limitless cursed technique — the power to manipulate space at an atomic level through attraction (Blue), repulsion (Red), and their collision (Purple)._

</div>

---

<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=0,2,2,5,30&height=120&section=footer&fontSize=0" width="100%"/>
</p>

<div align="center">
  
**Built with 🤍 and cursed energy**

_Press `q` to exit the Void._

</div>
