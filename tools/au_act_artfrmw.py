
from au_action import AxAction, AxJob

import artemis_svl

#--------------------------------------------------------------------------------------
# action testing
class AUxArtemisUploadFirware(AxAction):

    ACTION_ID = "artemis-upload-firmware"
    NAME = "Artemis Firmware Upload"

    def __init__(self) -> None:
        super().__init__(self.ACTION_ID, self.NAME)

    def run_job(self, job:AxJob):

        try:
            artemis_svl.upload_firmware(job.file, job.port, job.baud)

        except Exception:
            return 1

        return 0

