# encoding: utf8
#!/usr/bin/env python
import sys
import os
from optparse import OptionParser
import flickrapi
import flickr_cli
from ConfigParser import ConfigParser

config = ConfigParser()
config.read('flickr.config')
api_key = config.get('flickr', 'key')
secret = config.get('flickr', 'secret')


def photoset_default_title(directory):
	return os.path.basename(os.path.normpath(directory))

parser = OptionParser(version="1.0")

parser.add_option("-d", "--directory", dest="directory",
                  help="The directory from which you wish to copy the files", metavar="DIRECTORY")

parser.add_option("-p", "--photoset",
                  dest="photoset", default=False,
                  help="the name for the photoset on flickr.")

parser.add_option("-t", "--tags",
                  action="append", dest="tags", 
                  help="Tag to apply to pictures in this directory.")

parser.add_option("-q", "--quiet",
                  action="store_false", dest="verbose", default=True,
                  help="don't print status messages to stdout")

parser.add_option("-r", "--recursive",
                  action="store_false", dest="recursive", default=False,
                  help="recursively copy all subdirectories to different photosets")

parser.add_option("-R", "--RECURSIVE",
      action="store_false", dest="same_recursive", default=False,
      help="recursively copy all subdirectories to the same photoset. Overrides -r.")

(options, args) = parser.parse_args()


if len(args) > 0:
	print "ERROR"
	print "Aborting due to unrecognized arguments:\n %s" % ("\n\t".join(args))
	sys.exit(0)

if not options.directory: 
	print "ERROR"
	print "You must pass a directory.\n (example goes here)"
	sys.exit(0)


directory = options.directory
tags = options.tags or ""
photoset = options.photoset or photoset_default_title(options.directory)

if not options.photoset or not options.tags:
	print "WARNING"

if not options.photoset:
	print "You did not pass a name for the photoset.\n"
	print "We will use the photoset title '%s'" % photoset

if not options.tags:
	print "You did not pass any tags.\n"

print directory, tags, photoset


flickr = flickrapi.FlickrAPI(api_key, secret)
(token, frob) = flickr.get_token_part_one(perms='write')
flickr.get_token_part_two((token, frob))
upload = flickr_cli.directoryFlickrUpload(flickr)
upload(directory=directory, photoset=photoset, tags=tags)

