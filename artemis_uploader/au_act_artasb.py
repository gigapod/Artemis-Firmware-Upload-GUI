


from .au_action import AxAction, AxJob
from .asb import main as asb_main
import tempfile
import sys
#--------------------------------------------------------------------------------------
# Artemis Boot loader burn action
class AUxArtemisBurnBootloader(AxAction):

    ACTION_ID = "artemis-burn-bootloader"
    NAME = "Artemis Bootloader Upload"

    def __init__(self) -> None:
        super().__init__(self.ACTION_ID, self.NAME)

    def run_job(self, job:AxJob):

        # fake command line args - since the apollo3 bootloader command will use
        # argparse 
        sys.argv = ['./asb/asb.py', \
                    "--bin", job.file, \
                    "-port", job.port, \
                    "-b", str(job.baud), \
                    "-o", tempfile.gettempdir(), \
                    "--load-address-blob", "0x20000", \
                    "--magic-num", "0xCB", \
                    "--version", "0x0", \
                    "--load-address-wired", "0xC000", \
                    "-i", "6", \
                    "-clean", "1" ]

        # Call the ambiq command
        asb_main()
