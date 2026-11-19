import os, csv
folder = 'new_data_dawav2_improved'
files = ['clinical_kb_english.csv','clinical_kb_french.csv','clinical_kb_arabic.csv','universal_market_instances.csv']
print('Checking folder:', folder)
for fn in files:
    path = os.path.join(folder, fn)
    if not os.path.exists(path):
        print(f"{fn}: MISSING")
        continue
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration:
            print(f"{fn}: EMPTY")
            continue
        cols = len(header)
        rows = 0
        dupset = set()
        dup_count = 0
        sample = []
        header_l = [h.lower() for h in header]
        dci_idx = None
        for name in ['dci','denomination commune internationale','denomination_commune_internationale','medicine_name','dcis','active_ingredient']:
            if name in header_l:
                dci_idx = header_l.index(name)
                break
        brand_idx = None
        for name in ['brand_name','brand','nom_de_marque','medicine_name','medicine']:
            if name in header_l:
                brand_idx = header_l.index(name)
                break
        missing_dci = 0
        col_missing = [0]*cols
        for r in reader:
            rows += 1
            if rows <= 3:
                sample.append(r)
            for i,val in enumerate(r[:cols]):
                if val is None or str(val).strip() == '':
                    col_missing[i] += 1
            key = tuple(r[:cols])
            if key in dupset:
                dup_count += 1
            else:
                dupset.add(key)
            if dci_idx is not None:
                v = r[dci_idx] if dci_idx < len(r) else ''
                if not v or v.strip() == '':
                    missing_dci += 1
        print('-'*60)
        print(f'{fn}: rows={rows}, cols={cols}, exact_duplicates={dup_count}')
        if dci_idx is not None:
            print(f'  dci column present (index {dci_idx}), missing DCI rows={missing_dci} ({(missing_dci/rows*100) if rows else 0:.2f}%)')
        else:
            print('  dci column NOT FOUND')
        if brand_idx is not None:
            print(f'  brand column detected at index {brand_idx} -> header="{header[brand_idx]}"')
        print('  Top 6 header columns:', header[:6])
        print('  Sample rows (up to 3):')
        for s in sample:
            print('   ', s[:6])
print('\nDone.')
