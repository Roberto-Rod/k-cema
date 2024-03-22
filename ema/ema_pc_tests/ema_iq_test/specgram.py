import numpy as np
import matplotlib.pyplot as plt
from numpy.fft import fft, fftshift, fftfreq
import seaborn as sns

FILENAME1="D:/TS_OR10_CH01_00001.iq"
#FILENAME2="D:/TS_OR10_V2_CH01_00016.iq"
FFT_SIZE = 512
NFFTS = 8
NSAMPLES = int(FFT_SIZE*NFFTS)  # Use -1 for full file
RATE_SPS = 5760000
CENTRE_HZ = 895000000

samples1 = np.fromfile(FILENAME1, dtype=np.float32)
#samples2 = np.fromfile(FILENAME2, dtype=np.float32)
iq1 = (samples1[::2] + 1j*samples1[1::2])  # convert to IQIQIQ...
#iq2 = (samples2[::2] + 1j*samples2[1::2])  # convert to IQIQIQ...

START=FFT_SIZE*1024
f1=fft(iq1[START:START+FFT_SIZE]*np.blackman(FFT_SIZE))
#f2=fft(iq2[START:START+FFT_SIZE]*np.blackman(FFT_SIZE))
x=fftfreq(FFT_SIZE)
spec1=20*np.log10(np.abs(f1))
#spec2=20*np.log10(np.abs(f2))

sns.set_style('darkgrid')
fig, ax = plt.subplots()
ax.plot(x, spec1)
#ax.plot(x, spec2)
ax.grid(True)
ax.set_xlabel("Frequency Offset (MHz)\nfc = {} MHz".format(CENTRE_HZ/1e6))
ax.set_ylabel("Power (dBm)")
ax.set_ylim(-60, 60)
plt.show()