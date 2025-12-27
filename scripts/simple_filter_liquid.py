#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SIMPLE AUTO-FILTER LIQUID STOCKS

Uses comprehensive list of Vietnamese stocks (700+ codes)
Filters by liquidity and downloads
"""

import sys
import os
import io
import time
from datetime import datetime, timedelta
import pandas as pd
import pickle

# Fix encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Suppress VNStock ads
class NullWriter:
    def write(self, text):
        pass
    def flush(self):
        pass

original_stdout = sys.stdout
sys.stdout = NullWriter()

from vnstock import Vnstock

sys.stdout = original_stdout


# ========================================================================
# COMPREHENSIVE LIST OF VIETNAMESE STOCKS (700+ codes)
# ========================================================================
ALL_VIETNAM_STOCKS = [
    # VN30
    'ACB', 'BCM', 'BID', 'BVH', 'CTG', 'FPT', 'GAS', 'GVR', 'HDB', 'HPG',
    'MBB', 'MSN', 'MWG', 'PLX', 'POW', 'REE', 'SAB', 'SHB', 'SSB', 'SSI',
    'STB', 'TCB', 'TPB', 'VCB', 'VHM', 'VIB', 'VIC', 'VJC', 'VNM', 'VPB',
    
    # HOSE Large Caps
    'DGC', 'PHR', 'DPM', 'DCM', 'GMD', 'VRE', 'VCI', 'NVL', 'DXG', 'PDR',
    'KDH', 'NLG', 'DIG', 'CII', 'TCH', 'CTD', 'HDG', 'LGC', 'HBC', 'DVP',
    'PC1', 'DHG', 'DMC', 'DRC', 'FTS', 'VND', 'HCM', 'SZL', 'HDC', 'HT1',
    'IDC', 'PAN', 'GEG', 'TDM', 'BWE', 'EVF', 'ORS', 'AGR', 'VOS', 'HAH',
    'VNA', 'PVG', 'VSH', 'GEX', 'HAG', 'BMP', 'TRA', 'IMP', 'ANV', 'NKG',
    'HSG', 'DBC', 'GEE', 'CMG', 'FRT', 'DGW', 'PET', 'CTR', 'SCS', 'VCG',
    'PVT', 'BSI', 'CTS', 'VIX', 'NT2', 'PVD', 'PVS', 'VHC',
    
    # HOSE Mid/Small Caps (A-D)
    'AAA', 'AAM', 'AAT', 'ABS', 'ABT', 'ACC', 'ACL', 'ADG', 'ADP', 'ADS',
    'AGF', 'AGG', 'AGM', 'AGP', 'AIC', 'ALT', 'AMD', 'AMP', 'APC', 'APG',
    'APH', 'API', 'APS', 'ARM', 'ASG', 'ASM', 'ASP', 'AST', 'ATA', 'ATB',
    'ATC', 'ATG', 'BAB', 'BAF', 'BBC', 'BBM', 'BBS', 'BBT', 'BCE', 'BCG',
    'BCI', 'BCN', 'BFC', 'BGW', 'BHC', 'BIC', 'BKC', 'BLF', 'BLT', 'BMC',
    'BMD', 'BMF', 'BMG', 'BMI', 'BMJ', 'BMP', 'BMS', 'BMV', 'BPC', 'BRC',
    'BSC', 'BSG', 'BSL', 'BST', 'BTC', 'BTD', 'BTG', 'BTH', 'BTN', 'BTP',
    'BTT', 'BTW', 'BVG', 'BVL', 'BWA', 'BWS', 'C12', 'C21', 'C22', 'C32',
    'C47', 'C69', 'C71', 'C92', 'CAD', 'CAG', 'CAN', 'CAP', 'CAT', 'CAV',
    'CBC', 'CC1', 'CC4', 'CCA', 'CCI', 'CCL', 'CCM', 'CCP', 'CCR', 'CCV',
    'CDC', 'CE1', 'CEC', 'CEN', 'CEO', 'CET', 'CFC', 'CFM', 'CFV', 'CGL',
    'CGP', 'CGV', 'CHC', 'CIA', 'CIC', 'CID', 'CIG', 'CIP', 'CKA', 'CKD',
    'CKG', 'CKV', 'CLC', 'CLG', 'CLL', 'CLM', 'CLP', 'CLW', 'CMC', 'CMD',
    'CMF', 'CMI', 'CMK', 'CMN', 'CMP', 'CMT', 'CMV', 'CMW', 'CMX', 'CNC',
    'CNG', 'CNN', 'COM', 'CP1', 'CPA', 'CPC', 'CPH', 'CPI', 'CQN', 'CQT',
    'CRC', 'CRE', 'CSC', 'CSG', 'CSM', 'CSV', 'CT3', 'CT6', 'CTA', 'CTB',
    'CTC', 'CTF', 'CTI', 'CTN', 'CTP', 'CTT', 'CTV', 'CTW', 'CTX', 'CVN',
    'CVT', 'CX8', 'D11', 'D2D', 'DAC', 'DAD', 'DAE', 'DAG', 'DAH', 'DAN',
    'DAT', 'DBD', 'DBM', 'DBT', 'DC1', 'DC2', 'DC4', 'DCC', 'DCF', 'DCG',
    'DCH', 'DCL', 'DCR', 'DCS', 'DCT', 'DDG', 'DDH', 'DDM', 'DDN', 'DDV',
    'DFC', 'DFF', 'DGL', 'DGT', 'DHA', 'DHB', 'DHC', 'DHI', 'DHM', 'DHN',
    'DHP', 'DHT', 'DIC', 'DID', 'DL1', 'DLG', 'DLR', 'DLT', 'DMS', 'DNA',
    'DNC', 'DNE', 'DNH', 'DNL', 'DNM', 'DNN', 'DNP', 'DNR', 'DNS', 'DNT',
    'DNW', 'DOP', 'DPC', 'DPG', 'DPH', 'DPP', 'DPR', 'DPS', 'DQC', 'DRG',
    'DRH', 'DRI', 'DS3', 'DSG', 'DSN', 'DSP', 'DST', 'DSV', 'DTA', 'DTB',
    'DTC', 'DTD', 'DTE', 'DTG', 'DTH', 'DTI', 'DTK', 'DTL', 'DTN', 'DTP',
    'DTT', 'DTV', 'DVC', 'DVG', 'DVM', 'DVN', 'DWC', 'DWS', 'DXL', 'DXP',
    'DXS', 'DXV', 'DZM',
    
    # HOSE (E-H)
    'E12', 'E29', 'EBA', 'EBS', 'ECI', 'EFI', 'EIB', 'EIC', 'EID', 'EIN',
    'ELC', 'EMC', 'EME', 'EMG', 'EMS', 'EVE', 'EVG', 'FBA', 'FBC', 'FCC',
    'FCM', 'FCN', 'FCS', 'FDC', 'FGL', 'FHN', 'FHS', 'FID', 'FIF', 'FIR',
    'FIT', 'FLC', 'FMC', 'FOX', 'FRC', 'FRM', 'GAB', 'GBS', 'GCB', 'GDT',
    'GDW', 'GER', 'GHC', 'GIC', 'GIL', 'GKM', 'GLT', 'GLW', 'GMC', 'GMX',
    'GSM', 'GSP', 'GTA', 'GTD', 'GTH', 'GTN', 'GTS', 'GVT', 'HAD', 'HAI',
    'HAP', 'HAR', 'HAS', 'HAT', 'HAX', 'HBB', 'HBD', 'HBH', 'HBS', 'HCC',
    'HCD', 'HCI', 'HCT', 'HDM', 'HEV', 'HGM', 'HGT', 'HGW', 'HHC', 'HHG',
    'HHL', 'HHP', 'HHS', 'HHV', 'HID', 'HIG', 'HII', 'HLA', 'HLC', 'HLG',
    'HLY', 'HMC', 'HMG', 'HMH', 'HNA', 'HNB', 'HND', 'HNF', 'HNG', 'HNI',
    'HNM', 'HNP', 'HOM', 'HPB', 'HPD', 'HPM', 'HPT', 'HPW', 'HPX', 'HQC',
    'HRC', 'HRG', 'HRT', 'HSA', 'HSC', 'HSI', 'HSL', 'HSM', 'HST', 'HTC',
    'HTG', 'HTI', 'HTL', 'HTM', 'HTN', 'HTP', 'HTR', 'HTT', 'HTV', 'HTW',
    'HU1', 'HU3', 'HU4', 'HU6', 'HUB', 'HUT', 'HVA', 'HVG', 'HVH', 'HVN',
    'HVT', 'HVX',
    
    # HOSE (I-M)
    'IBC', 'ICC', 'ICF', 'ICG', 'ICI', 'ICN', 'ICT', 'IDI', 'IDJ', 'IDV',
    'IFC', 'IJC', 'ILA', 'ILB', 'ILS', 'IME', 'INN', 'IRC', 'ISG', 'ISH',
    'IST', 'ITA', 'ITC', 'ITD', 'ITQ', 'ITS', 'JAK', 'JVC', 'KAC', 'KBC',
    'KDC', 'KDM', 'KGM', 'KGS', 'KHA', 'KHB', 'KHG', 'KHL', 'KHP', 'KHS',
    'KKC', 'KLB', 'KLF', 'KMR', 'KMT', 'KOS', 'KPF', 'KSA', 'KSB', 'KSC',
    'KSD', 'KSF', 'KSH', 'KSK', 'KSQ', 'KSS', 'KST', 'KSV', 'KTC', 'KTL',
    'KTS', 'KTT', 'L10', 'L14', 'L18', 'L35', 'L40', 'L43', 'L44', 'L45',
    'L61', 'L62', 'L63', 'LAF', 'LAS', 'LBC', 'LBE', 'LBM', 'LCC', 'LCG',
    'LCM', 'LCS', 'LDG', 'LDP', 'LDW', 'LEC', 'LGC', 'LGL', 'LHC', 'LHG',
    'LIC', 'LIG', 'LIX', 'LM3', 'LM7', 'LM8', 'LMH', 'LMI', 'LO5', 'LPB',
    'LSS', 'LTC', 'LTG', 'LUT', 'MAC', 'MAS', 'MBG', 'MBS', 'MCC', 'MCF',
    'MCG', 'MCP', 'MCH', 'MDC', 'MEC', 'MED', 'MEL', 'MFS', 'MHC', 'MHL',
    'MIG', 'MIH', 'MIM', 'MKP', 'MKV', 'MLC', 'MLS', 'MSB', 'MSC', 'MSH',
    'MST', 'MTA', 'MTG', 'MTL', 'MTP', 'MVB', 'MVC', 'MVN', 'NAF', 'NAG',
    'NAP', 'NAV', 'NBA', 'NBC', 'NBP', 'NBT', 'NBW', 'NCS', 'NCT', 'NDN',
    'NDT', 'NDW', 'NDX', 'NED', 'NET', 'NGC', 'NHA', 'NHC', 'NHH', 'NHP',
    'NHT', 'NHW', 'NIS', 'NKD', 'NKG', 'NLC', 'NLG', 'NLS', 'NMS', 'NNC',
    'NNT', 'NOS', 'NPS', 'NQB', 'NQN', 'NQT', 'NSC', 'NSG', 'NSH', 'NSL',
    'NSN', 'NST', 'NT2', 'NTB', 'NTC', 'NTF', 'NTH', 'NTL', 'NTP', 'NTT',
    'NTW', 'NUE', 'NVB', 'NVC', 'NVL', 'NVN', 'NVP', 'NVT', 'NXT',
    
    # HOSE (O-T)
    'OCB', 'OCH', 'ODE', 'OGC', 'OIL', 'OPC', 'ORS', 'PAC', 'PAN', 'PAP',
    'PAT', 'PBP', 'PBT', 'PC1', 'PCE', 'PCF', 'PCG', 'PCM', 'PCT', 'PDN',
    'PDR', 'PEN', 'PET', 'PFL', 'PGB', 'PGC', 'PGD', 'PGI', 'PGN', 'PGS',
    'PGT', 'PGV', 'PHC', 'PHH', 'PHN', 'PHP', 'PHR', 'PHS', 'PHT', 'PIC',
    'PID', 'PIE', 'PIT', 'PIV', 'PJC', 'PJT', 'PLC', 'PLO', 'PLP', 'PMB',
    'PMC', 'PME', 'PMG', 'PMJ', 'PMP', 'PMS', 'PMT', 'PMW', 'PNC', 'PNG',
    'PNJ', 'PNT', 'POB', 'POM', 'POS', 'POT', 'POW', 'PPC', 'PPE', 'PPG',
    'PPH', 'PPI', 'PPS', 'PPT', 'PPY', 'PRC', 'PRE', 'PRO', 'PRT', 'PSB',
    'PSC', 'PSD', 'PSE', 'PSG', 'PSH', 'PSI', 'PSL', 'PSN', 'PSP', 'PSW',
    'PTC', 'PTD', 'PTE', 'PTG', 'PTH', 'PTI', 'PTL', 'PTO', 'PTP', 'PTS',
    'PTT', 'PVA', 'PVB', 'PVC', 'PVD', 'PVE', 'PVG', 'PVI', 'PVL', 'PVM',
    'PVP', 'PVR', 'PVS', 'PVT', 'PVV', 'PVX', 'PVY', 'PWA', 'PWS', 'PX1',
    'PXA', 'PXI', 'PXL', 'PXM', 'PXS', 'PXT', 'PYU', 'QBS', 'QCC', 'QCG',
    'QHD', 'QNC', 'QNP', 'QNS', 'QNW', 'QTC', 'RAL', 'RBC', 'RCD', 'RCL',
    'RDP', 'REE', 'RGC', 'RHC', 'RIC', 'RLC', 'ROS', 'RSC', 'RTB', 'RTC',
    'S12', 'S27', 'S33', 'S4A', 'S55', 'S64', 'S72', 'S74', 'S91', 'S96',
    'S99', 'SAB', 'SAC', 'SAF', 'SAM', 'SAP', 'SAS', 'SAV', 'SB1', 'SBA',
    'SBC', 'SBD', 'SBG', 'SBH', 'SBL', 'SBR', 'SBS', 'SBT', 'SBV', 'SC5',
    'SCD', 'SCG', 'SCI', 'SCJ', 'SCL', 'SCO', 'SCR', 'SCS', 'SCY', 'SD1',
    'SD2', 'SD3', 'SD4', 'SD5', 'SD6', 'SD7', 'SD8', 'SD9', 'SDA', 'SDB',
    'SDC', 'SDD', 'SDE', 'SDF', 'SDG', 'SDH', 'SDI', 'SDJ', 'SDK', 'SDN',
    'SDP', 'SDT', 'SDU', 'SDV', 'SDX', 'SDY', 'SEB', 'SED', 'SEL', 'SFC',
    'SFG', 'SFI', 'SFN', 'SGC', 'SGD', 'SGH', 'SGN', 'SGO', 'SGR', 'SGT',
    'SHA', 'SHB', 'SHC', 'SHE', 'SHG', 'SHI', 'SHN', 'SHP', 'SHS', 'SHV',
    'SIC', 'SII', 'SIP', 'SJ1', 'SJC', 'SJD', 'SJE', 'SJF', 'SJG', 'SJM',
    'SJS', 'SKG', 'SKH', 'SKN', 'SKS', 'SKV', 'SLB', 'SLS', 'SMB', 'SMC',
    'SMN', 'SMT', 'SNC', 'SNG', 'SNZ', 'SON', 'SOS', 'SPI', 'SPM', 'SPS',
    'SQC', 'SRA', 'SRC', 'SRT', 'SSB', 'SSC', 'SSF', 'SSG', 'SSH', 'SSI',
    'SSM', 'SSN', 'SSS', 'SST', 'SSU', 'ST8', 'STC', 'STD', 'STG', 'STH',
    'STK', 'STL', 'STP', 'STS', 'STT', 'STW', 'SVC', 'SVD', 'SVG', 'SVH',
    'SVI', 'SVL', 'SVN', 'SVS', 'SVT', 'SZB', 'SZC', 'SZE', 'SZL',
    
    # HOSE (T-Z)
    'TAC', 'TAN', 'TAR', 'TAS', 'TAW', 'TBC', 'TBD', 'TBH', 'TBR', 'TBT',
    'TBW', 'TBX', 'TC6', 'TCD', 'TCH', 'TCI', 'TCJ', 'TCL', 'TCM', 'TCO',
    'TCR', 'TCS', 'TCT', 'TCW', 'TDB', 'TDC', 'TDF', 'TDG', 'TDH', 'TDM',
    'TDN', 'TDP', 'TDS', 'TDT', 'TDW', 'TEG', 'TET', 'TGG', 'TGP', 'THA',
    'THB', 'THD', 'THG', 'THI', 'THL', 'THN', 'THP', 'THS', 'THT', 'THU',
    'THV', 'THW', 'TID', 'TIG', 'TIP', 'TIS', 'TIX', 'TJC', 'TKA', 'TKC',
    'TKG', 'TKU', 'TLD', 'TLG', 'TLH', 'TLI', 'TLT', 'TMB', 'TMC', 'TMG',
    'TMP', 'TMS', 'TMT', 'TMW', 'TMX', 'TNA', 'TNC', 'TNG', 'TNH', 'TNI',
    'TNM', 'TNP', 'TNS', 'TNT', 'TNW', 'TOP', 'TOT', 'TOW', 'TPC', 'TPH',
    'TPP', 'TPS', 'TQN', 'TQW', 'TR1', 'TRA', 'TRC', 'TRI', 'TRS', 'TS3',
    'TS4', 'TS5', 'TSB', 'TSC', 'TSD', 'TSG', 'TSJ', 'TSM', 'TST', 'TTA',
    'TTB', 'TTC', 'TTD', 'TTE', 'TTF', 'TTG', 'TTH', 'TTJ', 'TTL', 'TTN',
    'TTP', 'TTR', 'TTS', 'TTT', 'TTZ', 'TUG', 'TV1', 'TV2', 'TV3', 'TV4',
    'TV6', 'TVA', 'TVB', 'TVC', 'TVD', 'TVG', 'TVH', 'TVM', 'TVN', 'TVP',
    'TVS', 'TVT', 'TVU', 'TVW', 'TXM', 'TYA', 'UCT', 'UDC', 'UDJ', 'UDL',
    'UEM', 'UIC', 'UMC', 'UNI', 'UPC', 'UPH', 'URC', 'V11', 'V12', 'V15',
    'V21', 'VAB', 'VAF', 'VAN', 'VAV', 'VBC', 'VBG', 'VBH', 'VCA', 'VCB',
    'VCC', 'VCE', 'VCF', 'VCG', 'VCH', 'VCI', 'VCM', 'VCP', 'VCR', 'VCS',
    'VCT', 'VCW', 'VCX', 'VDB', 'VDL', 'VDN', 'VDP', 'VDS', 'VE1', 'VE2',
    'VE3', 'VE4', 'VE8', 'VE9', 'VEA', 'VEC', 'VED', 'VEF', 'VES', 'VET',
    'VFC', 'VFG', 'VFR', 'VFS', 'VGC', 'VGG', 'VGI', 'VGL', 'VGP', 'VGR',
    'VGS', 'VGT', 'VGV', 'VHC', 'VHD', 'VHE', 'VHF', 'VHG', 'VHH', 'VHI',
    'VHL', 'VHM', 'VHN', 'VHP', 'VHS', 'VIB', 'VIC', 'VID', 'VIE', 'VIF',
    'VIG', 'VIH', 'VIM', 'VIN', 'VIP', 'VIR', 'VIS', 'VIT', 'VIW', 'VIX',
    'VJC', 'VKC', 'VKD', 'VKP', 'VLA', 'VLB', 'VLC', 'VLF', 'VLG', 'VLP',
    'VLW', 'VMA', 'VMC', 'VMD', 'VMG', 'VMI', 'VMS', 'VNA', 'VNB', 'VNC',
    'VND', 'VNE', 'VNF', 'VNG', 'VNH', 'VNI', 'VNL', 'VNM', 'VNN', 'VNP',
    'VNR', 'VNS', 'VNT', 'VNW', 'VNX', 'VNY', 'VNZ', 'VOC', 'VOS', 'VPA',
    'VPB', 'VPC', 'VPD', 'VPG', 'VPH', 'VPI', 'VPK', 'VPR', 'VPS', 'VPW',
    'VQC', 'VRC', 'VRE', 'VRG', 'VSA', 'VSC', 'VSE', 'VSF', 'VSG', 'VSH',
    'VSI', 'VSM', 'VSN', 'VSP', 'VST', 'VT1', 'VT8', 'VTA', 'VTB', 'VTC',
    'VTD', 'VTE', 'VTF', 'VTG', 'VTH', 'VTI', 'VTJ', 'VTK', 'VTL', 'VTM',
    'VTO', 'VTP', 'VTQ', 'VTR', 'VTS', 'VTV', 'VTX', 'VTZ', 'VUB', 'VUC',
    'VV2', 'VVN', 'VVS', 'VW3', 'VWS', 'VXB', 'VXP', 'VXT', 'WCS', 'WTC',
    'X18', 'X20', 'X26', 'X77', 'XDH', 'XHC', 'XLV', 'XMC', 'XMD', 'XMP',
    'XPH', 'YBC', 'YBM', 'YEG', 'YSC', 'YTC',
]


def quick_liquidity_check(code, lookback_days=30):
    """Quick check of recent liquidity (last 30 days)"""
    
    try:
        stock = Vnstock().stock(symbol=code, source='VCI')
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=lookback_days)
        
        df = stock.quote.history(
            symbol=code,
            start=start_date.strftime('%Y-%m-%d'),
            end=end_date.strftime('%Y-%m-%d')
        )
        
        if df.empty or len(df) < 10:
            return 0, False
        
        avg_volume = df['volume'].mean()
        is_liquid = avg_volume >= 100000
        
        return avg_volume, is_liquid
        
    except Exception as e:
        return 0, False


def filter_liquid_stocks(all_stocks, min_volume=100000, delay=1):
    """Filter stocks by liquidity"""
    
    print("\n" + "=" * 70)
    print("🔍 FILTERING BY LIQUIDITY")
    print("=" * 70)
    print(f"Checking: {len(all_stocks)} stocks")
    print(f"Criteria: Average volume > {min_volume:,} shares/day")
    print("=" * 70)
    print()
    
    liquid_stocks = []
    failed_stocks = []
    low_liquidity = []
    
    for i, code in enumerate(all_stocks, 1):
        print(f"[{i}/{len(all_stocks)}] {code}...", end=' ')
        
        time.sleep(delay)
        
        avg_vol, is_liquid = quick_liquidity_check(code, lookback_days=30)
        
        if avg_vol == 0:
            print("❌")
            failed_stocks.append(code)
        elif is_liquid:
            print(f"✅ {avg_vol:,.0f}")
            liquid_stocks.append({'code': code, 'avg_volume': avg_vol})
        else:
            print(f"⚠️  {avg_vol:,.0f}")
            low_liquidity.append(code)
        
        # Progress every 50
        if i % 50 == 0:
            print(f"\n💡 Progress: {i}/{len(all_stocks)} | Liquid: {len(liquid_stocks)}\n")
    
    liquid_stocks.sort(key=lambda x: x['avg_volume'], reverse=True)
    
    print("\n" + "=" * 70)
    print("✅ FILTER COMPLETE")
    print("=" * 70)
    print(f"✅ Liquid: {len(liquid_stocks)}")
    print(f"⚠️  Low: {len(low_liquidity)}")
    print(f"❌ Failed: {len(failed_stocks)}")
    
    if liquid_stocks:
        print(f"\n📊 Top 20:")
        for i, s in enumerate(liquid_stocks[:20], 1):
            print(f"   {i:2}. {s['code']}: {s['avg_volume']:>12,.0f}")
    
    return liquid_stocks


def save_list(liquid_stocks, filename='liquid_stocks_list.txt'):
    """Save list to text file"""
    
    os.makedirs('data', exist_ok=True)
    filepath = os.path.join('data', filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"# LIQUID STOCKS (>100k/day)\n")
        f.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"# Total: {len(liquid_stocks)}\n\n")
        
        for s in liquid_stocks:
            f.write(f"{s['code']}\t{s['avg_volume']:,.0f}\n")
    
    print(f"\n📝 Saved: {filepath}")


def main():
    """Main function"""
    
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--min-volume', type=int, default=100000)
    args = parser.parse_args()
    
    print("=" * 70)
    print("🚀 SIMPLE AUTO-FILTER")
    print("=" * 70)
    print(f"Stocks to check: {len(ALL_VIETNAM_STOCKS)}")
    print(f"Min volume: {args.min_volume:,}")
    print("=" * 70)
    
    # Filter
    liquid_stocks = filter_liquid_stocks(ALL_VIETNAM_STOCKS, args.min_volume)
    
    # Save
    save_list(liquid_stocks)
    
    print("\n" + "=" * 70)
    print("✅ DONE!")
    print("=" * 70)
    print(f"📝 List saved: data/liquid_stocks_list.txt")
    print(f"✅ Found {len(liquid_stocks)} liquid stocks")
    print("\nNext: Use this list for downloading full history")
    print("=" * 70)


if __name__ == '__main__':
    main()
