import os
import re
import json
from textwrap import wrap
import base64
import hashlib

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path



## Uses a "brute-force" method to find correlations between income data and
## LIHS metrics within SA2 region, ranked by Pearson correlation coefficient. 

# TODO: Plot scatter graph of Income vs. Metric Outcomes

def find_correlations_multiyear(years):
    corrs_all = pd.DataFrame()
    for year in years:
        data = get_LIHS_data(year) 
        income = get_income_data(year)
        corr = find_correlations(data, income, year)
        corr = corr.rename("{} {}".format(corr.name, year))
        if corrs_all.empty: 
            corrs_all = corr
        else: 
            corrs_all = pd.concat([corrs_all, corr],axis=1)
            
    corrs_all.sort_values('Correlation Strength {}'.format(year))
    return corrs_all

def get_LIHS_data(year):
    # {'income year':'corresponding aedc year'}
    aedc_years = {
        '2011':'2012',
        '2016':'2015'
    }
    aedc_data = get_aedc_data_by_year(aedc_years[year])
    aurin_data = get_aurin_LIHS_data(year)
    # Change aurin_data from 9-digit SA2 Code to 5-digit
    aurin_data.index = aurin_data.index.map(lambda x: int(str(x)[0] + str(x)[-4:]))
    all_data = pd.merge(aedc_data, aurin_data, on='SA2 Code')
    return all_data

def get_aurin_LIHS_data(year):
    aurin_LIHS_files = {
        '2011':['Family-and-Community-2011.csv'],
        '2016':['Family-and-Community-2016.csv']
        }
    data = pd.DataFrame()
    for csv_filename in aurin_LIHS_files[year]:
        temp_LIHS_df = get_LIHS_from_csv(csv_filename) # Retrieve LIHS dataframe
        if data.empty:
            data = temp_LIHS_df
        else:
            data = pd.merge(data, temp_LIHS_df, on='SA2 Code') # Merge all
    return data

def get_LIHS_from_csv(filename):
    data_path = '../Datasets/' + filename                  # csv filepath
    metadata_path = data_path[0:-4] + '-metadata.json'  # json filepath
    df = pd.read_csv(data_path)                     # read csv
    file = open(metadata_path)                      # read json
    metadata = json.load(file)                      # load json
    for heading in df.columns:                      # for each column
        heading_nospace = heading.replace(" ", "")  # Remove whitespace
        for D in metadata['selectedAttributes']:    # In each dictionary...
            if heading_nospace == D['name']:        # If 'ugly name' match found
                df.rename({heading:D['title']}, axis=1, inplace=True)
                break
    # Manual heading and type cleanup
    df.rename({'SA2 Code (ASGS 2016).':'SA2 Code'}, axis=1, inplace=True)
    df['SA2 Code'] = df['SA2 Code'].astype(int)
    df.set_index('SA2 Code', inplace=True)
    return df

def find_correlations(data, income, year):
    corrs = data.corrwith( 
        income.loc[:,'Weekly Household Income'], # Series
        method='pearson')
    corrs.index.rename(name='LIHS Metric', inplace=True)
    corrs = corrs.sort_values(ascending=False)
    corrs = corrs.rename('Correlation Strength', inplace=True)
    pd.Series.drop(corrs, ['Year'], inplace=True)   # Drop rows (Series only)

    # Determine which metrics to plot, then plot them.
    metrics_to_plot = data[corrs[corrs.abs() > 0.4].index]
    # merge with income to align them for plotting. probs a better way to do this.
    income_aligned = metrics_to_plot.merge(income, on='SA2 Code')['Weekly Household Income']
    # plot each metric
    for metric in metrics_to_plot:
        plot_metric_against_income(
            metrics_to_plot[metric],
            income_aligned,
            corrs[metric],
            year
        )

    return corrs

