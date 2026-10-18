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
reports exported only after confirmed shutdown. Physical results and open items
are in docs/testdaten/Tischtests_v0.2.3-bench/; use docs/FEHLER_TISCHTEST.md.
bench_test.run(profile) is an explicit operator entry, never an automatic launcher.
Its pitch-range profile temporarily sets the real pitch boundary to 20 degrees;
it restores RAM configuration on return and does not inject an I2C or timing fault.
tools/analyze_bench.py runs on the host, not the MCU. A software-protocol PASS
does not validate electrical signals, servo mechanics or an independent fallback.

Owner update (2026-10-18), actual v0.2.3 reports: T2 neutral gating passed;
first T1 latched IMU_RUNTIME at 51228 ms, a later T1 repeat passed without PWM
or faults. Original T1 files were replaced by the owner; keep the first findings
separate from the repeat and preserve archived run copies. New reports identify
MicroPython v1.29.0 / RP2040-Zero; runtime/calibration snapshots are now archived.
Work times reach about 29-30 ms despite the 10-ms target; no hard timing trip.
Abrupt USB removal without Ctrl+C caused extreme rudder movement while BEC and
common ground remained connected. Correct shutdown avoided it by owner report.
Stop, await exports, turn BEC/receiver/servos off, download with USB connected,
then remove USB. Do not deliberately reproduce power loss with mounted actuators.
Further owner update (2026-10-18): T3/T5/T6 functioned as expected. T3 data prove
all three missing-start-channel cases; T5 has fault-free stabilization for about
95 s but averages only 74.92 Hz, with work >10 ms in 99.44% of iterations.
T6 proves PITCH_RANGE latching; later yaw pulse loss causes RX_TIMEOUT and neutral
outputs, ending without recovery. The owner subsequently confirmed a connector
fell out; record this as the owner-reported cause, consistent with the logged
yaw pulse loss, not an unexplained receiver/software fault. Secure the connection
before repeat tests. T4 is deliberately OPEN because no signal switch was
installed; the incidental T6 event does not replace it. Only one T5 run is archived.
The T6 frozen pitch plus level reference is consistent with the negative 20-degree
boundary. Preserve calibration/signs; account for the absolute boundary in repeats.
Next code scope is timing/fault diagnostics, not gain tuning or navigation.
See docs/testdaten/Tischtests_v0.2.3-bench/AUSWERTUNG_T3_T5_T6.md and
docs/NAECHSTE_SCHRITTE.md. Do not label all fault/timing qualification complete.

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
