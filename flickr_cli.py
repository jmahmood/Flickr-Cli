# encoding: utf8
#!/usr/bin/env python

import os
import imghdr

# Maintains state for the uploads
class uploadStatus:
    def __init__(self, filelist):
        self.filelist = filelist
        self.total_upload_size = self.get_upload_size(self.filelist)
    def get_upload_size(self, files):
        return sum([ os.path.getsize(f) for f in files ])
    def uploaded_thus_far(self):
        return float(self.get_upload_size(self.filelist[0:self.filelist.index(self.file)]))
    def status(self, progress, done):
        # which file?
        # What % of it is done?
        total = self.uploaded_thus_far() + \
                float(progress * os.path.getsize(self.file)) / 100
        return round(total / self.total_upload_size * 100, 2)

# Initialize it with the flickr instance.
# After that, you can use this to arrange photos into sets
# by the photo id

class photoset(object):
    def __init__(self, flickr):
        self.flickr = flickr

    def exists(self, title):
        photosets = self.flickr.photosets_getList().find("photosets").findall("photoset")

        for p in photosets:
            if p.find("title").text == title:
                return p.attrib["id"]
        return False

    def create(self, title):
        return self.flickr.photosets_create(
                method='flickr.photosets.create',
                title=title, 
                primary_photo_id=self.primary_photo_id
            ).find("photoset").attrib['id']

    def get_photoset_id(self, title):
        self.photoset_id = self.exists(title) or self.create(title)

    def add_photos(self):
        print repr(self.photo_ids)
        return [ self.flickr.photosets_addPhoto(
                photoset_id=self.photoset_id, 
                photo_id=i) for i in self.photo_ids ]

    def __call__(self, title, ids, primary_photo_id=0):
        self.primary_photo_id = primary_photo_id or ids[0]
        self.photo_ids = ids
        self.photo_ids.remove(self.primary_photo_id)
        self.get_photoset_id(title)
        if len(self.photo_ids) > 0:
            response = self.add_photos()
            return response



class abstractDirectoryUpload(object):
    def filter_directory_contents(self, d, f):
        return os.path.is_dir(os.path.join(d, f) )

    def get_directory_contents(self, d="/Users/jawaadmahmood"):
        dirList=os.listdir(d)
        self.files = [os.path.join(d, f) 
            for f in dirList 
            if not self.filter_directory_contents(d,f)  ]

    def prehook(self, **kwargs):
        pass

    def posthook(self):
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
        self.posthook()


class directoryFlickrUpload(abstractDirectoryUpload):

    def __init__(self, flickr):
        self.flickr  = flickr
        self.create_photoset = photoset(flickr)

    def valid_img(self, f):
        try:
            if imghdr.what(f):
                return True
        except:
            pass
        return False

    def filter_directory_contents(self, d, f):
        return not self.valid_img(os.path.join(d, f) )

    def prehook(self, tags, photoset):
        self.ids = []
        self.tags = ", ".join(tags)
        self.photoset_name = photoset


    def flickr_upload(self, f):
        print "uploading %s" % f
        return self.flickr.upload(filename=f, tags=self.tags, is_public=0, is_family=0)

    def upload(self):
        self.responses = [ (self.flickr_upload(f), f) for f in self.files ]

    def parse_response(self):
        self.ids = [ r.find("photoid").text for (r,f) in self.responses if r.attrib['stat'] == "ok" ]
        self.failed_uploads = [ f for (r,f) in self.responses if r.attrib['stat'] != "ok" ]


    def posthook(self):
        self.create_photoset(self.photoset_name,self.ids)
        self.handle_failed_uploads()

    def handle_failed_uploads(self):
        pass


class publicDirectoryUpload(directoryFlickrUpload):
    def flickr_upload(self, f):
        return self.flickr.upload(filename=f, tags=self.tags, is_public=1, is_family=0)


class familyDirectoryUpload(directoryFlickrUpload):
    def flickr_upload(self, f):
        return self.flickr.upload(filename=f, tags=self.tags, is_public=0, is_family=1)



"""
flickr = flickrapi.FlickrAPI(api_key, secret)
(token, frob) = flickr.get_token_part_one(perms='write')
flickr.get_token_part_two((token, frob))
images = get_images("/Users/jawaadmahmood/wedding/Mariko/Mendhi")
flickr_cli(flickr, images, "mehndi", "Mehndi")


images = get_images("/Users/jawaadmahmood/wedding/Mariko/Ceremony")
flickr_cli(flickr, images, "ceremony", "Wedding Ceremony")
"""