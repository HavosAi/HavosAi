import sys
sys.path.append('../src')

from webscrapping import webcrawler_main
import argparse


parser = argparse.ArgumentParser()
parser.add_argument('--folder_dataset', default = "../tmp/team_6_addition", help='folder for dataset')
parser.add_argument('--filename', default ="team_6_addition_1.txt",help='filename for search')

args = parser.parse_args()
_webcrawler_main = webcrawler_main.WebcrawlerMain()
_webcrawler_main.crawl_all_sources_from_file(args.filename, args.folder_dataset)