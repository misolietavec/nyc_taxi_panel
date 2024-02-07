import polars as pl
import panel as pn
import panel.widgets as pnw
import ipywidgets as ipw
from bokeh.io import curdoc as document # len kvoli nazvu v prehliadaci
from ipyleaflet import Map, MarkerCluster, CircleMarker
from data_functions_sk import dfdays, weekdays, pick_days, drop_days, pick_hours, drop_hours
from view_panel import play_hourly, df_for_map, view_distances, view_rtimes,\
                       meanloc, rides, view_shaded, view_hourly

pn.config.throttled = True
pn.extension('plotly','ipywidgets')

static_days = pn.Column(pick_days, drop_days)
static_hours = pn.Column(pick_hours, drop_hours)
static_weekdays = pn.Row(weekdays, width=800)

mapa =  Map(center=meanloc, layout=ipw.Layout(width='750px', height='450px'))
bod =  CircleMarker(location=meanloc, radius=6, visible=False)
body = MarkerCluster(markers=[bod] * 10, visible=False)
mapa.add(body)

day_choose = pnw.IntSlider(start=1, end=31, value=14, width=250, name='Deň')
hour_choose = pnw.IntSlider(start=0, end=23, value=11, width=300, name='Hodina')
day_player = pnw.DiscretePlayer(options=list(range(1, 32)), interval=300, value=1, show_loop_controls=False)
smer = pnw.RadioBoxGroup(options=['Nástup','Výstup'], inline=True)
# pre celkove grafy
day_or_hour = pnw.RadioBoxGroup(options=['Podľa dní','Podľa hodín', 'Dni v týždni (nástupy)'], inline=True)
# pre histogram vzdialenosti
nbins = pnw.IntSlider(start=10, end=120, value=20, width=250, name='Počet tried');

bind_hourly = pn.bind(play_hourly, value=day_player, direct=smer)
play_col = pn.Column(day_player, smer, bind_hourly)
bind_view_hourly = pn.bind(view_hourly, day=day_choose, direct=smer)


def view_totals(doh):
    return (static_days if doh == 'Podľa dní' else 
           (static_hours if doh == 'Podľa hodín' else static_weekdays))

bind_totals = pn.bind(view_totals, doh=day_or_hour)


def view_map(day, hour, direct):
    data, what = df_for_map(day, hour, direct)
    col_lat, col_lon = f'{what}_lat', f'{what}_lon'
    lat, lon = data[col_lat], data[col_lon]
    newcent = [lat.mean(), lon.mean()] if len(lat) else meanloc
    mapa.center = newcent
    marks = [CircleMarker(location=[lata, lona], radius=2) for lata, lona in zip(lat, lon)]
    body.markers = marks
    return mapa

bind_map = pn.bind(view_map, day=day_choose, hour=hour_choose, direct=smer)
bind_rides = pn.bind(rides, day=day_choose, hour=hour_choose, direct=smer)

bind_dist = pn.bind(view_distances, nb=nbins)
bind_rtimes = pn.bind(view_rtimes, nb=nbins)
dist_and_times = pn.Column(pn.Spacer(height=20), nbins, bind_dist, bind_rtimes)

bind_shaded = pn.bind(view_shaded, hour=hour_choose, direct=smer)
shaded_md = pn.pane.Markdown("### Všetkých 11 mil. zápisov, spracované cez datashader")
shaded = pn.Column(pn.Spacer(height=20), shaded_md, pn.Row(smer, hour_choose), bind_shaded)

nadpis = pn.pane.Markdown(
    f"""
    # Taxi v New Yorku
    ### Dáta z januára 2015, vzorka 155000 zápisov, celkovo je ich vyše 11 mil.
    """)
document().title = "NYC Taxi" # Nazov v prehliadaci
hourly = pn.Column(pn.Spacer(height=20), pn.Row(smer, day_choose), bind_view_hourly)
maps = pn.Column(pn.Spacer(height=20), pn.Row(smer, day_choose, hour_choose), 
                 pn.pane.Markdown(bind_rides), bind_map)
totals = pn.Column(pn.Spacer(height=20), day_or_hour, bind_totals)

tabs = pn.Tabs(('Grafy podľa dní', hourly), ('Grafy celkové', totals),
               ('Miesta na mape', maps), ('Histogramy', dist_and_times),
               ('Prehrávač', play_col), ('Datashader', shaded), dynamic=True)
pn.Column(nadpis, pn.Spacer(height=25), tabs).servable()
