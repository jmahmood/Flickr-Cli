from ConfigParser import ConfigParser
import webbrowser
import flickrapi
import flickr_cli
import unittest
import os.path

__author__ = 'jawaad'

import requests.packages.urllib3
requests.packages.urllib3.disable_warnings()


class TestSuccessfulUploads(unittest.TestCase):
    """
    Currently the repository for all tests related to flickr_up.
    """
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    def path(self, relative_path):
        """Get paths relative to the test script file"""
        return os.path.join(self.BASE_DIR, relative_path)

    def setUp(self):
        """
        Setup API key / Flickr Token for additional logins.
        :return:
        """
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
        """
        Test normal upload using DirectoryFlickrUpload
        TODO: Check file private/non-family status
        :return:
        """
        upload = flickr_cli.DirectoryFlickrUpload(self.flickr)
        upload(directory='./test_img/', pset=['test-0001'], tags=['tests'])
        self.assertEqual(upload.successful_uploads_count, 1)

    def test_upload_public(self):
        """
        Test public file upload using PublicDirectoryUpload
        TODO: Check file public status
        :return:
        """
        public_upload = flickr_cli.PublicDirectoryUpload(self.flickr)
        public_upload(directory='./test_img/', pset=['test-0001'], tags=['tests'])
        self.assertEqual(public_upload.successful_uploads_count, 1)

    def test_upload_family(self):
        """
        Test public file upload using PublicDirectoryUpload
        TODO: Check file family status
        :return:
        """
        family_upload = flickr_cli.FamilyDirectoryUpload(self.flickr)
        family_upload(directory='./test_img/', pset=['test-0001'], tags=['tests'])
        self.assertEqual(family_upload.successful_uploads_count, 1)

    def test_filter_bad_images(self):
        """
        Ensure that bad images / invalid types get filtered out of the list of uploaded files.
        :return:
        """
        self.assertFalse(flickr_cli.valid_img({}))
        self.assertFalse(flickr_cli.valid_img(self.path('./non_existant_file.png')))
        self.assertTrue(flickr_cli.valid_img(self.path('./test_img/actual_image.jpg')))

    def test_upload_status(self):
        """
        Ensure that UploadStatus works as expected wrt how it documents file uploads.
        TODO: What about OSes where the files are not sorted in alphabetical order?  Does this matter really?
        TODO: How does it handle failed files?
        :return:
        """
        a = flickr_cli.UploadStatus(self.path('./test_img/'))
        self.assertEqual(a.uploaded_thus_far(), 0.0) # actual_image.jpg
        a.increment()  # first file done uploading
        self.assertEqual(a.uploaded_thus_far(), 198167.0)
        self.assertAlmostEqual(a.status(0), 100 * 198167.0 / 198241.0, 2)
        a.increment()  # second file done uploading
        self.assertEqual(a.uploaded_thus_far(), 198241.0)
        self.assertEqual(a.status(0), 100.00)

if __name__ == '__main__':
    unittest.main()
