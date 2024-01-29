## Data analysis workshop for beginners (PyCon SK 2024?)

We will use `NYC taxi dataset`, data from January, 2015. This is modified
dataset from https://s3.amazonaws.com/datashader-data/nyc_taxi_wide.parq
used in `holoviz` ecosystem https://holoviz.org/. Column names are
shortened, instead of `datetime` column we use separate `hour` and `day` columns
(for passengers pickup and dropoff). For workshop we will need only the sample of
155000 records (`data/nyc_taxi155k.parq`). Full modified dataset is
available at https://feelmath.eu/Download/nyc_taxi.parq.

For running the notebook `taxi_panel.ipynb` the modules `panel, ipyleaflet,
fastparquet, plotly` need to be installed. 

File `datashader_images.py` is here only to show, how the images in `images/` folder
were generated.
