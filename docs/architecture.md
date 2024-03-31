# Architecture

* Django
    * Simple, powerful, scalable, and sufficiently fast.
    * We both know Python.
    * Python allows for future possibility of easy server-side ML.
    * Easy security, user authentication, database interaction, data sanitation etc.

* MySQL database
    * SQL seems appropriate for this use case.
    * Store user details, user text files, and links to other user media files.
    * SQLite has size restrictions and can't be used with client-server model.
    * PostgreSQL seems like overkill, especially for now.

## Models

Each account should store:
* Email, username, password.
* Text editor files and associated metadata.
* Links to other media.

In future we may add social media-type functionality, e.g. profile pictures, friends, etc.

## Endpoints

See [Conduit/docs/api.md](https://github.com/dan-smith-tech/conduit/blob/main/docs/api.md) for an exhaustive list.
