#!/usr/bin/env python3
import argparse
from classes.GenomeDownloader import GenomeDownloader

parser = argparse.ArgumentParser(description='Download genomes from NCBI, according to the species list in tsv format.')
parser.add_argument('species_list', help='Species list in tsv format')
parser.add_argument('-n', '--cores', default=1, type=int, help='Number of CPU cores to be used for downloading genome files.')
parser.add_argument('-o', '--outdir', default='genome', help='Output directory')
parser.add_argument('-d', '--debug', action='store_true', help='For debug: do not download the genomes')
args = parser.parse_args()

downloader = GenomeDownloader(args.outdir, args.cores)
summary_file = downloader.download_summary_file('ftp.ncbi.nlm.nih.gov', '/genomes/ASSEMBLY_REPORTS/assembly_summary_refseq.txt')
downloader.download_files(summary_file, args.species_list, 'genome_list.tsv', args.debug)
