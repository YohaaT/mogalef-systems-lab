# Phase 2 Parallel Execution - Opción A

## Overview

Phase 2 optimization distributed across **2 servers running in parallel**:
- **TANK** (local, 192.168.1.162): 8 cores
- **VPS BO** (remote, 79.72.62.202): ? cores (checking...)

**Execution Strategy:**

```
TANK                           VPS BO
════════════════════════════════════════════════════════════════
Phase 2a Block 1 ────────┐     Phase 2a Block 2
  (60 combos)            │       (90 combos)
  ~5 min                 ├─ SYNC ─→ ~8 min
                         │
Phase 2a Consolidate ←────┴─→ (Both blocks done)
  (150 combos)
  ~1 min

Phase 2b ────────────┐         Phase 2c
(6 profiles)         ├─ SYNC ─→ (5 bands)
~3 min               │         ~3 min

Final Consolidate ◄──┴─────────→
(2a+2b+2c)
~1 min

⏱️ TOTAL TIME: ~8-10 minutes (vs 20-25 sequential)
```

---

## Quick Start

### Single Command (Automated)

```bash
cd "C:\Users\Yohanny Tambo\Desktop\Bo_Oracle\mogalef-systems-lab\mgf-control"
bash phase2_parallel_coordinator.sh
```

This will:
1. ✓ Check connectivity to both servers
2. ✓ Upload coordinator scripts
3. ✓ Launch TANK and VPS in parallel
4. ✓ Monitor progress in real-time
5. ✓ Download final results
6. ✓ Display summary

---

## Manual Execution (Step-by-Step)

### Option 1: Launch from Windows (Easier)

```powershell
# From Windows (same directory)
wsl bash phase2_parallel_coordinator.sh
```

### Option 2: SSH to Servers Directly

**Terminal 1 - TANK:**
```bash
ssh tank
cd ~/phase2_work
bash phase2_parallel_tank.sh
```

**Terminal 2 - VPS BO:**
```bash
ssh bo
cd ~/phase2_parallel
bash phase2_parallel_vps.sh
```

Monitor both windows for progress.

---

## What Gets Executed

### TANK Server
1. **Phase 2a Block 1** (60 combos)
   - trend_r1 = [1, 2]
   - Time: ~5 min

2. **Waits** for VPS Block 2 completion (synchronization point)

3. **Phase 2a Consolidation** (merge blocks 1+2)
   - Time: ~1 min

4. **Phase 2b: Horaire** (6 UTC hour profiles)
   - Options: [0-23], [9-15], [9-17], [8-16], [9-12], [12-15]
   - Time: ~3 min

5. **Waits** for VPS Phase 2c completion

6. **Final Consolidation** (merge 2a+2b+2c into phase2_best_params.json)
   - Time: ~1 min

### VPS BO Server
1. **Phase 2a Block 2** (90 combos)
   - trend_r1 = [3, 4, 5]
   - Time: ~8 min

2. **Signals** TANK that Block 2 is done

3. **Waits** for Phase 2a consolidation from TANK

4. **Phase 2c: Volatility** (5 ATR bands)
   - Options: (0,500), (10,500), (0,200), (10,250), (20,200)
   - Time: ~3 min

5. **Signals** TANK that 2c is done

---

## File Structure

### On TANK (192.168.1.162)
```
~/phase2_work/
├── YM_phase_A_clean.csv
├── YM_phase_B_clean.csv
├── COMB_001_TREND_V1_vectorized.py
├── phase1_best_params.json
├── phase2a_trend_optimization_block_runner_vec.py
├── phase2b_horaire_optimization.py
├── phase2c_volatility_optimization.py
├── phase2a_consolidate_blocks.py
├── phase2_combine_results.py
├── phase2_parallel_tank.sh
└── [outputs will be created here]
```

### On VPS BO (79.72.62.202)
```
~/phase2_parallel/
├── YM_phase_A_clean.csv
├── YM_phase_B_clean.csv
├── COMB_001_TREND_V1_vectorized.py
├── phase1_best_params.json
├── phase2a_trend_optimization_block_runner_vec.py
├── phase2b_horaire_optimization.py
├── phase2c_volatility_optimization.py
├── phase2_parallel_vps.sh
└── [outputs will be created here]
```

---

## Expected Output Files

### On TANK (final consolidated results)
```
phase2a_trend_optimization_block_1_log.csv
phase2a_trend_optimization_block_1_best_params.json
phase2a_trend_optimization_block_1_top10.csv

phase2a_trend_optimization_block_2_log.csv        [from VPS]
phase2a_trend_optimization_block_2_best_params.json
phase2a_trend_optimization_block_2_top10.csv

phase2a_trend_full_log.csv                        [150 combos]
phase2a_trend_best_params.json

phase2b_horaire_optimization_log.csv
phase2b_horaire_best_params.json

phase2c_volatility_optimization_log.csv           [from VPS]
phase2c_volatility_best_params.json

phase2_best_params.json                           ← FINAL
phase3_summary.json                               ← READY FOR PHASE 3
```

---

## Monitoring Progress

### Real-time Monitoring via Coordinator

The coordinator script shows live progress:
```
[08:32] TANK: Running (2a Block 1)     | VPS: Running (2a Block 2)
[08:37] TANK: ✓ Completed (2a-B1)      | VPS: Running (2a Block 2)
[08:45] TANK: Running (2a Consolidate) | VPS: ✓ Completed (2a-B2)
[08:46] TANK: Running (2b Horaire)     | VPS: Running (2c Volatility)
[08:49] TANK: ✓ Completed (2b)         | VPS: ✓ Completed (2c)
[08:50] TANK: Running (Final Consolidate)
[08:51] TANK: ✓ COMPLETE
```

