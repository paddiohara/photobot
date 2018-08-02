from onvif import ONVIFCamera
import requests
from requests.auth import HTTPDigestAuth
import shutil
from datetime import datetime

import logging
log = logging.getLogger(__name__)
import pdb

class LorexCam(object):

    def __init__(self, **settings):
        self._host = settings['host']
        self._port = settings['port']
        # default to the out of box lorex user/pass combo
        self._user = settings.get('user', 'admin')
        self._password = settings.get('password', 'admin')
        self._wsdl_dir = settings.get('wsdl_dir', './wsdl')

        self._cam = ONVIFCamera(self._host, self._port, self._user,
            self._password, self._wsdl_dir)
        # Create media service object and save media profile
        # this is copied from the onvif examples
        media = self._cam.create_media_service()
        profiles = media.GetProfiles()
        self._media_profile = profiles[0]
        self._media_service = media

    def _get_snaphot_uri(self):
        "method to return the uri for saving a snapshot from the camera"
        request = self._media_service.create_type('GetSnapshotUri')
        request.ConfigurationToken = self._media_profile.VideoSourceConfiguration._token
        snapshot_uri_obj = self._media_service.GetSnapshotUri({
            'ProfileToken': self._media_profile._token})
        snapshot_uri = snapshot_uri_obj['Uri']
        return snapshot_uri

    def save_image(self, filename):
        "save an image from the camera to filename"
        snapshot_uri = self._get_snaphot_uri()
        res = requests.get(snapshot_uri, auth=HTTPDigestAuth(self._user, self._password), stream=True)
        if res.status_code == 200:
            with open(filename, 'wb') as f:
                res.raw.decode_content = True
                shutil.copyfileobj(res.raw, f)
            log.info("Image saved to %s" % filename)
        else:
            print("ERROR saving file, response: %s" % res)


if __name__ ==  "__main__":
    print("Running test of lorex camera...")
    # test expects there to be a symlink in this directory for the wsdl path
    lorex_cam = LorexCam(
        host = '192.168.1.65',
        port = 80,
        user = 'admin',
        password = 'admin',
        wsdl_dir = '/Users/iainduncan/Sites/patrick/lorex/env/wsdl/'
    )
    filename = "lorex_test_capture_-_%s.jpg" % datetime.now().isoformat()
    lorex_cam.save_image(filename)
    print("Done, image saved to %s" % filename)