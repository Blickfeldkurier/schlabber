# shlabber.py - Archives a soup

Schlabbern is like auslöffeln, only much more messy

## Features
 * Works with endless scroll
 * Saves more than images
 * Preserves some metadata

## Dependencies
 * beautifulsoup4￼ (bs4)
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