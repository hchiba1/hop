import os
import sys
from threading import Thread, Semaphore
from classes.FtpCli import FtpCli

class GenomeDownloader:
    def __init__(self, output_folder, species_list, num):
        self.ftp_server = 'ftp.ncbi.nlm.nih.gov'
        self.summary_file_source = '/genomes/ASSEMBLY_REPORTS/assembly_summary_refseq.txt'
        self.downloaded_files = 'genome_list.tsv';
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        self.output_folder = output_folder
        self.id_hash = self.__get_id_hash(species_list)
        self.taxid_hash = self.__get_taxid_hash(species_list)
        self.species_hash = self.__get_species_hash(species_list)
        self.semaphore = Semaphore(int(num))

    def __get_id_hash(self, species_list):
        hash = {}
        fp = open(species_list, 'r')
        line = fp.readline()
        while line:
            line = line.strip()
            tokens = line.split('\t')
            if tokens[0].isdigit():
                hash[tokens[0]] = line
            line = fp.readline()
        fp.close()
        return hash

    def __get_taxid_hash(self, species_list):
        hash = {}
        fp = open(species_list, 'r')
        line = fp.readline()
        while line:
            line = line.strip()
            tokens = line.split('\t')
            if len(tokens) >= 7:
                hash[tokens[6]] = tokens[0]
            line = fp.readline()
        fp.close()
        return hash

    def __get_species_hash(self, species_list):
        hash = {}

        fp = open(species_list, 'r')
        line = fp.readline()
        while line:
            line = line.strip()
            tokens = line.split('\t')
            if len(tokens) >= 2:
                species = tokens[1]
                hash[species] = tokens[0]
            line = fp.readline()
        fp.close()
        return hash

    def download(self, debug):
        index = self.summary_file_source.rfind('/')
        summary_file = self.summary_file_source[index + 1:]
        ftp = FtpCli(self.ftp_server)
        if not ftp.is_up_to_date(self.summary_file_source, summary_file):
            ftp.get(self.summary_file_source, summary_file)
        ftp.close()
        self.__download_files(summary_file, debug)

    def __download_files(self, summary_file, debug):
        file_obtained = {}
        fp = open(summary_file, 'r', encoding='UTF-8')
        line = fp.readline()
        threads = []
        while line:
            line = line.strip()
            tokens = line.split('\t')
            if not line.startswith('#') and len(tokens) >= 8:
                gcf_id = tokens[0]
                taxid = tokens[5]
                species_taxid = tokens[6]
                species = tokens[7]
                url = tokens[19]
                id = self.species_hash.get(species) or \
                     self.taxid_hash.get(taxid) or \
                     self.taxid_hash.get(species_taxid)
                if id is not None and file_obtained.get(id) is None:
                    thread = Thread(name=gcf_id, target=self.__download_file, args=(url, debug, file_obtained, id))
                    threads.append(thread)
                    thread.start()
            line = fp.readline()
        fp.close()

        for t in threads:
            t.join()

        print('Downloading done.', file=sys.stderr, flush=True)
        result_fp = open(self.downloaded_files, 'w')
        err_fp = open(self.downloaded_files + '.err', 'w')
        for id in self.id_hash:
            if file_obtained.get(id) is None:
                print(self.id_hash[id], file=err_fp)
            else:
                result_fp.write(id + '\t' + file_obtained[id] + '\n');
        result_fp.close()
        err_fp.close()
        print('Created', self.downloaded_files, file=sys.stderr, flush=True)

    def __download_file(self, url, debug, file_obtained, id):
        with self.semaphore:
            server = url.replace('ftp://', '')
            index = server.find('/')
            path = server[index:]
            server = server[0:index]
            index = path.rfind('/')
            file_name = path[index + 1:]
            outfile = self.output_folder + '/' + file_name + '_protein.faa.gz'
            print(f'{id}\t{outfile}', flush=True)
            if not debug:
                ftp = FtpCli(server)
                if not ftp.is_up_to_date(f'{path}/{file_name}_protein.faa.gz', outfile):
                    ftp.get(f'{path}/{file_name}_protein.faa.gz', outfile)
                ftp.close()
            file_obtained[id] = outfile.replace('faa.gz', 'faa')
