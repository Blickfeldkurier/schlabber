# shlabber.py - Archives a soup

Schlabbern is like auslöffeln, only much more messy

## Features
 * Works with endless scroll
 * Saves more than images
 * Preserves some metadata
 * If your soup shows timestamps, they will be used to sort the backup

## Dependencies
 * [beautifulsoup4 (bs4)](https://www.crummy.com/software/BeautifulSoup/)
 * requests

## Use
Basic usage:
```
./schlabber <name of soup>
```
If invoked without any parameters, the programm will asume the output direcory for all files is the 
working directory. 
To choose an alternative output diectory supply -d \<path> to the application

For more options:
```
./schlabber -h
```

### Contiune Backup
Sometimes Soup.io failes to fetch more Posts.
In this case the script will stop.
Just run the script again, but this time with the -c switch.
Look at your previous run. There is a line telling you "Get: ..."
Just use everything from /since/ till the line end as parameter for -c
and the script should continue where it has left off.

## Alternatives
If this script does not work for you there are others you can try:
 * https://github.com/neingeist/soup-backup
 * https://github.com/rixx/ripsoup
