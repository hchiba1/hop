from classes.CurlManager import CurlManager
import os

class GenomeDownloader2:
    def __init__(self, output_folder, species_list):
        self.ftp_server = 'ftp.ncbi.nlm.nih.gov'
        self.summary_file_source = '/genomes/ASSEMBLY_REPORTS/assembly_summary_refseq.txt'
        self.downloaded_genomes = 'genome_list.tsv';
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        self.output_folder = output_folder
        self.id_hash = self.__get_id_hash(species_list)
        self.taxid_hash = self.__get_taxid_hash(species_list)
        self.species_hash = self.__get_species_hash(species_list)

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
        curl = CurlManager(self.ftp_server)
        curl.download(self.summary_file_source, summary_file)
        self.__download_genomes(summary_file, debug)

    def __download_genomes(self, summary_file, debug):
        file_obtained = {}
        fp = open(summary_file, 'r', encoding='UTF-8')
        line = fp.readline()
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
                    gcf_file = self.__download_gcf_file(url, debug)
                    file_obtained[id] = gcf_file
            line = fp.readline()
        fp.close()

        result_fp = open(self.downloaded_genomes, 'w')
        for id in self.id_hash:
            if file_obtained.get(id) is None:
                print('Genome not obtained for: ' + self.id_hash[id])
            else:
                result_fp.write(id + '\t' + file_obtained[id] + '\n');
        result_fp.close()
    
    def __download_gcf_file(self, url, debug):
        server = url.replace('ftp://', '')
        index = server.find('/')
        path = server[index:]
        server = server[0:index]
        curl = CurlManager(server)
        files = curl.list(path)

        faa = None
        gcf_file_path = None
        for file in files:
            if file.endswith('faa.gz'):
                faa = file
        if faa is not None:
            index = faa.rfind('/')
            file_name = faa[index + 1:]
            faa_file = self.output_folder + '/' + file_name
            if not debug:
                curl.download_gz(faa, faa_file)
            gcf_file_name = file_name.replace('faa.gz', 'faa')
            gcf_file_path = self.output_folder + '/' + gcf_file_name
        return gcf_file_path
