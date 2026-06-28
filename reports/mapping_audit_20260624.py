import sys
from pathlib import Path
import pandas as pd

ROOT=Path('/home/mysktelecom/workplace/nps-ops-dashboard')
sys.path.insert(0, str(ROOT/'src'))
sys.path.insert(0, str(ROOT))
from nps_ops.config import RAW_DIR, MAPPING_FILE
from nps_ops.parser import parse_workbook, extract_report_date
from scripts.build_data import find_latest_file, load_store_mapping, _norm_code

path=find_latest_file(RAW_DIR)
print('SOURCE', path)
print('REPORT_DATE', extract_report_date(path))
parsed=parse_workbook(path)
mapdf=load_store_mapping(MAPPING_FILE)
print('MAPPING rows', len(mapdf), 'teams', mapdf['map_team_name'].astype(str).str.strip().value_counts().to_dict())
map_codes=set(mapdf['store_code_norm'].dropna().astype(str))
map_jb=mapdf[mapdf['map_team_name'].astype(str).str.strip().eq('전북')].copy()
map_jb_codes=set(map_jb['store_code_norm'].dropna().astype(str))
print('MAPPING_JEONBUK stores', len(map_jb_codes), 'agencies', map_jb['map_agency_name'].nunique())

store=parsed['store_agg'].copy()
store['store_code_norm']=_norm_code(store['store_code'])
store_team=store[store['team_name'].astype(str).str.strip().eq('전북')].copy()
store_team_codes=set(store_team['store_code_norm'].dropna().astype(str))
print('RAW_STORE_AGG_JEONBUK rows', len(store_team), 'stores', len(store_team_codes), 'agencies', store_team['agency_name'].nunique())
print('STORE_AGG 전북 총응답', int(pd.to_numeric(store_team['total_responses'], errors='coerce').fillna(0).sum()))

missing_in_mapping = sorted(store_team_codes - map_codes)
missing_in_mapping_jb = sorted(store_team_codes - map_jb_codes)
extra_mapping_jb = sorted(map_jb_codes - store_team_codes)
print('JEONBUK_STORE_AGG_CODES_NOT_IN_MAPPING_ANY_TEAM', len(missing_in_mapping), missing_in_mapping[:20])
print('JEONBUK_STORE_AGG_CODES_NOT_IN_MAPPING_JEONBUK', len(missing_in_mapping_jb), missing_in_mapping_jb[:20])
print('MAPPING_JEONBUK_CODES_NOT_IN_STORE_AGG_TODAY', len(extra_mapping_jb), extra_mapping_jb[:20])

for name in ['response_fact','negative_feedback']:
    df=parsed[name].copy()
    df['store_code_norm']=_norm_code(df['store_code'])
    df['raw_team']=df.get('team_name', pd.Series(['']*len(df))).astype(str).str.strip()
    df['raw_agency']=df.get('agency_name', pd.Series(['']*len(df))).astype(str).str.strip()
    df['raw_store']=df.get('store_name', pd.Series(['']*len(df))).astype(str).str.strip()
    df['matched_any']=df['store_code_norm'].isin(map_codes)
    df['matched_jb_mapping']=df['store_code_norm'].isin(map_jb_codes)
    df['in_store_agg_jb']=df['store_code_norm'].isin(store_team_codes)
    unmatched=df[df['store_code'].notna() & ~df['matched_any']].copy()
    print('\nTABLE', name)
    print(' rows', len(df), 'unmatched_any rows', len(unmatched), f"rate={len(unmatched)/len(df):.2%}" if len(df) else '')
    print(' unmatched unique codes', unmatched['store_code_norm'].nunique())
    print(' unmatched raw_team counts top10', unmatched['raw_team'].value_counts(dropna=False).head(10).to_dict())
    crit1=unmatched[unmatched['raw_team'].eq('전북')]
    crit2=unmatched[unmatched['in_store_agg_jb']]
    print(' CRITICAL unmatched rows with raw_team==전북:', len(crit1), 'unique_codes', crit1['store_code_norm'].nunique())
    print(' CRITICAL unmatched rows whose code appears in 전북 매장별 64:', len(crit2), 'unique_codes', crit2['store_code_norm'].nunique())
    if len(crit1) or len(crit2):
        cols2=['store_code_norm','raw_team','raw_agency','raw_store']
        print(' critical sample:')
        print(pd.concat([crit1[cols2], crit2[cols2]]).drop_duplicates().head(50).to_string(index=False))
    for label, sub in [('raw_team_전북', df[df['raw_team'].eq('전북')]), ('code_in_store_agg_전북64', df[df['in_store_agg_jb']]), ('code_in_mapping_전북', df[df['matched_jb_mapping']])]:
        print(f' {label}: rows={len(sub)} stores={sub.store_code_norm.nunique()} agencies={sub.raw_agency.nunique()} unmatched_any_rows={(~sub.matched_any & sub.store_code.notna()).sum()}')

print('\nJEONBUK_STORE_AGG_64_BY_AGENCY')
print(store_team.groupby('agency_name', dropna=False).agg(stores=('store_code_norm','nunique'), responses=('total_responses','sum')).sort_index().to_string())

out=ROOT/'reports'/'mapping_audit_20260624'
out.mkdir(parents=True, exist_ok=True)
cols=['store_code_norm','team_name','agency_code','agency_name','store_name','total_responses','sales_total_responses','non_sales_total_responses']
store_team[cols].sort_values(['agency_name','store_name']).to_csv(out/'jeonbuk_store_agg_64.csv', index=False, encoding='utf-8-sig')
for name in ['response_fact','negative_feedback']:
    df=parsed[name].copy(); df['store_code_norm']=_norm_code(df['store_code'])
    df['raw_team']=df.get('team_name', pd.Series(['']*len(df))).astype(str).str.strip()
    df['raw_agency']=df.get('agency_name', pd.Series(['']*len(df))).astype(str).str.strip()
    df['raw_store']=df.get('store_name', pd.Series(['']*len(df))).astype(str).str.strip()
    df['matched_any']=df['store_code_norm'].isin(map_codes)
    u=df[df['store_code'].notna() & ~df['matched_any']]
    (u.groupby(['store_code_norm','raw_team','raw_agency','raw_store'], dropna=False).size().reset_index(name='rows')
      .sort_values(['raw_team','rows'], ascending=[True,False])
      .to_csv(out/f'{name}_unmatched_codes.csv', index=False, encoding='utf-8-sig'))
print('REPORT_DIR', out)
