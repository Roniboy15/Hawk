# Engineering rules

## Scope and current setup

This is RP2040 MicroPython firmware for glider ground experiments. There is
no established flight release. Current work is MANUAL flight-logger preparation
on codex/manual-flight-logger, followed by measured data collection/reassessment.

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

Owner decision (2026-10-20), superseding that five-minute/1-Hz proposal: no fixed
flight timer. Free former throttle channel is CH3, a separate PWM output;
physical low selects MANUAL without recording, high selects MANUAL plus recording.
Pulse endpoints/polarity and receiver model are still unknown. Middle retains
state; debounce and low-before-high startup prevent accidental starts. Loss of
this auxiliary channel must not invalidate the three flight-control axes or
stop PWM. Repeated on/off creates segments; buffer-full/error stops logging only.
Use existing hardware first and measure onboard flash on the ground. Owner's
>1-MB-free figure is capacity, not timing qualification. RP2 v1.29 flash operations
disable interrupts/XIP and can stall RC updates; no flight flash backend is enabled.
recording.py implements the pure switch, including reverse pulse polarity;
logger_bench.py provides explicit run_channel/run_storage, no app/PWM, no import
side effects. CH3 test uses proposed free GP14 with servo power disconnected;
receiver needs its own BEC supply and shared GND, MCU uses USB without tied 5 V.
Storage test uses USB only/BEC off, three new 64-KiB pattern files and 128-KiB
space reserve; measures write/flush/sync/close, verifies readback, never deletes
old files or touches calibration. It is not the flight logger or a timing proof.
146 host tests pass; neither new hardware test has been executed by the agent.
Owner subsequently selected about ten minutes of total recording per flight as
a storage sizing target, still no stop timer. Proposed compact multirate package:
25-Hz gyro/RX/servo (50 Hz if measured budgets allow), 10-Hz attitude/acceleration
and barometer, 1-Hz GPS/status. Estimated 32/24/32/64/32-byte records are not yet
implemented/verified; count metadata/filesystem overhead before promising duration.
See docs/FLUGLOGGER_PLAN_UND_BODENTEST.md for capacity estimates and L1/L2 instructions.
BN-180 TX LED means serial output, PPS means receiver 3D fix; neither proves
the MCU parsed fresh positions. Software readiness LED is planned, not implemented.

Owner/result update (2026-10-21): L1/L2 archived in docs/testdaten/logger_boden/.
L1: 1300 fresh frames, 998..1998 us, last 998, clean shutdown. Owner confirms
first and last stick state were bottom, establishing bottom=998/top=1998.
RECORDING_CHANNEL now prepares pin14/1200-off/1800-on/200ms/sign+1, unused by app.
L2: all three 64-KiB pattern files verified, no reported errors, but write max
72.098 ms, flush max 114.338 ms, cycle max 181.709 ms; 109/208 reported cycles
over deadline. v0.1.0 did not store the threshold; current MAX_LOOP_US is 50 ms.
Free flash before patterns 1265664 B, after 1056768 B; capacity is not the problem.
Do not put this blocking filesystem writer in the MANUAL loop, hide time from
fault detection, or raise thresholds merely to accept it. No servo timing was
measured in this separate test. See AUSWERTUNG_L1_L2.md; preserve raw JSON.
Owner asks whether less frequent saving helps. Explain frequency versus maximum
stall separately. Proposed existing-hardware alternative: ~1-Hz full snapshots
in RAM and export after ground shutdown; GPS/slow flight-data useful, fast
gain analysis limited. This is a proposal, not consent to silently change final
flight-data quality. No in-air export on CH3-low; power loss loses unsaved RAM.
logger_bench 0.1.1 adds run_ram(): imports modules only, tests 144 B*(600+32)=91008 B
buffer plus 64 KiB reserve, releases it before JSON. L3 is preliminary: no actual
controller objects or final encoder, no hardware qualification. Ten minutes is
memory-sizing target, never a flight stop timer. No independent bypass gate added.

