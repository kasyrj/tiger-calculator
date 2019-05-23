#!/usr/bin/python3

import abc

class AbstractReader(metaclass=abc.ABCMeta):

    @abc.abstractstaticmethod
    def getReaderName(self):
        '''Return the string that specifies the format when coupled with the -f option.'''
        pass

    @abc.abstractmethod
    def getContents(file_or_dir):
        '''Return the contents of file_or_dir (provided by the user as an argument) as a list of the form [[taxa][aligned_characters]]. [taxa] should contain the names of the taxa as strings. [aligned_characters] should contain an alignment of each taxon as a list in the form  [site_1, site_2, site_3, ... site_n], in the same order as the taxon names are given in [taxa].'''
        pass

if __name__ == '__main__':
    print("Interface/abstract class definition for tiger-calculator file format readers")
