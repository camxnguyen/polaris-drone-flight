import subprocess
import json
import time

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

# main
if __name__ == "__main__":
    modem = get_modem_index()
    print(f"Using modem index: {modem}")

    enable_modem(modem)

    # tiny delay just to let signal reporting populate
    time.sleep(1)

    rssi, rsrp, rsrq, snr = read_signal(modem)

    print("Cell metrics:")
    print(f"  RSSI: {rssi} dBm")
    print(f"  RSRP: {rsrp} dBm")
    print(f"  RSRQ: {rsrq} dB")
    print(f"  SNR:  {snr} dB")