Owner/result update (2026-10-21), L3 0.1.1: allocation_failed for a single
91008-B bytearray, despite 164880 B total free and a 65536-B reserve target.
estimated_capacity_samples=689 is arithmetic, not successful allocation.
Fragmentation/split heap is consistent but not measured. Preserve original
logger_ram_357044_0.json and see docs/testdaten/logger_boden/AUSWERTUNG_L3.md.
Bench 0.1.2 now uses ram_buffer.RecordBuffer: 632 budgeted 144-B records in
39*2304-B blocks plus 1152 B, same payload/reserve, no silent rate/capacity cuts.
Whole records stay within blocks; slot indices do not wrap. Partial allocation
and interrupt release blocks; JSON follows release/GC. Content probe then GC
precedes actual remaining-RAM measurement, including list/object overhead.
156 host tests pass. New block variant still needs only L3 repeated by owner;
L1/L2 need no blanket repeat. Final encoder/controller objects are still absent,
so even fits_preliminary is not a complete application or timing qualification.

Later L3 result (0.1.2): allocation_failed/phase allocate despite 162608 B free;
raw logger_ram_1246428_0.json copied unchanged to L3_bloecke/. Planned block_count
40 and max_block_bytes 2304 do NOT report actual progress. No exact failing
block/error message is available, so do not assert proven fragmentation or that
even the first 2304-B allocation failed. Bench 0.1.3 instruments allocation:
actual successful blocks/bytes, last request, free RAM at allocator failure
before partial-buffer cleanup, error text/location; mem_info/traceback printed
to console. Same payload/block size/reserve, no quiet capacity/rate reduction.
158 host tests pass; next is one targeted L3 diagnosis, archive JSON AND console
under L3_diagnose/. No repeated L1/L2 or blind smaller-block iterations required.

Later L3 result (0.1.3): 35 blocks / 80640 B actually allocated, 36th 2304-B
allocation fails with 79552 B still free. failure_location=block_allocator;
raw logger_ram_2167178_0.json preserved under L3_diagnose/. Strong fragmentation
evidence, exact heap map unavailable (console not provided). 0.1.4 allocates
the whole same buffer BEFORE importing the same app/gps/ms5611/sensor_test/
recording modules, then verifies content and actual >=65536-B reserve after GC.
Compiler/import failure is a separate status and releases buffer before JSON.
free_before_bytes now precedes heavy imports, not comparable with 0.1.3; only
the final free_after_allocation_bytes qualifies reserve. Preloaded module list
is reported; next owner run needs soft reboot and only logger_bench imported.
161 host tests pass. New ordering is not yet board-tested; archive next JSON/
console in L3_frueh/. Future flight entry must preserve early buffer allocation
before app import if this works. No smaller capacity, no flight code enabled.

L3 closure (0.1.4): logger_ram_36572_0.json archived unchanged in L3_frueh/.
All 40 blocks / 91008 B allocated, content verified, no preloaded runtime
modules, all imports completed, 68656 B free (3120 above 64-KiB reserve).
Vorprobe passed; no further isolated L3. Does not qualify real runtime objects.
Owner explicitly chooses 1 Hz for first MANUAL data flights and accessible BOOT.
New logger 0.1.0: flight_start allocates before imports; explicit sensor/manual
profiles only, AUTO_START=False/main unchanged. app optional session after
servo write, included in work/period timing. Separate CH3 Receiver PIO offset,
no auxiliary freshness in control neutral gate. 144-B records/632 slots,
whole segments, full stops logging only, no flash in loop. BOOT released first,
hold 2 s while capture paused for ground shutdown/export. GPS/NeoPixel readiness;
no ready indication from repeated same epoch. Invalid IMU is missing, not frozen
fresh data; reading after latched automation fault never clears that fault.
Export only after PWM/control-PIO/aux-PIO/UART close, pending data retained on
failure and retry guarded by confirmed shutdown. 183 host tests pass.
Next physical step F1 sensor (servos unpowered), then F2 manual, see
docs/FLUGLOGGER_TEST.md. No isolated L1-L3 repeats, no autonomous function,
no standalone logger boot profile or flight qualification yet. Do not assume
the extra 3120 B is all remaining RAM, nor that encoder/objects are already
physically qualified by the older L3 import probe.

