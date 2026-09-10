---
title: My setup
description: Current hardware, software, workflow setup, and build notes.
date: '2026-06-05'
lastmod: '2026-07-15'
aliases:
- /setup.html
- /setup/
tags:
searchable: true
legacy_path: setup.html
type: "dashboard"
layout: "pc"
entryType: "dashboard"
---

A living spec sheet for my current workstation and the build notes around it.
This page summarises the current workstation hardware, software stack, and build notes.

## Current workstation

### Active system

- **Host:** Kaz
- **Operating system:** Windows 11 Pro, build 26200, x64
- **CPU:** AMD Ryzen 7 5800X, 8 cores / 16 threads
- **Motherboard:** ASUS ROG CROSSHAIR VIII EXTREME, revision X.0x
- **Memory:** 32GB DDR4 at 3600MHz, 4 x 8GB Corsair across DIMM_A1, DIMM_A2, DIMM_B1, and DIMM_B2
- **GPU:** NVIDIA GeForce RTX 3090 with 24GB VRAM, driver 32.0.16.1074, compute capability 8.6
- **Display setup:** MSI MAG401QR running vertical picture-by-picture, acting as two display surfaces, plus one additional active display path. The system reports 3 active display paths total and a 5120 x 2160 primary surface at about 179Hz.

### Storage

The current detected storage total is about **15.9TB** across eight SSD/NVMe drives.

| Model | Size |
|---|---:|
| addlink M.2 PCIe G4x4 NVMe | ~3.7TB |
| Samsung SSD 870 EVO | ~3.7TB |
| Sabrent | ~1.9TB |
| Samsung SSD 860 EVO | ~0.9TB |
| Samsung SSD 980 | ~0.9TB |
| WD_BLACK SN850X HS 2000GB | ~1.9TB |
| Sabrent | ~0.9TB |
| Samsung SSD 870 EVO | ~1.9TB |

### Audio devices

- Focusrite USB Audio
- VB-Audio Voicemeeter VAIO
- NVIDIA High Definition Audio
- NVIDIA Broadcast
- USB Audio 2.0 / Device
- ASUS Utility

### Development and tooling

The workstation has a Windows-first development toolchain:

- PowerShell 7.6.2 / 7.5.5
- VS Code, Git, GitHub CLI, GitHub Desktop, Git Extensions, GitButler, Gitify, and Neovim
- Docker Desktop, Docker Engine, Docker Compose, and Podman
- Python 3.10, 3.11, 3.12, 3.13, and 3.14
- Node.js 26.3.1, Bun 1.3.14, and pnpm 10.33.0
- Go 1.26.5, R 4.6.1, and .NET SDKs 8, 9, and 10
- Kubernetes CLI, Helm, Astro CLI, Pandoc, AWS CLI, and Azure CLI
- DBeaver, DB Browser for SQLite, SSMS, PowerBI Desktop, Bruno, and Postman
- LM Studio and Ollama for local AI/ML experiments

### Media, creative, and diagnostics

- OBS Studio, Streamlabs Desktop, Elgato Stream Deck, FFmpeg, HandBrake, and mpv.net
- GIMP, Krita, ImageGlass, ImageMagick, Figma, ONLYOFFICE, Graphviz, and Google Earth Pro
- Audacity, REAPER, Focusrite Control, Equalizer APO, EarTrumpet, and Hue Sync
- HWiNFO, LibreHardwareMonitor, CPUID HWMonitor, LatencyMon, CapFrameX, FurMark, MSI Afterburner, and AMD Ryzen Master

## Build notes

These notes document the physical build, history, and planned work separately from the detected hardware summary.

### Tower 900 workstation notes

- **Case:** Thermaltake Tower 900
- **Power supply:** Corsair HX1000i, 1000W Platinum
- **Control hardware:** Corsair iCUE Nexus, added around January 2022
- **Theme:** Halo Covenant-inspired lighting with purple, pink, and sci-fi accents

### Custom watercooling notes

The custom-loop notes are build documentation. They are kept separate from the detected hardware summary so they do not imply sensor-confirmed current state.

