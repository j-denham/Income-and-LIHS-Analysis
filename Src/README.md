## Source Code

#### Centrelink Benefits
* `rent_proportion_processor.py` contains the code for the processing for bedrooms by dwelling type and weekly rent by dwelling
type in order to obtain an average weekly rent value per person. In addition, the function for calculating the cost of living
proportion from the processed data can be found here
* `rent_proportion_analysis.py` contains the code for plotting the cost of living proportion by year and SA2, along with predicting
the rent, and thus cost of living proportion for 2021 from the 2016 census values and quarterly CPI


#### Correlations
* `find_correlations.py` is the main file where all the datasets are combined, analysed, and plotted.
  The most interesting functions are:
    * `get_aedc_data` gets the AEDC datasets, merges them together, and reshaping.
    * `get_aurin_LIHS_data` gets the other datasets and performs some basic preprocessing.
    * `get_LIHS_data` merges the datasets that we are going to use and modifies the SA2 codes to be the same format.
    * `get_LIHS_from_csv` reads a csv file obtained from AURIN and fixes up the column names to be human readable.
    * `find_correlations` computes the correlations strengths between income and LIHS metrics. Also plots highly correlated metrics.
    * `plot_metric_against_income` creates the scatter plots for correlated metrics.
* `average-2011` and `average-2016` contains code to preprocess individual weekly incomes.
