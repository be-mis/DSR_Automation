#File name to chain mapping



chain_mapping = {
    **dict.fromkeys(["wds", "waltermart", "walter"], 'WDS'),
    **dict.fromkeys(["uratex"], 'URATEX'),
    **dict.fromkeys(["fisher", "fishermall"], 'FISHER'),
    **dict.fromkeys(["rds", "robinsons","robinson\'s", "spatio"], 'RDS'),
    **dict.fromkeys(["landmark"], 'LANDMARK'),
    **dict.fromkeys(["rdstoysrus"], 'RDS – Toys R Us'),
    **dict.fromkeys(["ourhome"], 'OUR HOME'),
    **dict.fromkeys(["smtoykingdom"], 'SM Aff – Toy Kingdom'),
    **dict.fromkeys(["smdept.store", "sm"], 'SM'),
    **dict.fromkeys(["smhomeworld", "SMHW", "sm"], 'SM'),
    **dict.fromkeys(["allhome"], 'ALLHOME'),
    **dict.fromkeys(["metro"], 'METRO'),
    **dict.fromkeys(["kcc"], 'KCC'),
    **dict.fromkeys(["homeworks"], 'HWORKS'),
    **dict.fromkeys(["nccc"], 'NCCC'),
}

db_mapping = {
    **dict.fromkeys(["epc"], 'EPC'),
    **dict.fromkeys(["nbfi"], 'NBFI'),
}

HEADERS = {
    'SKU': ['matcode', 'sku#', 'sku', 'sku number', 'sku code'],
    'BRANCH': ['store name', 'branch', 'site name', 'branch name', 'store description'],
    'DESC': ['item description', 'description', 'product description'],
    'DATE': ['date', 'tran date', 'post date'],
    'QTY': ['qty sold', 'qty', 'qty/kilo', 'quantity', 'units sold ty'],
    'GROSS': ['total amount', 'gross sales amt', 'sales amount', 'gross amount', 'gross sales', 'gross sales ty']
}

#All of the raw files should be consolidated already before uploading to the system. The users should do the consolidation
