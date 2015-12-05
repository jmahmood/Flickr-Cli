from ConfigParser import ConfigParser
import webbrowser
import flickrapi
import flickr_cli
import unittest

__author__ = 'jawaad'

import requests.packages.urllib3
requests.packages.urllib3.disable_warnings()


class TestSuccessfulUploads(unittest.TestCase):
    def setUp(self):
        config = ConfigParser()
        config.read('flickr.config')
        api_key = config.get('flickr', 'key')
        secret = config.get('flickr', 'secret')
        self.flickr = flickrapi.FlickrAPI(api_key, secret)
        # Only do this if we don't have a valid token already
        if not self.flickr.token_valid(perms=u'write'):
            # Get a request token
            self.flickr.get_request_token(oauth_callback=u'oob')
            # Open a browser at the authentication URL. Do this however
            # you want, as long as the user visits that URL.
            authorize_url = self.flickr.auth_url(perms=u'write')
            webbrowser.open_new_tab(authorize_url)
            # Get the verifier code from the user. Do this however you
            # want, as long as the user gives the application the code.
            verifier = unicode(raw_input('Verifier code: '))
            # Trade the request token for an access token
            self.flickr.get_access_token(verifier)

    def test_upload(self):
        upload = flickr_cli.DirectoryFlickrUpload(self.flickr)
        upload(directory='./test_img/', pset=['test-0001'], tags=['tests'])
        # print repr(upload.successful_uploads_count)
        self.assertEqual(upload.successful_uploads_count, 1)

    def test_upload_family(self):
        family_upload = flickr_cli.FamilyDirectoryUpload(self.flickr)
        family_upload(directory='./test_img/', pset=['test-0001'], tags=['tests'])
        # print repr(family_upload.successful_uploads_count)
        self.assertEqual(family_upload.successful_uploads_count, 1)

if __name__ == '__main__':
    unittest.main()