def get_income_data(year):
    data = pd.read_csv('../Datasets/income_{}.csv'.format(year),
                        dtype=str, na_values='null')
    data.columns = data.columns.str.strip() # Clean heading names
    
    # Remove irrelevant cols. 
    data = data.loc[:,[
        'sa2_maincode_2016',
        'equivalised_total_household_income_census_median_weekly'
        ]
    ]
    
    # Rename relevant cols.
    data.columns = ['SA2 Code', 'Weekly Household Income']
    
    # convert type. should be int, but there are some null values so we use float
    data = data.astype({
        'Weekly Household Income': float,
        'SA2 Code': int
        })
    data.set_index('SA2 Code', inplace=True)
    data.index = data.index.map(lambda x: int(str(x)[0] + str(x)[-4:]))
    return data

def write_final_output_to_csv(data):
    output_folder = Path('../OutputCSV/')
    output_folder.mkdir(parents=True, exist_ok=True) # Make output folder  
    data.to_csv(
        '../OutputCSV/Income-LIHS Correlations ({}).csv'.format(', '.join(years))
        )

def get_aedc_data():
    files = Path('../Datasets/AEDC').glob('*.csv')
    data = []
    for file in files:
        domain_name = file.stem.replace('_', ' ')
        raw_df = get_LIHS_from_csv(str(file.relative_to('../Datasets')))
        # raw_df = raw_df.set_index('SA2 Code')
        # get a df of just the percentage data
        df_cols = list(filter(lambda x: '(%)' in x, raw_df.columns.values))
        df = raw_df[df_cols]
        # extract years from col names
        df.columns = df.columns.map(lambda x: (' '.join(x.split()[:-1]), x.split()[-1]))
        # stack records
        df = df.stack([0, 1]).reset_index()
        df.columns = ['SA2 Main Code', 'Status', 'Year', 'Percentage']
        # add on domain type
        df['Domain'] = 'AEDC - ' + domain_name
        # save the df
        data.append(df)

    data = pd.concat(data)
    return data

def get_aedc_data_by_year(year):
    data = get_aedc_data()
    data = data[data['Year'] == year]
    # reshape so SA2 codes are the index
    data = data.pivot(index='SA2 Main Code', columns=['Domain', 'Status'], values='Percentage')
    data.columns = data.columns.map(lambda x: '{} - {}'.format(*x))
    data.index.rename('SA2 Code', inplace=True)
    return data

def plot_metric_against_income(metric, income, strength, year):
    plt.clf()
    plt.scatter(income, metric, color='green', s=5)
    plt.xscale('linear')
    plt.yscale('linear')
    #plt.tick_params(bottom=False, labelbottom=False)
    plt.xlabel('Weekly Household Income ($AUD)')
    plt.ylabel('Measured Metric ' + metric.name.split()[-1])
    plt.title('\n'.join(wrap('Income Versus {} ({})'.format(metric.name, year), 60)))
    # put in corr strength
    plt.text(
        0.95, 0.05,
        'Correlation Strength: {:.4f}'.format(strength),
        transform=plt.gca().transAxes,
        ha='right',
        bbox={
            'boxstyle': 'round',
            'facecolor': 'white',
            'alpha': 0.5
        }
    )

    plt.tight_layout()
    #plt.grid(True)
    output_folder = Path('../Plots/Corrs')
    output_folder.mkdir(parents=True, exist_ok=True)
    plt.savefig(fname=Path('../Plots/Corrs/{}_{}_{}.png'.format(
        create_friendly_filename(metric.name),
        year,
        # collision prevention
        base64.urlsafe_b64encode(
            hashlib.sha1(metric.name.encode('utf-8')).digest()
        )[:5].decode()
    )))

def create_friendly_filename(metric_name):
    return re.sub(r'[^\w-]', '-', metric_name)[:30]

if __name__ == '__main__':
    os.chdir(Path(__file__).parent) # Set working directory to script location
    years = ['2011', '2016']
    df = find_correlations_multiyear(years)
    write_final_output_to_csv(df)