F1 result (2026-10-21): flight_327002_0 CSV/JSON archived unchanged under
docs/testdaten/fluglogger/F1_sensor/. Owner tested indoors/at a window. Two
segments, 35 samples + four events, clean ground_button/shutdown_ok, no PWM,
69616 B free after startup objects. No component errors; nevertheless TIMING
latched at 7812 ms, nine periods >50 ms (max 50940 us), work max 50337 us.
Do not read errors={} or the SENSOR mode label as absence/presence of a
sensor fault: first state has empty fault, later TIMING persists. GPS serial
works (920 valid sentences, no parse/checksum/poll gaps) but no fix in this run;
indoor reception is a plausible cause, not a proven device defect. F1 operation/
export passed, integrated timing and outdoor readiness remain open, F2 not run.
Timing trips invalidate control RX and reapply the neutral gate even in MANUAL;
with nonneutral sticks interruption can outlast the single 51-ms interval.
This concrete issue warrants targeted stage timing before F2, without imposing
exactly 100 Hz or revisiting accepted bypass risk. Cause (including possible GC)
is unproven; no per-stage telemetry yet. Do not raise deadline, disable gate,
blindly optimize or repeat L3. Current review changes evidence/docs only.
Next prepare bounded stage timing, then one F1 diagnostic run outdoors with
servos unpowered; preserve JSON/CSV and console in a separate folder. See
docs/testdaten/fluglogger/F1_sensor/AUSWERTUNG.md.

Subsequent 0.1.1 implements that bounded stage timing only for logger SENSOR:
three fixed nine-element arrays, created before the RAM-reserve check; no
per-iteration files/console added. Previous iteration's phases are paired
with the next measured period, including its uninstrumented tail/sleep.
stage_timing exported in JSON after shutdown; normal timing/fault gates remain.
186 host tests pass, including slow-phase attribution/wrap and real-app TIMING.
Next owner action is F1_timing outdoors, not further implementation first:
upload app/diagnostics/flight_logger/config, preserve calibration, soft reboot,
run flight_start.run('sensor'), two captures/pause, BOOT, save both files AND
console. See docs/FLUGLOGGER_TEST.md. MANUAL profile has no active stage probe.

F1_timing 0.1.1 completed indoors: 60.162 s, two segments, ground_button/export
clean, 17 timing trips, max period 53689 us. Worst preceding phases: IMU 30130,
GPS 16347 us; similar ~25-ms maxima in unrelated stages suggest GC but do not
prove it. Baro jumps +174 Pa / -15.35 m at 18.493 s; owner denies touching/
covering/changes, confirms VCC/PS=3V3 and GND/CSB=GND. Cause open, no filter fix.
0.1.2 reuses GPS scratch snapshot (cache coherent pairs separately), removes
per-snapshot helper closure, batches byte counter per received block. 187 host
tests pass; no deadline/gate/GC-mode changes, no measured timing improvement yet.
Next: upload gps/flight_logger/config only from prior 0.1.1, soft reboot, indoor
60-90-s SENSOR comparison, one segment, BOOT; archive F1_vergleich_012 plus
console. Outdoor GPS load remains later; do not require computer outdoors for
this comparison. See docs/testdaten/fluglogger/F1_timing/AUSWERTUNG.md.

0.1.2 comparison archived in F1_vergleich_012: owner moved all axes, then rested.
90.734 s, seven trips/max51355 us, mean66.24 Hz; startup_gc_us=23898. Baro
95763..95770 Pa / -0.243..0.375 m, old 15-m jump not repeated or explained.
0.1.3 schedules GC after output/LED when free heap <32768 B and work <=15 ms,
further limited by measured startup GC +5-ms margin against the SAME deadline.
Busy loops defer it; automatic GC stays enabled, all cost stays in Work/Period,
loop_tail and new JSON runtime_gc. Start reserve/payload unchanged. 189 host
tests pass, including actual GC-method call with simulated 60-ms delay through
app proving TIMING/neutralization. Hardware effect unproven. Next owner action:
upload flight_logger/config only, soft reboot, indoor SENSOR 60-90 s, one
segment/BOOT, save F1_gc_013 plus console. No new calibration/L3; F2 still pending.

