from datetime import datetime
import sys_test_ipam_set_mute
import sys_test_full_power_tone
import sys_test_ipam_get_temperature
import sys_test_ipam_get_rf_power

start = 20e6
stop = 520e6
step = 1e6

mute = sys_test_ipam_set_mute.SysTestIPAMSetMute()
tone = sys_test_full_power_tone.SysTestFullPowerTone()
temp = sys_test_ipam_get_temperature.SysTestIPAMGetTemperature()
rfpwr = sys_test_ipam_get_rf_power.SysTestIPAMGetRFPower()

iso_date = datetime.now().isoformat()
file = open("{}_pwr_mon.csv".format(iso_date), "w")
file.write("Forward,Reverse,Difference\n")

for f in range(int(start), int(stop+step), int(step)):
    mute.set_mute(True)
    print("{} MHz".format(float(f)/1e6))
    tone.set_tone(f)    
    mute.set_mute(False)
    temp.get_temperature()
    ok, error_msg, rf = rfpwr.get_rf_power()
    if ok:
        fwd = int(rf["fwd"])
        rev = int(rf["rev"])
        diff = fwd - rev
        print("Power Monitor Fwd: {}, Rev: {}, Diff: {}".format(fwd, rev, diff))
        file.write("{},{},{}\n".format(fwd, rev, diff))
    else:
        print(error_msg)
