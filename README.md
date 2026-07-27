# 🤖 Gazebo ROS Text-to-Speech (TTS) Plugin for Gazebo Harmonic

> **Bring natural speech output to your Gazebo Harmonic robots using ROS 2.**

The **Gazebo ROS Text-to-Speech (TTS) Plugin for Gazebo Harmonic** is the next generation of our previously released **Gazebo ROS Text-to-Speech (TTS) Plugin** for **Gazebo Classic**.

The original project introduced offline speech synthesis for robots running inside Gazebo Classic, enabling robots to naturally speak messages published from ROS 2 topics using offline Text-to-Speech (TTS) engines such as **eSpeak**, **Festival**, and **Piper**. It provided an easy and lightweight solution for adding natural voice interaction to simulation environments and Human-Robot Interaction (HRI) applications.

With the robotics community rapidly moving toward the modern **Gazebo Harmonic (gz-sim)** ecosystem, this repository extends the same idea to the latest generation of Gazebo.

Unlike the previous release, which focused on a standalone demonstration, this version integrates the plugin into a complete humanoid robot running in Gazebo Harmonic. The plugin has been successfully tested with the **Heinz H1 Humanoid Robot**, demonstrating synchronized robot speech and physical actions inside the simulator.

The plugin supports both **ROS 2 Humble** and **ROS 2 Jazzy**, allowing developers and researchers to build modern Human-Robot Interaction (HRI), Embodied AI, Physical AI, and Vision-Language-Action (VLA) systems using the latest Gazebo architecture.

This project represents the official continuation of our Gazebo Classic plugin and serves as the foundation for the next generation of conversational robots in simulation.

---

# Why This Plugin?

Recent advances in **Large Language Models (LLMs)**, **Vision-Language Models (VLMs)**, **Vision-Language-Action (VLA)** systems, and **Physical AI** have significantly improved robot intelligence.

Today's robots can:

* Understand natural language
* Perceive complex environments
* Reason about tasks
* Navigate autonomously
* Manipulate objects
* Interact intelligently with humans

However, one essential capability has remained limited inside modern simulation environments:

> **Natural robot speech integrated directly into Gazebo Harmonic.**

While our previous Gazebo Classic plugin solved this limitation for Gazebo Classic, researchers increasingly require support for the latest Gazebo ecosystem.

This repository fills that gap.

It enables robots running in **Gazebo Harmonic** to speak naturally while performing physical actions, allowing researchers to build complete Human-Robot Interaction pipelines entirely inside simulation before deploying them to real hardware.

> **You build the robot intelligence.
> This plugin gives your Gazebo Harmonic robot a natural voice.**

---

# What's New?

Compared to the original Gazebo Classic release, this version introduces:

* Native Gazebo Harmonic support
* ROS 2 Humble support
* ROS 2 Jazzy support
* New gz-sim plugin architecture
* Humanoid robot integration
* Speech synchronized with robot motions
* GUI-based testing application
* Improved robot behavior validation
* Easier integration with modern ROS 2 projects
* Foundation for future conversational robotics

---

# Features

* Native Gazebo Harmonic plugin
* ROS 2 Humble support
* ROS 2 Jazzy support
* Offline Text-to-Speech
* eSpeak support
* Festival support
* Piper support
* Humanoid robot integration
* Speech synchronized with robot behaviors
* GUI testing application
* Lightweight architecture
* Easy integration into existing robots
* Works entirely offline
* Human-Robot Interaction ready
* Physical AI ready
* Embodied AI ready
* Research and education friendly

---

# Architecture

```text
                     Human / Application
                             │
                             ▼
                   testing_plugin.py
                             │
               ┌─────────────┴─────────────┐
               ▼                           ▼
      ROS2 Joint Controllers       /robot/speak
               │                           │
               ▼                           ▼
      Humanoid Robot Motion      Gazebo Harmonic
                                 TTS Plugin
                                       │
                          ┌────────────┼────────────┐
                          ▼            ▼            ▼
                      eSpeak      Festival      Piper
                                       │
                                       ▼
                              Robot Speech Output
```

Both robot motion and speech execute simultaneously, enabling synchronized behaviors for realistic Human-Robot Interaction.

---

# Tested Platforms

| Operating System | ROS 2  | Gazebo          | Status   |
| ---------------- | ------ | --------------- | -------- |
| Ubuntu 22.04     | Humble | Gazebo Harmonic | ✅ Tested |
| Ubuntu 24.04     | Jazzy  | Gazebo Harmonic | ✅ Tested |

---

# Tested Robot

The plugin has been successfully integrated with the **Heinz H1 Humanoid Robot**.

Clone the repository:

```bash
git clone https://github.com/K-d4wg/ros2_heinz.git
```

The Gazebo Harmonic TTS plugin was added directly to the humanoid robot simulation and successfully validated with synchronized robot speech and physical actions.

