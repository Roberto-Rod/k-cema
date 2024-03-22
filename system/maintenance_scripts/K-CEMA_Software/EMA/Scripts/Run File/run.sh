export APP_ROOT=/run/media/mmcblk0p1
export FILE_ROOT=/run/media/mmcblk0p2
export LD_LIBRARY_PATH=/usr/local/lib/Boost:/usr/local/lib/OpenSSL:/usr/local/lib/OpenDDS
${FILE_ROOT}/KCemaEMAApp -DCPSConfigFile ${FILE_ROOT}/rtps.ini
if [ $? == 0 ]; then
    poweroff
fi