0.1.3 failed: Downloads flight_265737_0 copied unchanged into F1_gc_013/.
Orange=GPS MemoryError allocating640, full=false, no segments/CSV rows;
Ctrl+C/shutdown_ok. runtime_gc count0/deferred1566/min_free384. GC starvation
policy bug: per-loop heap scan precedes 15-ms eligibility. 0.1.4 checks time
first, heap query every200 ms, pending GC retries without another scan,
checks actual remaining deadline budget after scan. Automatic GC unchanged,
isenabled now reported. Three new realistic scan-delay tests failed before,
pass after; 192 total. Preserve 64-KiB startup reserve; no inferred hardware
fault/disabled-auto-GC from missing old telemetry. Next upload flight_logger/
config only, soft reboot, SENSOR indoors; archive F1_gc_014 +console. Abort
cleanly on orange and preserve report; do not repeat 0.1.3 unchanged. No F2 yet.

0.1.4 follow-up: flight_68106_0 and flight_62671_0 still fail GPS with
MemoryError allocating640 despite active GC; latest has CH3 capture and no
timing trips over only 18.570 s with GPS disabled early. Preserve raw reports
in F1_gc_014. MicroPython 1.29.0/Unix reproduces the exact error in checked_fields:
text iteration interns characters and expands a QSTR pool on fragmented heap.
0.1.5 uses byte iteration for checksum/ASCII checks; same reproduction passes
without new interned strings. The reported 640 is the pool entry count passed
to m_malloc_fail, not its actual byte allocation. 193 CPython tests pass.
Board failure line is not captured; reproduction strongly explains the symptom,
but board GPS/timing validation remains pending. No more GC-policy changes here.

0.1.5 board follow-up, flight_344020_0: 137.227 s, no component/fault/timing
errors, 1096 checksum-valid GPS sentences/274 updates with no fix, 105 samples
plus start/stop, clean BOOT export. Worst period49.500 ms leaves only0.500 ms
to deadline; no flight timing guarantee. Targeted indoor SENSOR check passed;
next F2 MANUAL ground check, then valid-fix/readiness and intended-duration
checks plus standalone power/start. No firmware change needed for F2.

F2 0.1.5, flight_322120_0: two segments/145 samples, clean export, but control
continuity FAILED. At152784 ms a51.021-ms period triggers TIMING, deliberately
invalidates ALL RC channels and neutralizes all three outputs. Fresh frames
return27 ms later; WAIT_NEUTRAL lasts until157913 ms (5.129-s interruption).
No logged evidence of a particular lost radio channel. Owner also reports
stepped/lagging MANUAL motion, explicitly also with CH3 paused; sensor/attitude
work and GC continue then, so do not attribute it solely to record packing.
Mean loop16.275 ms, PWM50 Hz, GC max24.660 ms;
these support jitter as a hypothesis, not measured end-to-end latency. All
logged MANUAL outputs exactly match configured mapping; no smoothing present.
0.1.6 reuses existing StageTiming for MANUAL too (was SENSOR only), with fixed
fields before unchanged reserve check. It is diagnosis, not a performance fix;
guard/rearm/deadline/gains/pins/capacity unchanged. Existing real-app60-ms-GC
regression now also asserts phase attribution; failed before, passes after.
193 host tests pass. Next: upload app/config only, short MANUAL timing table
run, archive F2_timing_016. Do not repeat F2 0.1.5 or claim flight qualification.

