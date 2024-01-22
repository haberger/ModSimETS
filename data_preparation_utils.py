import pandas as pd
import numpy as np

def get_allocation_over_years(austrian=False, years = range(2008, 2023), path='./data/data_2008-2022.xlsx'):
    df_free_allowances = pd.read_excel(path, header=21)

    if austrian:
        df_free_allowances = df_free_allowances[df_free_allowances.REGISTRY_CODE == 'AT']
        
    df_free_allowances.columns = [c if 'ALLOCATION_' in c else c.replace('ALLOCATION', 'ALLOCATION_') for c in df_free_allowances.columns]
    allowance_cols = [c for c in df_free_allowances.columns if 'VERIFIED_EMISSIONS_2' in c or 'ALLOCATION_2' in c]
    df_free_allowances = df_free_allowances.replace('Excluded', np.nan)
    df_free_allowances[allowance_cols] = df_free_allowances[allowance_cols].astype(float)

    for year in years:
        df_free_allowances[f'ALLOCATION_DIFF_{year}'] = df_free_allowances[f'VERIFIED_EMISSIONS_{year}'] - df_free_allowances[f'ALLOCATION_{year}']
        df_free_allowances[f'ALLOCATION_DIFF_NORM_{year}'] = df_free_allowances[f'ALLOCATION_DIFF_{year}'] / df_free_allowances[f'VERIFIED_EMISSIONS_{year}']

    # df_free_allowances = df_free_allowances.drop(columns=['REGISTRY_CODE', 'IDENTIFIER_IN_REG', 'INSTALLATION_IDENTIFIER', 'PERMIT_IDENTIFIER', 'MAIN_ACTIVITY_TYPE_CODE'])
    return df_free_allowances


def get_allocation_melted(df_free_allowances, filter_out_non_verified_emissions=True):
    id_cols = ['REGISTRY_CODE', 'IDENTIFIER_IN_REG', 'INSTALLATION_NAME',
        'INSTALLATION_IDENTIFIER', 'PERMIT_IDENTIFIER',
        'MAIN_ACTIVITY_TYPE_CODE']
    # id_cols = ['INSTALLATION_NAME', 'ACTIVITY_TYPE']

    stubnames = ['ALLOCATION_', 'ALLOCATION_RESERVE_', 'ALLOCATION_TRANSITIONAL_', 'ALLOCATION_DIFF_', 'CH_ALLOCATION_',
             'VERIFIED_EMISSIONS_', 'CH_VERIFIED_EMISSIONS_', 'ALLOCATION_DIFF_NORM_']
    
    df_free_allowances_melted = pd.wide_to_long(df_free_allowances, stubnames=stubnames, i=id_cols, j='year')
    df_free_allowances_melted = df_free_allowances_melted.reset_index(drop=False)

    for c in df_free_allowances_melted.columns:
        if filter_out_non_verified_emissions:
            if c == 'ALLOCATION_' or c == 'VERIFIED_EMISSIONS_':
                df_free_allowances_melted = df_free_allowances_melted[df_free_allowances_melted[c] != -1]
    return df_free_allowances_melted


def get_totals_by_year(df, cols=['ALLOCATION_', 'VERIFIED_EMISSIONS_']):
    df = pd.DataFrame(df.groupby('year')[cols].sum()).reset_index(drop=False)
    df.columns = ['year'] + [f'{c}TOTAL' for c in cols]
    return df


def get_activity_df(path='./data/data_activity_type.xlsx'):
    df_activity = pd.read_excel(path)
    df_activity = df_activity.rename(columns={'Installation Name': 'INSTALLATION_NAME', 'Activity Type': 'ACTIVITY_TYPE'})[['INSTALLATION_NAME', 'ACTIVITY_TYPE']]
    df_activity['INSTALLATION_NAME'] = df_activity['INSTALLATION_NAME'] + ''
    return df_activity


def add_activity_info(df, df_activity):
    df = df.merge(df_activity, on='INSTALLATION_NAME', how='left')
    df.loc[df.ACTIVITY_TYPE.isna(), 'ACTIVITY_TYPE'] = 'Unknown'
    return df