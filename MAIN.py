import subprocess
import time

# config / thresholds
POLL_INTERVAL_SEC = 2.0     # how often to pull signal metrics
POOR_DURATION_SEC = 30.0    # how long signal must be down before we trigger launch
POOR_SAMPLES_REQ = int(POOR_DURATION_SEC / POLL_INTERVAL_SEC)   # number of consecutive bad samples needed
RSRP_THRESH = -100.0        # reference signal received power
RSRQ_THRESH = -15.0         # reference signal received quality
SNR_THRESH = 7.0            # signal to noise ratio

# run shell command
def run(cmd): 
    return subprocess.check_output(cmd, shell=True, text=True).strip()

# get modem index automatically
def get_modem_index():
    out = run("mmcli -L")
    for line in out.splitlines():
        if "Modem/" in line:
            after = line.split("Modem/")[1]   
            token = after.split()[0]         
            idx = ''.join(c for c in token if c.isdigit())
            return idx
    raise Exception("No modem detected")


# enable modem signal reporting
def enable_modem(modem):
    print(f"[+] Enabling modem {modem}...")
    try: run(f"mmcli -m {modem} --enable")
    except: print("    (already enabled)")

    time.sleep(1)

    print(f"[+] Setting up signal reporting...")
    try: run(f"mmcli -m {modem} --signal-setup=1")
    except: print("    (signal reporting may already be active)")

# get cell signal metrics
def read_signal(m):
    out = run(f"mmcli -m {m} --signal-get")
    rssi = rsrp = rsrq = snr = None

    for line in out.splitlines():
        line = line.strip().lower()
        if "rssi:" in line: rssi = float(line.split("rssi:")[1].split()[0])
        if "rsrp:" in line: rsrp = float(line.split("rsrp:")[1].split()[0])
        if "rsrq:" in line: rsrq = float(line.split("rsrq:")[1].split()[0])
        if "s/n:" in line or "snr:" in line:
            snr = float(line.split(":")[1].split()[0])

    return rssi, rsrp, rsrq, snr

# detect poor signal
def is_poor_signal(rsrp, rsrq, snr):
    reasons = []
    if rsrp is not None and rsrp < RSRP_THRESH:
        reasons.append(f"RSRP={rsrp} dBm < {RSRP_THRESH}")
    if rsrq is not None and rsrq < RSRQ_THRESH:
        reasons.append(f"RSRQ={rsrq} dB < {RSRQ_THRESH}")
    if snr is not None and snr < SNR_THRESH:
        reasons.append(f"SNR={snr} dB < {SNR_THRESH}")

    return (len(reasons) > 0), reasons

def trigger_launch():
    print("\n Poor signal peristed - sending LAUNCH command")

# main
if __name__ == "__main__":
    modem = get_modem_index()
    print(f"Using modem index: {modem}")

    enable_modem(modem)

    time.sleep(1)       # tiny delay just to let signal reporting populate
    start_time = None
    poor_count = 0      # consecutive samples with poor signal
    total_readings = 0  
    history = []        # store all poor samples for summary
    #start_time = None   

    try:
        while True:
            rssi, rsrp, rsrq, snr = read_signal(modem)
            total_readings += 1

            if start_time is None:
                start_time=time.time()

            timestamp = time.strftime("%H:%M:%S")
            print(f"\n[{timestamp}] Cell metrics:")
            print(f"  RSSI: {rssi} dBm      RSRP: {rsrp} dBm        RSRQ: {rsrq} dB         SNR:  {snr} dB")

            is_poor, reasons = is_poor_signal(rsrp, rsrq, snr)

            if is_poor:
                poor_count += 1

                # save history entry
                history.append({
                    "RSSI": rssi,
                    "RSRP": rsrp,
                    "RSRQ": rsrq,
                    "SNR": snr,
                    "reasons": reasons.copy(),
                    "timestamp": time.strftime("%H:%M:%S")
                })

                print(f"  -> Signal classified as POOR (#{poor_count} / {POOR_SAMPLES_REQ})")
                print("     Reasons:")
                for r in reasons:
                    print("      -", r)

                if poor_count >= POOR_SAMPLES_REQ:
                    trigger_launch()
                    poor_count = 0
                    
            else:
                if poor_count > 0:
                    print("  -> Signal recovered, resetting poor signal counter.")
                poor_count = 0

            time.sleep(POLL_INTERVAL_SEC)

    except KeyboardInterrupt:
        end_time = time.time()
        if start_time is not None:
            total_seconds = int(end_time - start_time)
        else:
            total_seconds = 0

        hrs, rem = divmod(total_seconds, 3600)
        mins, secs = divmod(rem, 60)

        print("\n==================== SUMMARY ====================")
        print(f"   Runtime (active monitoring): {hrs:02d}:{mins:02d}:{secs:02d}")
        print(f"   Total signal readings:       {total_readings}")
        print(f"   Poor-signal readings:        {len(history)}\n")

        for i, h in enumerate(history, 1):
            print(f"[{i}] Time: {h['timestamp']}")
            print(f"     RSSI={h['RSSI']} / RSRP={h['RSRP']} / "
                  f"RSRQ={h['RSRQ']} / SNR={h['SNR']}")
            print("     Reasons:")
            for r in h["reasons"]:
                print(f"       - {r}")
            print()

        print("=================================================\n")
        print("[+] Monitoring stopped by user.\n")