F2 timing0.1.6, flight_385195_0 (2026-10-22): 283.299 s, 218 samples/224 rows,
one timing trip53.154 ms. Worst preceding phase IMU/pose30.284 ms, GPS8.964 ms,
loop_tail1.049 ms: scheduled GC in tail did not cause that worst phase;
automatic GC is plausible but not measured there. At187877 ms IMU_RUNTIME
reports saturation; owner confirms Hawk still, only servos moved. No raw
saturated axis saved, so do not infer fast hand movement or electrical cause.
At191824 ms timing invalidates all RC despite fault label still IMU_RUNTIME;
fresh frames25 ms later, MANUAL192397 ms (573-ms interruption). GPS/exports OK.
0.1.7 reduces allocation in IMU.read/Attitude.update, preserves math/mapping,
range thresholds and guards; caches one first_saturation raw tuple and exports
imu_first_saturation_raw only after shutdown. 196 host tests pass, including
signed boundaries/retention, mixed-axis rotation and MANUAL continuing after
IMU saturation with raw metadata. MicroPython/Unix100-step probe uses31.46%
less temporary heap, not a board timing proof; GC disabled ONLY in host probe.
Next: upload imu/attitude/app/config, soft reboot, MANUAL table comparison
4-5 min (stop on fault), archive F2_vergleich_017. No new calibration/GPS walk.

F2 comparison0.1.7, flight_231333_0: two TIMING trips at19.161/127.166 s,
max51.156 ms; fresh RC after20/19 ms, MANUAL after541/2981 ms. No saturation
this run, GPS/export OK. Raw files/report in F2_vergleich_017/. 0.1.8 changes
only gc_poll_ms200->20 and version: 200-ms checks can miss heap exhaustion
between checks. MicroPython/Unix actual IMU/pose probe:71->0 unplanned heap
increases under simulated scheduling; not board timing proof. New regression
fails old interval/passes new;197 suite tests pass. Guards/GC mode/reserve and
sample capacity unchanged. Owner reports gc.threshold()=-1 after reopening
console; previous-run value unknown. Next: config.py only, soft reboot, short
MANUAL comparison F2_gc_018; no calibration or hardware action by agent.

F2 0.1.8 result, flight_813555_0 (2026-10-22):288.274 s, one segment,
273 samples/275 rows retained; clean BOOT export. No timing/fault/reacquisition
after initial neutral enable; max period45.709 ms, mean19.638 ms (50.92 Hz).
1770 planned GCs/max24.656 ms; minimum queried free heap3328 B, not a leak
proof or continuous reserve.825 recorded MANUAL axis mappings exactly match
source functions. IMU/baro valid, no saturation; GPS2304 valid sentences but
no fix. Targeted F2 continuity/export passed, physical latency/full-fix/10-min
and standalone supply/start still open. No new firmware needed for this result.
See F2_gc_018/AUSWERTUNG.md. Next secure this stand, plan MCU supply/intentional
logger boot without Mac, then combined GPS-ready/10-min two-segment ground run.
Do not imply AUTO_START=True already starts the flight logger.

Owner update2026-10-22: checkpoint8b9adde committed with197 passing tests;
stay on codex/manual-flight-logger for requested standalone logger startup.
0.1.9 adds LOGGER_BOOT_MODE=None/sensor/manual; AUTO_START=False still required
for logger. Optional wait occurs after early buffer/imports/pin validation,
before app hardware. Purple waits for release/2-s-BOOT/release, white confirms,
then normal gyro calibration/RC neutral gate. Reuses GroundStop; no loop change.
JSON start_method is boot_button or explicit.201 host tests, four changed
files compile on MicroPython1.29/Unix; board RAM reserve/start not yet qualified.
Owner chooses regulated BEC5 V at board input for MCU. Before Mac-USB physically
disconnect MCU5 V from BEC/servo rail; battery-off alone can still backfeed from
USB. First B1 in SENSOR with servo supplies disconnected; then MANUAL F3 GPS/
ten-minute two-segment ground test. See docs/BORDSTART_LOGGER.md. Do not flash,
operate hardware, lower reserve or assume Soaring is already implemented.