- 2 x Alphacool VPP Apex D5 PWM pumps
- 2 x Barrow D5 pump tops
- 2 x XSPC D5 aluminium screw rings
- Bykski POM Acrylic Double Helix T-Virus reservoirs used for fill, bleed, and visual layout
- Alphacool dual bay reservoir used for fill/bleed, then sealed
- 2 x Bykski 420mm radiators, model CR-RD420RC-TN-V3
- CPU block, GPU block, coolant temperature sensors, and Corsair Hydro X XF drain valve

Logical loop note:

```text
Green Helix Reservoir
-> Pump 1
-> BayRes / Silver Coil
-> Pump 2
-> Radiator 1
-> CPU Block
-> GPU Block
-> Radiator 2
-> Return to Green Helix
```

### Peripheral notes

These are retained as desk/setup notes. The MSI MAG401QR PBP layout is manually confirmed; the remaining peripheral list should still be treated as self-reported unless rechecked.

- **Keyboard:** Corsair K100 primary, NEWMEN GM326 backup
- **Mouse:** Corsair M65 primary, Razer Viper Mini compact mouse
- **Controllers:** Xbox One controllers
- **Headsets:** HyperX Cloud II and Corsair HS50
- **Microphone:** Audio-Technica AT-2020
- **Backup interface:** Fifine SC3
- **Webcam:** Logitech C920

## Build and learning timeline

### 2017 - First enthusiast build era

- Ryzen 7 1800X build in a Thermaltake Core V71
- Gigabyte AORUS X470 Gaming, Rev 1.0
- Initial 450W PSU

### 2020 - Audio foundation and pre-loop cooling

- Focusrite Scarlett Solo, 3rd Gen
- Audio-Technica AT-2020 microphone
- Corsair H115i RGB PRO XT 280mm AIO
- Sabrent Rocket Q 1TB NVMe

### 2021 - Major upgrade wave

- RTX 3090
- Corsair K100
- Samsung Odyssey G7 and Rift S
- Samsung 980 1TB NVMe
- EVGA SuperNOVA 750W PSU era

### 2022 - Watercooling expansion and platform upgrade

- ROG Crosshair VIII Extreme and iCUE Nexus
- Samsung 860 QVO 1TB SATA
- EK loop expansion orders and leak tester
- Vector2 ABP set order
- Crucial X6 external, later gifted

### Late 2022 - Mobile workstation

- ASUS TUF Dash F15

### 2023 onward - Storage growth

- Storage expanded into the current eight-drive SSD/NVMe set

## Accuracy audit

### Confirmed current setup

- Windows 11 Pro is the current active OS
- Ryzen 7 5800X, Crosshair VIII Extreme, 32GB DDR4-3600, and RTX 3090 are current
- Display layout is manually confirmed as MSI MAG401QR in vertical PBP acting as two display surfaces, with 3 active display paths reported by the system
- Total detected storage is about 15.9TB
- Focusrite, Voicemeeter, NVIDIA audio, NVIDIA Broadcast, USB Audio 2.0, and ASUS Utility are present
- Docker, Podman, Python, Node, Bun, pnpm, Go, R, .NET, Kubernetes, Helm, Astro, Pandoc, AWS CLI, Azure CLI, LM Studio, and Ollama are installed

### Build notes to recheck

- Thermaltake Tower 900 case
- Corsair HX1000i PSU
- Exact watercooling loop state
- Desk peripherals, microphones, headsets, webcam, and controller inventory
- NAS parts and future home-lab build plan

### To verify later

- Whether each self-reported peripheral is still in active use
- Exact model for the non-MSI display path behind the 3 active display paths
- Exact brand/model details for the Sabrent drives reported without model names
- Current custom-loop state, coolant route, sensors, pump setup, and maintenance status
- NAS motherboard, CPU, RAM, HBA, drive list, backup plan, and iSCSI workflow

## Always evolving

This setup changes as my goals change: better workflows, better stability, better documentation, and a clearer link between the hardware I use and the work I publish here.
