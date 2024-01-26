from .utils import download, get_cache_path


_URL = "https://ccat.sas.upenn.edu/gopher/text/religion/biblical/parallel/{file}.par"
_FILES = {
    # Torah
    "Gen": "01.Genesis",
    "Exod": "02.Exodus",
    "Lev": "03.Lev",
    "Num": "04.Num",
    "Deut": "05.Deut",
    # Neviim
    "Josh": "06.JoshB",  # or 07.JoshA
    "Judg": "08.JudgesB",  # or 09.JudgesA
    "1Sam": "11.1Sam",
    "2Sam": "12.2Sam",
    "1Kgs": "13.1Kings",
    "2Kgs": "14.2Kings", 
    "Isa": "40.Isaiah",
    "Jer": "41.Jer",
    "Ezek": "44.Ezekiel",
    "Hos": "28.Hosea",
    "Joel": "31.Joel",
    "Amos": "30.Amos",
    "Obad": "33.Obadiah",
    "Jonah": "32.Jonah",
    "Mic": "29.Micah",
    "Nah": "34.Nahum",
    "Hab": "35.Hab",
    "Zeph": "36.Zeph",
    "Hag": "37.Haggai",
    "Zech": "38.Zech",
    "Mal": "39.Malachi",
    # Ketuviim
    "Ps": "20.Psalms",
    "Prov": "23.Prov",
    "Job": "26.Job",
    "Song": "25.Cant",
    "Ruth": "10.Ruth",
    "Lam": "43.Lam",
    "Eccl": "24.Qoh",
    "Esth": "18.Esther",
    "Dan": "45.DanielOG",  # or 46.DanielTh
    "Ezra": "18.Ezra",
    "Neh": "19.Neh",
    "1Chr": "15.1Chron",
    "2Chr": "16.2Chron",
}


def create_lxx():
    """
    Create LXX stuff.
    """
    records = []
    for code, fname in _FILES.items():
        path = _download(fname)
        records.extend(_parse(code, path))


def _download(fname):
    url = _URL.format(file=fname)
    path = get_cache_path("raw", "grlxx", f"{fname}.par")
    download(url, path)
    return path

  
def _parse(code, path):
    with path.open() as f:
        record = None
        brk = True
        for line in f:
            if line.strip() == "":
                brk = True
                continue
            if brk:
                if record: yield record
                cv = line.strip().split()[-1].split(":")
                c = 1 if len(cv) == 1 else cv[0]
                v = cv[0] if len(cv) == 1 else cv[1]
                try:
                    record = {"chapterId": f"{code}.{c}", "verseNum": int(v), "tokens": []}
                finally:
                    print(line)
                brk = False
                continue
            record["tokens"].append(line.strip().split("\t"))
        if record: yield record

