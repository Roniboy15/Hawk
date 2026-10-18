# Engineering rules

## Scope and current setup

This is RP2040 MicroPython firmware for glider ground experiments. There is
no established flight release; the current goal is supervised table testing.

Owner-reported setup (2026-10-11):

- The glider has no engine or throttle. Older motor/throttle references are legacy.
- All servos are mounted and connected to their intended receiver channels.
- A common power rail is being ordered for the aircraft installation.

Treat these as owner-reported facts, not electrical or control-direction validation.
Mounted hardware does not automatically authorize enabling additional software axes.

Owner update (2026-10-12): four servos, BEC label 5 V @ 3 A (also marked 20 A);
elevator/rudder signals still connect directly to receiver CH2/CH4. Basic roll
MANUAL/stabilization direction tests passed by owner report. A brief loss of
socket-powered equipment remains unexplained; it returned without a manual reset.
The pitch/yaw table-test work was continued on `codex/receiver-timing-hardening`
as requested. Keep electrical qualification separate from functional acceptance.

Owner update (2026-10-13): the owner reports all axis tests passed and adjusted
both receiver and servo signs to -1 for roll/pitch/yaw. Supplied console samples
show all three MCU output values in STABILIZE with neutral sticks; they do not
independently prove actual pin wiring, mechanical effect or error recovery.
Basic direction/function acceptance is owner-reported; power, timing and fault
qualification remain open. See docs/TESTBERICHT_2026-10-13.md for evidence.
The owner approved this completion commit and the next branch on 2026-10-13.
Current branch: `codex/bench-fault-validation`, starting from the completed
step's commit f66ccd1;
do not branch from an older main or treat a bench commit as a flight release.

v0.2.3 adds bounded per-iteration timing aggregates, a transition ring and CSV/JSON
reports exported only after confirmed shutdown. Physical acceptance is pending;
follow docs/FEHLER_TISCHTEST.md and record results in its protocol template.
bench_test.run(profile) is an explicit operator entry, never an automatic launcher.
Its pitch-range profile temporarily sets the real pitch boundary to 20 degrees;
it restores RAM configuration on return and does not inject an I2C or timing fault.
tools/analyze_bench.py runs on the host, not the MCU. A software-protocol PASS
does not validate electrical signals, servo mechanics or an independent fallback.

## Working boundaries

Keep changes small and preserve the separation of pure mathematics, hardware
adapters and application orchestration. Describe coordinates, signs and units.
Keep pins, gains and limits in `firmware/config.py`.

Default validation is host-only. Hardware access, uploads, flashing, calibration,
actuator operation and flight tests require explicit task authorization.
Preserve device calibration; never silently overwrite it during source deployment.

## Safety contracts

- `AUTO_START=False` and `START_MODE='sensor'` are the safe defaults.
- SENSOR produces no PWM. First output requires valid RC calibration and fresh
  neutral frames; stabilization additionally requires a valid level reference.
- RX loss commands configured trim-neutral after output activation and clears
  the neutral gate. Reacquisition requires fresh neutral frames.
- Detected timing loss discards buffered RC, neutralizes active outputs and
  requires fresh neutral frames before software fallback can resume.
- Automation faults latch. Manual fallback depends on a functioning MCU and
  valid receiver input; it is not an independent recovery route.
- Final servo pulses remain bounded after trim. Integral anti-windup must account
  for those final bounds when integral control is enabled.
- The running control loop performs no flash writes.

The body convention is +roll right, +pitch nose-down, +yaw nose-left. Nose-up
pitch is negative; preserve the right-handed sensor/gyro transformation.
Require SENSOR/MANUAL direction checks before adding an axis to
`DIRECTION_CHECKED_AXES` and permitting its stabilization. This checkbox is
an operator acknowledgement, not an independent proof of correct wiring.
Do not infer sensor identity, signal freshness, timing guarantees or flight readiness
from host tests, register readback or WHO_AM_I alone.
An independent recovery strategy is required before considering flight operation.

## Validation and reporting

Run host tests without creating bytecode:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
```

For control, timing or safety changes, add meaningful failure-path regression tests
and update the relevant architecture/validation/operator documentation.
Check MicroPython compatibility; host mocks do not validate PIO, PWM, I2C or timing.
Report changed behavior, checks performed, remaining assumptions and which hardware
measurements must be repeated. Keep verified evidence separate from inference.
