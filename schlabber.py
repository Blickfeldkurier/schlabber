#!/usr/bin/env python
import os
import argparse
import pprint

class Soup:
    def assertdir(self,dirname):
        if not os.path.isdir(dirname):
            os.makedirs(dirname)

    def __init__(self, soup, bup_dir):
        self.rooturl = "http://"+soup+".soup.io/"
        self.bup_dir = os.path.abspath(bup_dir)
        self.assertdir(self.bup_dir)
        self.dlurl = self.rooturl
        self.dlnextfound = False
        print("Backup: " + self.rooturl)
        print("into: " + self.bup_dir)

def main(soups, bup_dir):
    for site in soups:
        soup = Soup(site, bup_dir)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Soup.io backup')
    parser.add_argument('soups', nargs=1, type=str, default=None, help="Name your soup")
    parser.add_argument('-d','--dir', default=os.getcwd(), help="Directory for Backup (default: Working dir)")
    #parser.add_argument('-f','--foo', action='store_true', default=False, help='sample for option (used later)')
    args = parser.parse_args()
    main(args.soups, args.dir)