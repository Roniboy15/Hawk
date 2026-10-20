# Engineering rules

## Scope and current setup

This is RP2040 MicroPython firmware for glider ground experiments. There is
no established flight release. Current work is GPS/barometer bring-up, followed
by manual data collection and a reassessment using measured results.

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
Table-test results are committed as 913a9e6 on codex/bench-fault-validation.
Current branch: codex/gps-baro-bringup, starting from that result commit.
Do not branch from an older main or treat a bench commit as a flight release.

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
Owner decision (2026-10-18): progress with BN-180 GPS and GY-63/MS5611 sensor
checks first, then collect flight data using the existing MCU MANUAL-through
path. The owner explicitly accepts the absence of an independent manual fallback;
do not impose a new approval gate or block sensor work on a bypass or exactly
100 Hz. Record the risk honestly: MANUAL still needs the MCU, and a low failure
probability is not established. Timing/fault investigation continues alongside
sensor work and later data collection; it is not a blanket stop on development.
An autonomous circle remains a later navigation/control implementation, not a
feature enabled merely by attaching GPS/barometer. The current standalone
sensor_test profiles never start app/PWM and are not yet a flight logger.
GY-63 pin labels are owner-confirmed: VCC/GND/SCL/SDA/CSB/SDO/PS. GPS cable
pin order and actual signal level remain to be checked before physical connection.
See docs/testdaten/Tischtests_v0.2.3-bench/AUSWERTUNG_T3_T5_T6.md and
docs/NAECHSTE_SCHRITTE.md. Do not label all fault/timing qualification complete.

Owner update (2026-10-19): first GY-63 run archived under
docs/testdaten/barometer_tests/; 60.002 s, 594 samples, valid PROM CRC,
no logged errors. Sensor data path verified. Owner subsequently confirmed lifting
Hawk during this same run: indicated height increased by approximately the lift
distance. S1 functionally passed using log evidence plus owner observation;
absolute accuracy/drift/repeatability are not quantified. GPS was disconnected
for that barometer run; a later GPS result is recorded below.
Separate incident: powered BEC/receiver and transmitter already on, elevator/
rudder at GP6/GP7 moved to maximum on USB insertion and stayed there. Owner
believes no program was running; Thonny was open. Existing IMU was unpowered
but SDA/SCL/GND remained connected. Owner later supplied current main.py with
matching startup logic and reported AUTO_START=False; files at the incident
may have differed, boot.py/waveforms unknown. Capacitor reported 1000 uF / 10 V,
parallel across regulated BEC 5 V and GND, minus to GND. This reported connection
is plausible; no measurements establish capacitor performance or event cause.
Do not attribute this to attitude correction: sensor_test never uses IMU/PWM.
Keep servos off for sensor-only work; power the IMU normally or disconnect it
fully with all supplies off, not VCC alone. Investigate startup/back-power and
wiring before another powered mounted-actuator test; do not deliberately
reproduce endstop movement or add automatic boot PWM as an unproven fix.
This does not block isolated sensor development or revoke the accepted MCU risk.

Later owner update (2026-10-19): BN-180 connected and tested outdoors;
white wire identified as GPS TX in the supplied description. Apply that color
only to this specimen, not every BN-180; actual TX voltage was not measured.
docs/testdaten/gps_tests/ contains a 180.225-s run with 908 checksum-valid
sentences, 360 GGA/RMC updates, no checksum/parse errors, but no logged paired
fix. First raw sentences show no fix; later receiver fix status cannot be
reconstructed because 314 poll gaps clear current state. Do not call S2 passed
or infer a defective GPS/zero satellites for the whole run from reset defaults.
Source bug: RP2 v1.29 enforces inter-character timeout even at timeout_char=0;
fixed-size UART reads can wait through a serial burst. Sensor-test 0.1.1 now
requests only min(UART.any(), limit) in normal and discard paths, preserving
100-ms freshness and paired-fix rules. New receiver fix/satellite counters survive
freshness resets and are not current navigation validity. Two timed-stream
regressions failed before the fix, passed after; 123 host tests now pass.
Physical improvement/fix still needs an outdoor repeat with the six updated
sensor modules; then S3. Keep old logs and save repeats in separate folders.