### Manual Monitoring

Check log files:
```bash
# TANK progress
tail -f phase2_tank_*.log

# VPS progress
ssh bo "tail -f ~/phase2_parallel/phase2_parallel_vps.sh.log"
```

Check specific phase outputs:
```bash
# On TANK
ssh tank "ls -lh ~/phase2_work/phase2*.json"

# On VPS
ssh bo "ls -lh ~/phase2_parallel/phase2*.json"
```

---

## Synchronization Points

The scripts use **lock files** for coordination:

1. **VPS Block 2 Done → TANK**
   - VPS creates: `/tmp/phase2_block2_done.lock`
   - TANK waits for this lock before consolidating

2. **TANK Phase 2a Consolidation → VPS**
   - VPS polls for: `phase2a_trend_best_params.json`
   - VPS uses `scp` to retrieve file from TANK

3. **TANK Phase 2b Done → VPS**
   - VPS polls for: `phase2b_horaire_best_params.json`
   - VPS uses `scp` to retrieve file

4. **VPS Phase 2c Done → TANK**
   - VPS creates: `/tmp/phase2c_done.lock`
   - TANK waits for this lock before final consolidation

5. **Final Results → Local**
   - Coordinator `scp` downloads results from TANK

---

## Troubleshooting

### Script Fails to Start

```bash
# Check SSH connectivity
ssh tank "echo 'Tank online'"
ssh bo "echo 'VPS online'"

# Check scripts are executable
ssh tank "ls -l ~/phase2_work/phase2_parallel_tank.sh"
ssh bo "ls -l ~/phase2_parallel/phase2_parallel_vps.sh"
```

### Block Doesn't Complete

```bash
# Check TANK logs
ssh tank "tail -50 ~/phase2_work/phase2_parallel_tank.sh.log"

# Check VPS logs
ssh bo "tail -50 ~/phase2_parallel/phase2_parallel_vps.sh.log"

# Check specific phase output
ssh tank "cat ~/phase2_work/phase2a_trend_optimization_block_1_log.csv | wc -l"
```

### Files Not Synchronized

```bash
# Check if lock files exist
ssh tank "ls /tmp/phase2_*.lock"
ssh bo "ls /tmp/phase2_*.lock"

# Manually copy missing file
scp tank:~/phase2_work/phase2a_trend_best_params.json .
scp bo:~/phase2_parallel/phase2c_volatility_best_params.json tank:~/phase2_work/
```

### Phase 2c Fails (Missing Params)

If Phase 2c fails because it's waiting for TANK results:
1. Check TANK Phase 2a/2b completion
2. Manually copy files to VPS:
   ```bash
   scp tank:~/phase2_work/phase2a_trend_best_params.json bo:~/phase2_parallel/
   scp tank:~/phase2_work/phase2b_horaire_best_params.json bo:~/phase2_parallel/
   ```
3. Restart VPS script

---

## Performance Estimate

### Wall-Clock Time (Elapsed)
- **Phase 2a Block 1 + Block 2 (parallel):** 8 min (slowest of the two)
- **Phase 2a Consolidation:** 1 min
- **Phase 2b + Phase 2c (parallel):** 3 min (slowest of the two)
- **Final Consolidation:** 1 min
- **Total:** **~8-10 minutes**

### vs Sequential
- Sequential: 20-25 minutes
- **Speedup:** 2.5-3x faster

### CPU Utilization
- TANK: 4-8 cores active (~50-100% utilization during phase 2a/2b)
- VPS: 4-8 cores active (~50-100% utilization during phase 2a/2c)
- Total: Both servers working simultaneously = 8-16 combined cores

---

## Success Criteria

✓ Both TANK and VPS scripts complete without errors  
✓ All robustness values ≥ 0.80  
✓ phase2_best_params.json generated on TANK  
✓ phase3_summary.json ready for Phase 3  
✓ Total execution time ≤ 15 minutes  

---

## Next Steps After Phase 2

1. **Review Results**
   ```bash
   cat phase2_best_params.json
   cat phase3_summary.json
   ```

2. **Prepare Phase 3**
   - Create `phase3_exits_optimization_block_runner_vec.py`
   - Optimize: target_atr_multiplier × timescan_bars (4×4 = 16 combos)

3. **Archive Phase 2 Results**
   ```bash
   mkdir -p phase2_results
   scp -r tank:~/phase2_work/phase2a_*.csv phase2_results/
   scp -r tank:~/phase2_work/phase2b_*.csv phase2_results/
   scp -r tank:~/phase2_work/phase2c_*.csv phase2_results/
   ```

---

## Commands Reference

### Start Phase 2 Parallel
```bash
bash phase2_parallel_coordinator.sh
```

### Check Status (during execution)
```bash
ssh tank "ps aux | grep phase2"
ssh bo "ps aux | grep phase2"
```

### Get Logs
```bash
cat phase2_tank_*.log
cat phase2_vps_*.log
```

### Download Results Manually
```bash
scp tank:~/phase2_work/phase2_best_params.json .
scp tank:~/phase2_work/phase3_summary.json .
scp tank:~/phase2_work/phase2a_trend_full_log.csv .
scp tank:~/phase2_work/phase2b_horaire_optimization_log.csv .
scp bo:~/phase2_parallel/phase2c_volatility_optimization_log.csv .
```

---

## SSH Config Required

Ensure your `~/.ssh/config` has both hosts:

```
Host tank
    HostName 192.168.1.162
    User ytambo

Host bo
    HostName 79.72.62.202
    User ubuntu
    IdentityFile "C:\Users\Yohanny Tambo\.ssh\B_O.key"
```

---
