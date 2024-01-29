import polars as pl
import panel as pn
import numpy as np
import panel.widgets as pnw
import plotly.express as px
import ipywidgets as ipw
from bokeh.io import curdoc as document # len kvoli nazvu v prehliadaci
from data_functions_sk import make_graphs, static_graphs
from ipyleaflet import Map, MarkerCluster, CircleMarker
from PIL import Image
pn.config.throttled = True
pn.extension('plotly','ipywidgets')

df = pl.read_parquet('data/nyc_taxi155k.parq')
meanloc = [df['pick_lat'].mean(), df['pick_lon'].mean()]

pick_days, drop_days, pick_hours, drop_hours = static_graphs(df)
static_days = pn.Column(pick_days, drop_days)
static_hours = pn.Column(pick_hours, drop_hours)

dfdays = make_graphs(df, create=False)  # grafy predrobene uz pre tento vyber

day_choose = pnw.IntSlider(start=1, end=31, value=14, width=250, name='Deň')
hour_choose = pnw.IntSlider(start=0, end=23, value=11, width=300, name='Hodina')
day_player = pnw.DiscretePlayer(options=list(range(1, 32)), interval=300, value=1, show_loop_controls=False)
smer = pnw.RadioBoxGroup(options=['Nástup','Výstup'], inline=True)
# pre celkove grafy
day_or_hour = pnw.RadioBoxGroup(options=['Podľa dní','Podľa hodín'], inline=True)
# pre histogram vzdialenosti
nbins = pnw.IntSlider(start=10, end=120, value=20, width=250, name='Počet tried');


def play_hourly(value, dnuvon):
    graf = dfdays[value]['pick_graph'] if dnuvon == 'Nástup' else dfdays[value]['drop_graph']
    graf.update_layout(title='')
    graf.update_yaxes(range=[0, 750])  # odhad z grafov
    return graf
    

bind_hourly = pn.bind(play_hourly, value=day_player, dnuvon=smer)
play_col = pn.Column(day_player, smer, bind_hourly)


@pn.depends(day_choose, smer)
def view_hourly(day_choose, smer):
    if smer == 'Nástup':
        return dfdays[day_choose]['pick_graph']
    return dfdays[day_choose]['drop_graph']


@pn.depends(day_or_hour)
def view_totals(day_or_hour):
    return static_days if day_or_hour == 'Podľa dní' else static_hours


mapa =  Map(center=meanloc, layout=ipw.Layout(width='750px', height='450px'))
bod =  CircleMarker(location=meanloc, radius=6, visible=False)
body = MarkerCluster(markers=[bod] * 10, visible=False)
mapa.add(body)


@pn.depends(day_choose, hour_choose, smer)
def filtered_df(day_choose, hour_choose, smer):
    pick_df = df.filter((pl.col('pick_day') == day_choose) &
                        (pl.col('pick_hour') == hour_choose)) 
    drop_df = df.filter((pl.col('drop_day') == day_choose) &
                        (pl.col('drop_hour') == hour_choose))
    data, what = (pick_df, 'pick') if smer == 'Nástup' else (drop_df, 'drop')
    return data, what


@pn.depends(day_choose, hour_choose, smer)
def view_map(day_choose, hour_choose, smer):
    data, what = filtered_df(day_choose, hour_choose, smer)
    col_lat, col_lon = f'{what}_lat', f'{what}_lon'
    lat, lon = data[col_lat], data[col_lon]
    newcent = [lat.mean(), lon.mean()] if len(lat) else meanloc
    mapa.center = newcent
    marks = [CircleMarker(location=[lata, lona], radius=2) for lata, lona in zip(lat, lon)]
    body.markers = marks
    return mapa


@pn.depends(day_choose, hour_choose, smer)
def rides(day_choose, hour_choose, smer):
    data, what = filtered_df(day_choose, hour_choose, smer)
    return pn.pane.Markdown(f"### Počet jázd: {data.shape[0]}")


@pn.depends(nbins)
def view_distances(nbins): 
    y, x = np.histogram(df['distance'], bins=nbins, range=(0, 8))
    x = (x[0:-1] + x[1:]) / 2  # stredy intervalov
    df_hist = pl.DataFrame({'x': x, 'y': y}) # , 'zaokrúhlené': yr})
    return px.bar(data_frame=df_hist, x='x', y='y', #  'zaokrúhlené'], 
                  barmode='group', labels={'x': 'Vzdialenosť (km)', 'y': 'početnosť',
                                           'variable': 'hodnota'}, width=900, height=350)

@pn.depends(nbins)
def view_rtimes(nbins):
    y, x = np.histogram(df['rtime'], bins=nbins, range=(0, 45)) # min.
    x = (x[0:-1] + x[1:]) / 2  # stredy intervalov
    df_hist = pl.DataFrame({'x': x, 'y': y}) # , 'zaokrúhlené': yr})
    return px.bar(data_frame=df_hist, x='x', y='y', 
                  barmode='group', labels={'x': 'Čas jazdy (min.)', 'y': 'početnosť',
                                           'variable': 'hodnota'}, width=900, height=350)
dist_and_times = pn.Column(pn.Spacer(height=20), nbins, view_distances, view_rtimes)


pick_images, drop_images = {}, {}
for hour in range(24):
    pick_images[hour] = Image.open(f'images/pick_{hour:02d}.jpg')
    drop_images[hour] = Image.open(f'images/drop_{hour:02d}.jpg')


@pn.depends(hour_choose, smer)
def view_shaded(hour_choose, smer):
    images = pick_images if (smer == 'Nástup') else drop_images
    return images[hour_choose]
shaded_md = pn.pane.Markdown("### Všetkých 11 mil. zápisov, spracované cez datashader")
shaded = pn.Column(pn.Spacer(height=20), shaded_md, pn.Row(smer, hour_choose), view_shaded)


nadpis = pn.pane.Markdown(
    f"""
    # Taxi v New Yorku
    ### Dáta z januára 2015, vzorka 155000 zápisov, celkovo je ich vyše 11 mil.
    """)
document().title = "NYC Taxi" # Nazov v prehliadaci
hourly = pn.Column(pn.Spacer(height=20), pn.Row(smer, day_choose), view_hourly)
maps = pn.Column( pn.Spacer(height=20), pn.Row(smer, day_choose, hour_choose), rides, view_map)
totals = pn.Column(pn.Spacer(height=20), day_or_hour, view_totals)

tabs = pn.Tabs(('Grafy podľa dní', hourly), ('Grafy celkové', totals),
               ('Miesta na mape', maps), ('Histogramy', dist_and_times),
               ('Prehrávač', play_col), ('Datashader', shaded), dynamic=True)
pn.Column(nadpis, pn.Spacer(height=25), tabs).servable()