0.1.9 owner results2026-10-22: two B1 reports plus outdoor SENSOR176.465 s
and MANUAL265.652 s archived; all boot_button, clean export, no faults/trips.
MANUAL after581-ms enable continuous,573 axis mappings exact; all191 rows have
GPS fix/ready,9..12 satellites,HDOP1.01..2.02, no GPS errors/poll gaps. Boot
reserve66992/67088 B verified; electrical rail quality not logged. Owner reports
no felt control outage, uphill walk/hand orientation adjusted to commands.
MANUAL records only190.294 s in two segments (93+94 samples),19.614-s pause;
10-min recording NOT yet tested. No gain/aerodynamic validation from carrying
Hawk, no absolute yaw from slow GPS course. See AUSWERTUNG_019.md. No new
firmware needed; next one10-min combined ground run in final installation,
then reassess first MANUAL data flight. Owner now explicitly authorizes the
0.1.9 checkpoint commit with these test reports; stay on the same branch.

## Working boundaries

Owner request2026-10-25: implement compact20-Hz response logging on
codex/response-logger-20hz, branched from8f6ed38. Logger0.2.0 adds optional
response_log.py; LOGGER_PROFILE=response20 or snapshot1. Both buffers reserved
before large imports;1800*36+132*144=83808 B in response20, unchanged64-KiB
start reserve. Angles0.01deg, gyro/RX/command20Hz target; full snapshots1Hz.
CH3 pauses both, capacity stops logging only, export both CSVs after hardware
stop. Timestamps are logger-entry times, not sensor/servo capture measurements.
Keep AUTO_START=False,
LOGGER_BOOT_MODE=None and all pins/gains/signs/guards unchanged.

0.2.0 board results2026-10-25: R1 SENSOR55.215 s/608 fast samples; R2 MANUAL
210.197 s/1800 fast samples, three segments totalling89.987 s capture and FULL.
All six files reconciled; no faults/trips/errors, clean ground_button export,
5679 MANUAL axis commands match calibration/source. After597-ms enable no
RC rearm; control continues25.923 s after FULL. Owner reports no felt control
irregularities. Fast intervals12..92/13..93 ms, mean50.025/50.014 ms; zero
missed raster slots, not uniform sampling. Startup free65616/65632 B exceeds
65536 by only80/96 B; do not lower reserve or assume more code fits.
Both runs explicit start and NO GPS fix/used satellites, despite clean NMEA.
No full-fix20-Hz or0.2.0 boot_button validation yet. Next one combined outdoor
MANUAL/BOOT run with GPS-ready and60..90 s capture in intended installation,
then assess first MANUAL data flight. No firmware fix indicated by these logs.
See docs/testdaten/fluglogger/AUSWERTUNG_020.md; preserve raw files.

R3 result2026-10-25 supersedes that open GPS/boot item: boot_button MANUAL,
250.492 s, two capture segments totalling89.978 s,1800 fast rows/93 full rows,
19.996 Hz, zero missed raster slots, no timing trips/rearm after560-ms enable.
All93 full rows GPS-fix/ready (6..12 sats,HDOP0.93..1.69,age<=1072 ms), no GPS
errors/poll gaps.5679 axis commands match source/calibration; clean FULL/BOOT
export,66624 B startup free. NOT fault-free: IMU_RUNTIME at211.294 s app time;
first raw(-10350,5302,32767,-1727,3133,-11169,5340) clips acc-Z in configured
2g range. Nine fast rows IMU-invalid/blank, manual RX/PWM remain valid; fault
latches while later IMU samples recover. CSV origin is78 ms before app origin.
Owner reports frequent vigorous movement, exact fault moment uncertain; motion
is plausible, not proven cause. Keep limits/gains unchanged; review IMU range
before stabilization/navigation. No logger fix indicated. Next secure commit,
finish installation/model checks, short MANUAL data flight; no identical GPS
ground repeat required. See R3_response20_manual_gps/AUSWERTUNG.md. No commit
authorization inferred from the test report; preserve all raw files.

Owner approval2026-10-25: commit the0.2.0 implementation plus R1..R3 evidence,
then branch directly from that checkpoint for20-Hz MANUAL flight-test work.
Owner asks to assess limited elevator/rudder travel before flight. Current
SERVOS limits are roll200 us, pitch/yaw150 us, used in MANUAL too. No measured
safe replacement limits or exact airframe recommendations yet; do not infer
mechanical clearance from pulse conventions. Keep tested firmware unchanged
for this checkpoint; flight preparation belongs on the new branch.

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
