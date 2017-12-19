"""DailyData module.

Reads all data from a plain text file and stores them in a list which can
then be indexed to be read back. List will be 'rewound' or 'reset' to the
top of the list if the end of the list is reached.

@author Christopher Teh Boon Sung

"""


class DailyData(object):
    """DailyData class.

    Load all values from file into a list, accessible by indexing.

    Attributes:
        data - the list, containing all the values read from the file
        nset - number of values per line in the file
    """

    def __init__(self, fname):
        """Construct the DailyData object.

        Args:
            fname: name of plain text file containing the data

        Returns:
            None
        """
        self.nset = None    # will hold the no. of lines read from file
        self.data = []      # will hold the entire list of values
        with open(fname, 'rt') as f:
            nset = set()    # number of values per line of file
            for line in f:
                # read file line-by-line, where each line is then split
                #    into list of strings, and where each string is
                #    converted into a float and stored in the data list.
                lst = [float(item.strip()) for item in line.split(',')]
                if lst:
                    # add only if list is not empty
                    #    (can happen when reading a blank line)
                    nset.add(len(lst))
                    self.data += lst
            if len(nset) != 1:
                raise IndexError('Inconsistent pairing/missing'
                                 ' values in file.')
            self.nset = nset.pop()

    def __getitem__(self, key):
        """Override the indexing operator [] to return data.

        Indexing begins at 1, not 0, because the key indicates
        the day number or number of elapsed days.

        Args:
            key: day no. or no. of days elapsed (starts at 1, not 0)

        Returns:
            A float or list of floats
        """
        if key < 1:
            raise ValueError('No. of days (key) must be greater than 0.')
        nlen = len(self.data)
        idx = ((key - 1) * self.nset) % nlen
        if self.nset == 1:
            # return a float because only 1 value per data set
            return self.data[idx]
        else:
            # return a list of floats
            return [self.data[idx + i] for i in range(self.nset)]

    def __iter__(self):
        """Allow the object to be used in generators."""
        for idx in range(0, len(self.data), self.nset):
            yield [self.data[idx + i] for i in range(self.nset)]
