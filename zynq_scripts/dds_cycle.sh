while true; do
	./dds_cw_400MHz_+5dBm.sh
	sleep 1
	./dds_cw_600MHz_+5dBm.sh
	sleep 1
	./dds_cw_800MHz_+5dBm.sh
	sleep 1
	./dds_cw_1000MHz_+5dBm.sh
	sleep 1
	./dds_cw_1200MHz_+5dBm.sh
	sleep 1
	./dds_cw_1400MHz_+5dBm.sh
	sleep 1
done
