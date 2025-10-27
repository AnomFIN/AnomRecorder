Camera system (Python) with XYZ control

Overview
- Live preview from a USB camera via OpenCV.
- Keyboard control to move an XYZ camera stage (mock or serial).
- Simple serial protocol so an Arduino or similar can drive steppers/servos.

Dependencies
- Python 3.9+
- OpenCV: `pip install opencv-python`
- Optional (for hardware control): `pip install pyserial`

Run
- Mock controller (no hardware):
  - `python camera_system.py --mock`
- Select camera index or path:
  - `python camera_system.py --device 0`  (or `/dev/video2`)
- With serial controller (example):
  - `python camera_system.py --serial-port /dev/ttyACM0 --baud 115200`

Useful flags
- `--width 1280 --height 720 --fps 30` set capture.
- `--step 1.0` units per key press (mm or steps as your firmware defines).
- `--fast-mult 5` multiplier when using uppercase keys (Shift).
- `--invert-x --invert-y --invert-z` flip axis directions.

Controls
- `W/S`: +Y / -Y
- `A/D`: -X / +X
- `Q/E`: -Z / +Z
- `H`: Home axes (same as `C` in this build)
- `C`: Home all
- `Esc`: Quit
- Use uppercase (hold Shift) for fast moves with `--fast-mult`.

Serial protocol (simple ASCII)
- MOVE: `MOVE X <dx> Y <dy> Z <dz>`
- HOME: `HOME XYZ` (letters optional subset, e.g., `HOME XZ`)
- Lines end with `\n`. Floats or ints allowed. Firmware should interpret units.

Arduino example
- See `arduino/xyz_controller.ino` for a minimal parser and TODOs to drive motors.
- It currently only prints actions; you must wire drivers and implement motion.

Tips
- On Linux, list serial ports with: `ls /dev/ttyACM* /dev/ttyUSB* 2>/dev/null`.
- If the camera fails to open, try a different index/path or close other apps using it.
- For UVC cameras that support pan/tilt/zoom, you may also explore `v4l2-ctl`.

