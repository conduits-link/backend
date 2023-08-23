# Architecture

* Django
    * Easy and fast
    * Python allows for future possibility of easy server-side ML

* MySQL database
    * Store user details, user text files, and links to other user media files
    * SQLite has size restrictions and can't be used with client-server model
    * PostgreSQL seemed like overkill for now

* JWT (JSON web token) User authentication
  * Saves server memory

## Models

Each account should store:
* Email, username, password
* Text editor files
* Links to other media

In future we may add social media-type functionality, e.g. profile pictures, friends, etc.