---

# Testing Application

A dedicated Python application named

```text
testing_plugin.py
```

was developed to validate robot behaviors together with speech generation.

The testing application provides:

* Greeting
* Left hand wave
* Right hand wave
* Both hands up
* Salute
* Walking
* Stable standing initialization
* Smooth motion interpolation
* Safe walk recovery
* Speech synchronization
* GUI controls
* Progress monitoring
* Live status logging

The application initializes the robot in a stable standing pose, publishes speech messages to `/robot/speak`, commands all major humanoid actions, and synchronizes robot speech with every behavior. Safe standing recovery and smooth joint interpolation are also implemented for reliable motion execution.

---

# Demonstrated Behaviors

The plugin has been successfully validated with:

* Greeting
* Left hand wave
* Right hand wave
* Both hands up
* Salute
* Walking
* Speech announcements
* Motion + speech synchronization

Every behavior was tested successfully inside Gazebo Harmonic.

---

# Applications

This plugin can be integrated into:

* Human-Robot Interaction (HRI)
* Physical AI
* Embodied AI
* Vision-Language-Action (VLA)
* Vision-Language-Action-Speech (VLAS)
* Mobile Manipulators
* Humanoid Robots
* Service Robots
* Educational Robotics
* Digital Twins
* AI Robot Assistants
* Research Demonstrations
* ROS 2 Simulation Projects

---

# Project Structure

```text
ros2_heinz/
│
├── h1_gazebo_sim/
├── gz_ros_tts/
├── launch/
├── models/
├── worlds/
├── testing_plugin.py
└── README.md
```

---

# Roadmap

## Completed

* [x] Gazebo Classic TTS Plugin Release
* [x] Gazebo Harmonic Support
* [x] ROS 2 Humble Support
* [x] ROS 2 Jazzy Support
* [x] Humanoid Robot Integration
* [x] Speech and Motion Synchronization
* [x] GUI Testing Application
* [x] Offline Text-to-Speech Support

---

# Coming Soon 🚀

This repository represents only the first step toward the next generation of intelligent conversational robots inside Gazebo.

As robotics continues to evolve toward **Physical AI**, **Embodied AI**, and **Vision-Language-Action-Speech (VLAS)** systems, we are actively developing new capabilities that will transform Gazebo into a complete platform for natural Human-Robot Interaction.

## 🎙️ Audio-to-Audio Interaction

Our next major release will introduce **real-time Audio-to-Audio communication**, allowing users to talk directly with robots inside the simulator using natural speech.

Instead of manually publishing ROS topics, users will simply speak to the robot.

The complete interaction pipeline will be:

```text
Human Voice
      │
      ▼
Speech-to-Text (STT)
      │
      ▼
Large Language Model (LLM)
      │
      ▼
Robot Reasoning
      │
      ▼
Text-to-Speech (TTS)
      │
      ▼
Robot Voice Response
```

The robot will be able to listen, understand, reason, and respond naturally in real time.

---

## Planned Features

* 🎤 Real-time Audio-to-Audio interaction
* 🧠 LLM-powered robot conversations
* 👀 Vision-Language-Action-Speech (VLAS) integration
* 🌍 Multi-language speech support
* 😊 Emotion-aware speech generation
* 🗣️ Natural voice conversations
* 🤖 Voice-controlled robot behaviors
* 🦾 Autonomous task execution through conversation
* 👥 Multi-robot communication
* ☁️ Local and cloud AI model support
* 🔊 High-quality neural voice synthesis
* 🧩 Agentic AI integration
* 🌐 Support for additional Gazebo Harmonic robots

---

## Our Vision

We believe the future of robotics is not only about robots that can perceive, reason, and act—but also robots that can communicate naturally.

Our long-term vision is to transform Gazebo Harmonic into a complete development platform for conversational robots, where researchers and developers can build, test, and evaluate entire Human-Robot Interaction pipelines before deploying them to real-world robotic systems.

From offline Text-to-Speech to fully autonomous Audio-to-Audio conversations, this project is a step toward making simulated robots feel as natural and interactive as real-world intelligent assistants.

---

# Authors

* **Aachal Sharma**
* **Rahul Gupta**

**Equal Contribution:** Aachal Sharma and Rahul Gupta contributed equally to the design, implementation, development, integration, testing, and documentation of this project.

---

# Citation

If you use this project in your research, please consider citing it.

```bibtex
@software{gazebo_harmonic_tts_plugin,
  title  = {Gazebo ROS Text-to-Speech Plugin for Gazebo Harmonic},
  author = {Aachal Sharma and Rahul Gupta},
  year   = {2026},
  note   = {ROS 2 Humble and ROS 2 Jazzy}
}
```

---

# License

This project is released under the **MIT License**.

---
