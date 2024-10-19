class Preset:
    pass


class Prophet_Rev2:
    def __init__(self):
        pass

    """
        To read table from docs:
        s = "" # table from string
        def crop(substring, header):
            if header == "Description":
                return substring, ""
            return substring[:substring.find(" ")], substring[substring.find(" ")+1:]
        header = ('NRPN Layer A', 'NRPN Layer B', 'Value', 'Description',)
        data = {h:[] for h in header}
        for substring in s.split('\n'):
            for h in header:
                value, substring = crop(substring, h) 
                data[h].append(value)
    """