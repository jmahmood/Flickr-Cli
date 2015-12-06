# encoding: utf8
# !/usr/bin/env python
import logging
import os.path
import imghdr


def valid_img(f):
    """
    Is this a valid image that we can use to upload?

    :param f: str that indicates the file directory.
    :return: boolean
    """
    try:
        file_type = imghdr.what(f)
        supported_types = ['jpeg', 'gif', 'png']
        if file_type in supported_types:
            return True
    except AttributeError as e:
        # You probably passed something that is not a path.
        logging.warning(e)
    except IOError as e:
        # You passed a path that does not exist, or you do not have access to it.
        logging.warning(e)
    return False


def get_upload_size(files):
    """
    Size of all files in a list.
    :param files:
    :return:
    """
    return sum([os.path.getsize(f) for f in files])


class UploadStatus(object):
    """Used to maintain state while performing uploads."""
    # TODO: Is this actually being used?

    def __init__(self, file_list):
        if isinstance(file_list, basestring):
            # The file list is a directory and should be converted into a directory list.
            file_list = [os.path.join(file_list, f)
                         for f in os.listdir(file_list)
                         if not os.path.isdir(os.path.join(file_list, f))]

        self.file_list = file_list
        self.total_upload_size = get_upload_size(self.file_list)
        self._file_no = 0
        self.file = self.get_current_file()

    def increment(self):
        """
        Select the next file in the list
        :return:
        """
        try:
            self._file_no += 1
            self.file = self.get_current_file()
            return self.file
        except IndexError:
            return None

    def get_current_file(self):
        """
        What is the file that is currently selected?  Used to fill the self.file variable.
        :return:
        """
        return self.file_list[self._file_no]

    def uploaded_thus_far(self):
        """
        Total file size for files uploaded thus far.
        :return:
        """
        return float(get_upload_size(self.file_list[0:self._file_no]))

    def status(self, progress):
        """
        Progress: Float: How much of the currently uploading file has been uploaded.
        """
        total = self.uploaded_thus_far() + float(progress * os.path.getsize(self.file)) / 100
        return round(total / self.total_upload_size * 100, 2)


class Photoset(object):
    """
    Object that helps organize photos into sets.

    Arguments
    flickr: A FlickrAPI object that grants access to your flickr API.
    """
    def __init__(self, flickr):
        self.flickr = flickr
        self.photoset_id = ''

    def exists(self, title):
        """Returns Photoset ID that matches title, if such a set exists.  Otherwise false."""
        # TODO: What happens if there is no photoset in your account?
        photosets = self.flickr.photosets_getList().find("photosets").findall("photoset")

        for p in photosets:
            if p.find("title").text == title:
                return p.attrib["id"]
        return False

    def create(self, title):
        """Returns Photoset and returns ID."""
        return self.flickr.photosets_create(
            method='flickr.photosets.create',
            title=title,
            primary_photo_id=self.primary_photo_id
        ).find("photoset").attrib['id']

    def get_photoset_id(self, title):
        """
        Get photoset ID from flickr for a photoset with the title 'title'
        :param title:
        :return:
        """
        self.photoset_id = self.exists(title) or self.create(title)

    def add_photos(self):
        """Adds photo ids to photoset on Flickr."""
        return [self.flickr.photosets_addPhoto(
            photoset_id=self.photoset_id,
            photo_id=i) for i in self.photo_ids]

    def __call__(self, title, ids, primary_photo_id=0):
        """Generates photoset based on information passed in call"""
        self.primary_photo_id = primary_photo_id or ids[0]
        self.photo_ids = ids
        self.photo_ids.remove(self.primary_photo_id)
        self.get_photoset_id(title)
        if self.photo_ids:
            response = self.add_photos()
            return response


class AbstractDirectoryUpload(object):
    """
    Framework to create uploads to other locations.
    I was on an Object Oriented programming kick when I did this, don't judge me. orz
    """
    def __init__(self):
        self.files = []

    def filter_directory_contents(self, d, f):
        """Return true for files we don't want in our list (directories for now)"""
        return os.path.isdir(os.path.join(d, f))

    def get_directory_contents(self, d):
        """Get list of all files in a directory.
        TODO: Maybe this is better as a generator?"""
        self.files = [os.path.join(d, f)
                      for f in os.listdir(d)
                      if not self.filter_directory_contents(d, f)]

    def prehook(self, **kwargs):
        pass

    def posthook(self, **kwargs):
        pass

    def upload(self):
        raise NotImplementedError

    def parse_response(self):
        raise NotImplementedError

    def __call__(self, directory, **kwargs):
        self.directory = directory

        self.prehook(**kwargs)
        self.get_directory_contents(self.directory)
        self.upload()
        self.parse_response()
        self.posthook(**kwargs)


class DirectoryFlickrUpload(AbstractDirectoryUpload):
    """
    Handles actual upload to Flickr.
    """
    def __init__(self, flickr):
        super(DirectoryFlickrUpload, self).__init__()
        self.ids = []
        self.tags = []
        self.photoset_name = ''
        self.responses = []
        self.failed_uploads = []
        self.flickr = flickr
        self.create_photoset = Photoset(flickr)

    def filter_directory_contents(self, d, f):
        return not valid_img(os.path.join(d, f))

    def prehook(self, tags, pset, **kwargs):
        self.ids = []
        self.tags = ", ".join(tags)
        self.photoset_name = pset

    def flickr_upload(self, f, **kwargs):
        """
        Actually uploads file to Flickr.
        :param f:
        :param kwargs:
        :return:
        """
        print "Uploading %s" % f
        return self.flickr.upload(filename=f, tags=self.tags,
                                  is_public=kwargs.get('is_public', 0),
                                  is_family=kwargs.get('is_family', 0))

    def upload(self):
        self.responses = [(self.flickr_upload(f, is_public=0, is_family=0), f) for f in self.files]

    def parse_response(self):
        """
        Handles response from Flickr API.
        :return:
        """
        self.ids = [r.find("photoid").text for (r, f) in self.responses if r.attrib['stat'] == "ok"]
        self.failed_uploads = [f for (r, f) in self.responses if r.attrib['stat'] != "ok"]
        self.successful_uploads_count = len(self.ids)
        self.failed_uploads_count = len(self.failed_uploads)

    def posthook(self, **kwargs):
        self.create_photoset(self.photoset_name, self.ids)
        self.handle_failed_uploads()

    def handle_failed_uploads(self):
        pass


class PublicDirectoryUpload(DirectoryFlickrUpload):
    """Uploads files in a directory exclusively as "Public" files."""

    def flickr_upload(self, f, **kwargs):
        """dispatches upload command to flickr with appropriate details taken from the self object
        :type f: str
        The path to a file.
        """
        return super(PublicDirectoryUpload, self).flickr_upload(f, is_public=1, is_family=0)


class FamilyDirectoryUpload(DirectoryFlickrUpload):
    """Uploads files in a directory exclusively as "Family-only" files."""

    def flickr_upload(self, f, **kwargs):
        """dispatches upload command to flickr with appropriate details taken from the self object
        :type f: str
        The path to a file."""
        return super(FamilyDirectoryUpload, self).flickr_upload(f, is_public=0, is_family=1)
