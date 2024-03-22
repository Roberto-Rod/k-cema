ADDR1="0x40030000"
ADDR2="0x40030004"
DATA="0x00000000"

if [ "$1" = '0' ]; then
    ADDR1="0x40030000"
    ADDR2="0x40030004"
elif [ "$1" = '1' ]; then
    ADDR1="0x40030008"
    ADDR2="0x4003000C"
elif [ "$1" = '2' ]; then 
    ADDR1="0x40030010"
    ADDR2="0x40030014"
fi

if [ "$2" = '0' ]; then
    DATA="0x00000000"
elif [ "$2" = '1' ]; then
    DATA="0xFFFFFFFF"
fi

devmem $ADDR1 32 $DATA
devmem $ADDR2 32 $DATA
