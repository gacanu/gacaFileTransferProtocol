# gacaFileTransferProtocol
A custom File Transfer Protocol (FTP) application written entirely in Python!

### Usage Instructions

To use, download the source files into the same folder and run `./client [FTP command] [args]` on a linux terminal.

This implementation supports the following FTP commands: `ls`, `mkdir`, `rmdir`, `rm`, `mv`, `cp`.

### Usage Examples

`./client ls ftp://bob:secret123@ftpurl.example.com/path`

Where the username is `bob`, the password is `secret123`, the FTP url is `ftpurl.example.com`, and the path to the folder to list the contents of is `path/`.

`./client mv documents/file.txt ftp://@127.0.0.1/files/serverfile.txt`

Omitting the username and password is allowed, and sets the usernme automatically to `anonymous`. In this case, this moves a local file contained within `documents/file.txt` to the server at IP Address `127.0.0.1`, into the directory `file/` with the name `serverfile.txt`.

When utilizing commands with two required arguments (`mv` and `cp`), exactly one of both a server FTP location and a local path is required.
