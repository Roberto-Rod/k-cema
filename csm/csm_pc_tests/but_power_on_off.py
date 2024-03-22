import sys
from csm_test_jig_intf import CsmTestJigInterface


def main(argv):
    """
    Sets the CSM Motherboard GPIO1 register to assert/de-assert the
    RF_MUTE signals based on the passed command line argument
    :param argv: argv[1]: '0' = de-assert; non-zero assert
    :return: None
    """
    ctji = CsmTestJigInterface("COM5")

    if len(argv) == 1:
        if int(sys.argv[1]):
            ctji.toggle_rcu_power_button()
            print("Turning Board On")
        else:
            ctji.toggle_rcu_power_button(hard_power_off=True)
            print("Turning Board Off")
    else:
        print("Invalid number of command line arguments!")


# -----------------------------------------------------------------------------
# RUNTIME PROCEDURE
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    """
    Run main() routine
    """
    main(sys.argv[1:])
