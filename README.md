# Prebooru

Repository for downloading and storing artist data and images prior to being uploaded to a booru.

# Installation

1. Copy the Prebooru project locally.

    `git clone https://github.com/BrokenEagle/Prebooru.git`

2. Run the installation script from the root directory.

    `setup.bat`

    **Note:** This can be done in a virtual Python environment in order to keep this install from conflicting with other projects.

3. Setup the local config file.

    Using the `app\default_config.py` as a reference, create `app\local_config.py` with the configuration specific to the user and machine.

    **Note:** The`default_config.py` is tracked by Git, but if that is not a concern, then it can be modified directly instead.

4. Initialize the database.

    `prebooru.py init`

5. Start all of the servers.

    `server.py startall`

6. Install FFMPEG binaries (optional)

Go to https://www.gyan.dev/ffmpeg/builds/ and download `ffmpeg-git-essentials.7z`. Copy the `ffprobe.exe` to the root directory.

This allows the downloader to verify the dimensions and streams of MP4 videos before saving them to disk.

# Supported sites

There are currently only a few sites supported for automatic uploading. The following lists these sites and their supported request URL.

- Pixiv / artwork
    - https://www.pixiv.net/artworks/1234
- Twitter / tweet
    - https://twitter.com/nothing/status/1234

# Bookmarklets

Prebooru has two landing pages which support uploading directly with a source URL. The bookmarklets will open new tabs to these pages when on one of the supported site pages.

**Note:** The following assume the default IP address and port from the local config file. Replace these values if they are different.

## All

Will upload all images from the site post.

```
javascript:window.open('http://127.0.0.1:5000/uploads/all?upload[request_url]='+encodeURIComponent(location.href),'_blank');false;
```

## Select

Will go to a page with all of the preview images from the post displayed, allowing one to select which images to upload from the site post.

```
javascript:window.open('http://127.0.0.1:5000/uploads/select?upload[request_url]='+encodeURIComponent(location.href),'_blank');false;
```

# Other

## Image server

The default image server provided is functional, but isn't optimized at sending a lot of images at once. An alternate image server can be used instead for this purpose. If this is being done, then add the necessary information to the config file, as well as setting the following value.

```python
HAS_EXTERNAL_IMAGE_SERVER = True
```

### NGINX

- **Info:** http://nginx.org/en/docs/windows.html
- **Downlad:** http://nginx.org/en/download.html

An example configuration file (`nginx.conf`) is present under the **misc\\** folder. The **listen** line contains the port number, and by default it binds to **0.0.0.0**, so it will listen on all network adapters. The **root** line is the base directory where the images will reside as determined by the Prebooru config file, and the filepath needs to use Linux-style directory separators "/" instead of Windows-style "\\".

Additionally, there is also a `nginx.bat` batch file there which can be modified as necessary as an aid to quickly starting or stopping this service.

## Userscript

### NTISAS

A userscript which shows Tweets already uploaded to Danbooru as well as provides other additional functionality.

- **Info:** https://github.com/BrokenEagle/JavaScripts/wiki/Twitter-Image-Searches-and-Stuff
- **Forum page:** https://danbooru.donmai.us/forum_topics/16342

There is a branch of NTISAS under development which adds support for uploading and querying data from Prebooru.

https://raw.githubusercontent.com/BrokenEagle/JavaScripts/ntisas-prebooru/New_Twitter_Image_Searches_and_Stuff.user.js

### NPISAS

(Under development)