Owner/result update (2026-10-20): gps_2 plus a supplied console excerpt now
functionally pass S2: first paired fix 74.820 s, 106 GGA and 106 RMC fix sentences,
up to 12 used satellites, no poll gaps/checksum/parse errors. Work max 33.329 ms,
no >50-ms event. CSV is only final 40.735 s; the owner returned earlier. Console
proves west/south movement then east/north return; exact original start position
is missing, so do not assert surveyed closure or absolute accuracy. See
docs/testdaten/gps_tests/AUSWERTUNG_GPS_2.md and gps_2_konsole.txt. Preserve raw
files. The logged test version is still 0.1.0 despite new counters; actual file
set/import cache uncertain. Next S3 must use consistent modules and soft reboot.
Owner requested retaining whole short sensor runs. Sensor-test 0.2.0 now stores
packed RAM samples (83 bytes, default 2 Hz), allocates for the requested duration
before hardware, and exports after stop. About 30 kB for 180 s, 50 kB for 300 s;
64-KiB buffer limit plus planned 32-KiB free-RAM reserve. Reject oversize/low
reported memory before starting devices; never silently wrap or lower rate.
CSV still 25 columns, UTC normalized to milliseconds; JSON schema 2 records log
capacity/bytes/all_samples_retained. Power loss still loses RAM. Existing app/
bench logging is unchanged; this is not yet a MANUAL flight logger. 129 host
tests pass, including full simulated 180-s retention and memory/overflow paths.
New storage needs physical validation in a ground run, not another mandatory S2 repeat.

Owner/result update (2026-10-20): S3 functionally passed, 172.972 s, explicitly
stopped by owner with Ctrl+C, shutdown_ok and no logged sensor errors/poll gaps.
Owner route: south level, west uphill, east downhill, north level. Archived
S3 still identifies sensor-test 0.1.0/schema 1 and retains 200 of 841 rows,
only final 40.963 s; do not claim the new 0.2.0 full-run buffer was physically
validated or that the entire route is proved. Last window moves mostly north
with an east component. Barometer compensation matches raw data, but a 2.21-m
height change over 0.201 s needs installation/pressure-artifact checks, not an
assumed physical climb or a speculative filter fix. See
docs/testdaten/S3_gps_and_baro/AUSWERTUNG.md. Preserve raw files.
Planned IMU installation is owner-confirmed top-up, X rearward: a 180-degree
Z rotation, body_axes=(0,1,2), body_signs=(-1,-1,1). Change active mapping only
with physical remount, recalibrate level, retain RC and raw-frame acc calibration,
then redo SENSOR/MANUAL/stabilization directions. Level calibration alone cannot
detect the reversed longitudinal axis. Two new host regressions cover transforms
and calibration compatibility; 131 total tests pass. Current mapping is unchanged.
Installation rails: GPS uses regulated 5 V; IMU and GY-63 use 3V3, shared GND.
Do not put all three sensors on 3V3 or parallel BEC/USB 5-V sources at the board.
Owner approved the sensor closure commit and creation of codex/manual-flight-logger
on 2026-10-20. Keep the closure on codex/gps-baro-bringup and start the logger
branch directly from that commit, not old main. No push or merge is requested.
docs/EINBAU_UND_MANUAL_DATENFLUG.md specifies wiring, power,
mounting and the proposed five-minute/1-Hz logger with continued MANUAL on log
capacity exhaustion and a ground-only stop/export before power removal.

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
An independent recovery strategy remains an engineering recommendation. Respect
the owner's accepted test risk above; never describe the absent path as implemented
or certify flights from successful host/table tests.

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
