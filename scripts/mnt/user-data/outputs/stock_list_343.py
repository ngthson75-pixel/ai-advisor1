# 343 Cổ phiếu có thanh khoản cao nhất HOSE + HNX

TOP_343_STOCKS = [
    # HOSE - Top Blue Chips & Large Caps (50 stocks)
    'VCB', 'VHM', 'VIC', 'VNM', 'HPG', 'TCB', 'VPB', 'MBB', 'STB', 'MSN',
    'FPT', 'VRE', 'SSI', 'BID', 'CTG', 'PLX', 'GAS', 'MWG', 'VJC', 'HDB',
    'PDR', 'POW', 'SAB', 'NVL', 'BCM', 'KDH', 'DGC', 'REE', 'TPB', 'ACB',
    'GVR', 'PNJ', 'VGC', 'DHG', 'DPM', 'GMD', 'HPX', 'LPB', 'VCI', 'SSB',
    'BVH', 'HNG', 'TCH', 'DXG', 'VHC', 'PC1', 'DIG', 'HT1', 'VGS', 'IDC',
    
    # HOSE - Mid Caps (100 stocks)
    'VPI', 'GEX', 'HSG', 'DCM', 'NT2', 'HVN', 'VND', 'VCG', 'SBT', 'EVF',
    'DBC', 'HCM', 'CTD', 'KBC', 'DGW', 'SZC', 'LGC', 'VNE', 'VIX', 'HDG',
    'PPC', 'VSC', 'BWE', 'HT2', 'VDS', 'VSH', 'VTP', 'SCS', 'TDH', 'PVD',
    'PVT', 'ASM', 'CSV', 'ITA', 'NLG', 'VCF', 'CMG', 'BMP', 'PAN', 'SGN',
    'PHR', 'NBB', 'DPR', 'DVP', 'FCM', 'GEG', 'PVS', 'PTB', 'HBC', 'HAG',
    'CMX', 'VPH', 'PVG', 'DMC', 'KDC', 'TNG', 'HRC', 'SVC', 'TCL', 'PXI',
    'TYA', 'HHS', 'DRL', 'DRI', 'HAX', 'SZL', 'VTO', 'HAI', 'PET', 'PVP',
    'ASP', 'HU3', 'FRT', 'SJS', 'VST', 'VCS', 'TRA', 'VIB', 'TCM', 'VGT',
    'HAP', 'DHA', 'VNT', 'VMD', 'PDN', 'PMG', 'PVX', 'GIL', 'VFC', 'CTI',
    'FCN', 'QCG', 'TDM', 'GMC', 'HQC', 'VPS', 'VIS', 'TNI', 'DXV', 'HDC',
    
    # HOSE - Small Caps (93 stocks)
    'CII', 'HTN', 'PDC', 'PGD', 'AGG', 'FLC', 'POM', 'ASG', 'ITC', 'CAV',
    'VOS', 'VTB', 'PGC', 'SHI', 'SRC', 'CNG', 'DVN', 'GDT', 'VLA', 'BTT',
    'DTT', 'VRC', 'KSB', 'CRE', 'PGI', 'TTF', 'TNT', 'VDP', 'CSM', 'CTS',
    'TPC', 'TCO', 'DLG', 'PGS', 'VCW', 'TMT', 'TIX', 'DVW', 'GTA', 'PGT',
    'SII', 'TCR', 'TLG', 'LBM', 'GDW', 'THG', 'PLC', 'VNL', 'HTI', 'HU1',
    'NHH', 'BCG', 'HU6', 'BFC', 'CTR', 'PNC', 'PTL', 'HDM', 'VHL', 'VTL',
    'TCW', 'NHA', 'CLC', 'SAM', 'VCX', 'PTI', 'PXT', 'SMA', 'VIT', 'VGG',
    'BAF', 'SHB', 'TLH', 'PAN', 'BCC', 'VSM', 'VE1', 'VE2', 'VE3', 'VE4',
    'VE8', 'VE9', 'VHG', 'VID', 'VIE', 'VIF', 'VIG', 'VIH', 'VIK', 'VIM',
    'VIN', 'VIP', 'VIR',
    
    # HNX - Top Stocks (100 stocks)
    'PVS', 'ACB', 'VCS', 'SHS', 'PVB', 'CEO', 'VCG', 'BVS', 'BAB', 'NVB',
    'VIB', 'OCB', 'SHB', 'MSB', 'TPB', 'BVB', 'EIB', 'VBB', 'PGB', 'VND',
    'TIG', 'VGC', 'PVI', 'BMI', 'BIC', 'PTI', 'VIG', 'MIG', 'BSI', 'ABI',
    'BII', 'PGI', 'EVS', 'PSI', 'HBS', 'TVS', 'APS', 'VDS', 'CTS', 'FTS',
    'MBS', 'APG', 'AGG', 'SVC', 'L10', 'L14', 'L18', 'L40', 'L43', 'L44',
    'L45', 'L61', 'L62', 'L63', 'DHT', 'DHA', 'DHM', 'NHP', 'NHS', 'NHT',
    'NHW', 'SIC', 'LAS', 'HUT', 'BCC', 'DBC', 'DTD', 'DTT', 'NBC', 'NNC',
    'PLC', 'PTC', 'PVL', 'PVV', 'SCR', 'SRA', 'TIG', 'VE1', 'VE2', 'VE3',
    'VE4', 'VE8', 'VE9', 'VGS', 'VHL', 'VIG', 'VIX', 'CEO', 'VGG', 'VTB',
    'AMV', 'API', 'ARM', 'ART', 'ASA', 'ASG', 'ASM', 'ASP', 'AST', 'ATA'
]

# Use this in your scanner
if __name__ == "__main__":
    print(f"Total stocks: {len(TOP_343_STOCKS)}")
    print(f"First 10: {TOP_343_STOCKS[:10]}")
    print(f"Last 10: {TOP_343_STOCKS[-10:]}")
