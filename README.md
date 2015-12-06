Flickr-Cli
==========

Do you manage your images in directories? Do you find it obscene when you are unable to upload a few gigs of images because a program is trying to load all of them into memory at the same time?

Congratulations!  You are sane.

This tool is meant to facilitate the uploading of large numbers of images to Flickr.  

It was built after I realized that the CLI that everyone keeps talking about didn't work on my computer, and that the horrid GUI-based tools kept failing under the burden of uploading 4 gigs of wedding photos.

Dependencies
------------
Flickrapi, Python 2.6.x

(If you are interested, I could probably produce a python 3.x version.)

Installation
------------
1. Install python dependencies

        pip install -r pip.txt

2. Copy the sample `flickr.config`:

        cp flickr.config.sample flickr.config

3. Optional: if you prefer to use your own API key, you can generate
it here and then update the settings in your `flickr.config`:
http://www.flickr.com/services/apps/create/noncommercial/?


Example:
--------

    ./flickr_up.py -d /path/to/lolcats/ -t lol -t cats -p Cats

The first time you run it, it will prompt you to log into your Flickr account through a browser window.  Once you are logged in, you need to approve uploads by the app to your Flickr account.


TODO
----
- Improve failed upload handling
- Add uploads to 500px and other photo uploading services.
