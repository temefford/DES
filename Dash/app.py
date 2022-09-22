# -*- coding: utf-8 -*-
"""
Created on Fri Oct  5 12:48:10 2018
@author: Aveedibya Dey
"""
import numpy as np
import datetime as dt
import pandas as pd

import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
from dash.dependencies import Input, Output, State

#Internal package with functions and classes
import call_vrad_gen as cvg

#-------------------------------
app = dash.Dash(meta_tags=[{
        'name': 'description',
        'content': 'An illustrative tool to evaluate call waiting times based on simulated call arrival pattern and agent allocation. The interactive\
 graphical output shows expected interval brand promise and call waiting time impact. Agent allocation is also shown graphically.'},
        {'name': 'author',
         'content': 'Theodore Mefford'}])
app.title = 'Teleradiology Netword Simulator'
server = app.server

#-------------------------------
#Define Formatting Stuff
margin={'l':50, 'b':40, 'r':40, 't':40}
yaxis = dict(zeroline = False)
xaxis = dict(zeroline = False)

def graphingRegion(height, margin=margin):
        return {'data':[], 
                'layout': go.Layout(height=height, 
                                    margin=margin, 
                                    yaxis = dict(zeroline = False, showticklabels=False, showgrid=False),
                                    xaxis = dict(zeroline = False, showticklabels=False, showgrid=False),
                                    font=dict(family='Dosis')
                                    )
                }

intro_text = '''##### About this Simulator:
This simulator was built to provide an interactive platform for running simulations on 
different staffing and scheduling scenarios. The simulator lets you input the following parameters:

- __Number of Agents:__ Enter the number of agents staffed. Current assumption is that all these agents
are staffed 24x7. This is not practical, however, it is equivalent to having a flat staff throughout the day.
A more efficient system will call for different schedules assigned to different agents to meet the changing workload demand.
This scenario will be built in future versions, but can be easily integrated in this simulator.
- __Peak Call Count:__ Lets you enter the maximum expected number of calls in an half-hour interval. Using this input, 
a call distribution is built for the entire day, assuming linear increase in the average number of calls to the peak value and then
a linear decrease in average calls. Once the average call distribution is built, actual call counts are calculated based on a random draw
from a poisson distribution assuming the average calls for that interval is based on the distribution previously generated.
- __Average Handling Time (Lower and Upper bounds):__ The average handling time or AHT includes the total time spent by agents on a call and two inputs
are taken from the user - minimum and maximum AHT expected throughout the day. Using these lower and upper bounds a random draw allows the simulator
to assign a call aht to each call in every interval. 

Once the above inputs are available, calls are generated with AHT assigned to each. These calls are then allocated to agents. Agent allocation is usually
random for agents in idle status, but if no agents are available in an interval, then the call is assigned to the agent who is available at the earliest 
to reduce the call wait time. This assignment is based on a first-in first-out assignment where the calls are sequentially queued and the first call to arrive 
will be handled first. 

__Go ahead and enter any combination of parameters you would like!__

_If you are not sure what to enter, try this: `Number of agents: 3, Peak call count: 20, AHT Lower Bound: 200, AHT Upper Bound: 250`_ 

'''
        
text_to_show = '''###### Simulation Results:

Below parameters show a summary of the statistics from the simulation that was run:

 1. __Calls: {}__
   - Total Calls: __{:.0f}__
   - Avg. Handling Time (AHT): __{:.1f} sec__
   - AHT Range in Simulation: __{:.0f}-{:.0f} sec__
   - Call Wait Time Range: __{:.1f}-{:.1f} sec__

 2. __Agent Statistics:__  
   - Total number of agents staffed: __{:.0f}__
   - All agents were assumed to be staffed 24x7

'''
#To see a distribution at an interval level, refer charts shown below. 

footnote_markdown = '''
Created by: Theo Mefford | [Source Code](https://github.com/temefford) | Original code by Aveedibya Dey
    '''

#-------------------------------
#App Layout
app.layout = html.Div(
    html.Div([
        html.H3('Teleradiology Network Simulator Dashboard'),
        
        dcc.Interval(
            id='interval-component',
            interval=1*100, # in milliseconds
            n_intervals=0,
            max_intervals=600
        ), 
        html.Div(html.H6(id='animated-subtitle', children=' ', style={'line-height': '1.1', 'color': 'rgb(0, 153, 255)'})),
        
        html.Div([html.Div([html.H4('Enter Simulation Parameters:'), 
                            html.Button('Run Simulation', id='begin-simulation')], style={'width': '25%', 'display': 'inline-block'}), 
                  html.Div([html.Label('Number of Radiologists:'), 
                            dcc.Input(id='rads-count', type='number', step=.1, placeholder='#Radiologists'),
                            html.Label('Image Arrival Rate:'), 
                            dcc.Input(id='arr-rate', type='float', step=.1, placeholder='mins between images')], style={'width': '25%', 'display': 'inline-block'}),
                  html.Div([html.Label('avg urgent time:'), 
                            dcc.Input(id='urg-time', type='float', step=0.1, placeholder='minutes'),
                            html.Label('non-urgent time:'), 
                            dcc.Input(id='non-time', type='float', step=50, placeholder='minutes')], style={'width': '25%', 'display': 'inline-block'}),
                  ], style={'border': 'thin lightgrey solid', 'paddingLeft': '40', 'paddingBottom': '20', 'paddingTop': '10', 'backgroundColor': '', 'marginBottom': '5'}
                ),
                  
        html.Div(id='intro-text-above-graph', children=(dcc.Markdown(intro_text)), style={'backgroundColor': 'rgb(212,212,212,0.5)', 'padding': '10', 'marginTop': '1%'}),
        
        html.Div(id='graph-block', children=[
        #---
        #Image Count Graph
        html.Div([html.Div([dcc.Graph(id='live-update-graph', config={'displayModeBar': False}, figure=graphingRegion(450), clear_on_unhover=True, hoverData={'points':[{'customdata': 'showall'}]})], style={'width': '69%', 'display': 'inline-block'}),
                  html.Div(dcc.Markdown(id='simulation-details'), style={'width': '29%',  'fontSize': '80%', 'display': 'inline-block', 'verticalAlign': 'top', 'padding': '5', 'paddingTop': '10'})]),
        #---
        #Image Wait Time and Completion Graphs
        html.Div([dcc.Graph(id='img-wait-time-graph', config={'displayModeBar': False}, figure=graphingRegion(225)),
                  dcc.Graph(id='sucess-graph', config={'displayModeBar': False}, figure=graphingRegion(225))], style={'width': '49%', 'display': 'inline-block'}),
        #---
        #Radiologist Status Graph
        html.Div([dcc.Graph(id='rad-view-graph', config={'displayModeBar': False}, figure=graphingRegion(450))], style={'width': '49%', 'display': 'inline-block', 'padding': '5'}),
        
        #---
        #Hidden elements storing intermediate dataframes in json 
        html.Div(id='img_table', style={'display':'none'}),
        html.Div(id='rad_table', style={'display':'none'})
        ], style={}),
                  
        html.Div(id='intro-text-below-graph', children=(dcc.Markdown(intro_text)), style={'display': 'none'}),
        
        #---------
        #Footnote
        html.Div([dcc.Markdown(footnote_markdown)], 
                  style={'borderTop': 'thin lightgrey solid', 'textAlign': 'center', 'padding': '10', 'fontSize': 'small'})
        
    ]), className= 'container'
)



#=====================================
#APP CALLBACK FUNCTIONS
#=====================================

@app.callback(Output('animated-subtitle', 'children'),
              [Input('interval-component', 'n_intervals')])
              
def update_subtitle(n):
    '''
    '''
    subtitle_text = 'EASILY RUN SIMULATIONS, GET DEEPER INSIGHTS' 
    if n%60 > 0 :
        return subtitle_text[:n%60] + '|'
    else:
        if n == 600 :
            return subtitle_text
        else:
            return '|'
    
#--------------------------------------------------
#Generate Text Section: Read Inputs and Update Text
#--------------------------------------------------
@app.callback(Output('simulation-details', 'children'),
              [Input('rad_table', 'children'),
               Input('rads-count', 'value'), 
               Input('arr-rate', 'value'), 
               Input('urg-time', 'value'),
               Input('non-time', 'value'),
               Input('live-update-graph', 'hoverData')]
               )
                  
def update_info_text(img_table_json, rads_count, arr_rate, urg_time, non_time, time_filter):
    '''
    '''
    print('-----time filter----------:', time_filter)
    img_table_df = pd.read_json(img_table_json, orient='split')
    if time_filter is not None:
        if time_filter['points'][0]['customdata'] != 'showall':
            current_hover = dt.datetime.strptime(time_filter['points'][0]['customdata'], "%Y-%m-%d %H:%M:%S")
            call_table_df = call_table_df[call_table_df['intvl_time_elapsed']==cvg.timeElapsed(current_hover)]
            show_filter_text = '(for ' + str(current_hover.time()) + ' to ' + str(cvg.timeAddition(current_hover.time(),[0,30,0])) + ')'
        else:
            show_filter_text = '(for 24 hrs)'
    else:
        show_filter_text = '(for 24 hrs)'
    #print(call_table_df)
    img_count = len(img_table_df)
    wait_min = min(img_table_df['img_wait_time_elapsed'])
    wait_max = max(img_table_df['img_wait_time_elapsed'])
    aht_lower_actual = min(img_table_df['img_avg_t'])
    aht_upper_actual = max(img_table_df['img_avg_t'])
    avg_aht = sum(img_table_df['img_avg_t'])/img_count
    
    return text_to_show.format(show_filter_text, img_count, avg_aht, aht_lower_actual, aht_upper_actual, wait_min, wait_max, rads_count)

#--------------------------------------------------
#Show/Hide Graphs
#--------------------------------------------------
@app.callback(Output('intro-text-above-graph', 'style'),
              [Input('rad_table', 'children')]
               )

def show_chart_block_above(rad_table):
    '''
    '''
    if rad_table is None:
        return {'backgroundColor': 'rgb(212,212,212,0.5)', 'padding': '10', 'marginTop': '1%'}
    else:
        return {'display': 'none'}

#--------------------------------------------------
#Show/Hide Graphs
#--------------------------------------------------
@app.callback(Output('intro-text-below-graph', 'style'),
              [Input('rad_table', 'children')]
               )

def show_chart_block_below(rad_table):
    '''
    '''
    if rad_table is not None:
        return {'backgroundColor': 'rgb(212,212,212,0.5)', 'padding': '10', 'marginTop': '1%'}
    else:
        return {'display': 'none'}
    

#--------------------------------------------------
#Run Simulation: Read Inputs and Generate Dataframe
#--------------------------------------------------
@app.callback(Output('rad_table', 'children'),
              [Input('begin-simulation', 'value')],
              [State('rads-count', 'value'), 
               State('arr-rate', 'value'), 
               State('urg-time', 'value'),
               State('non-time', 'value')]
              )

def gen_system_state(sim_time, rads_count, arr_rate, urg_time, non_time):
    #Define urgency times
    cvg.update_globals(urg_time, non_time)
    #Create the intervals
    arrival_times = cvg.create_arrival_times(sim_time, arr_rate)
    print(arrival_times)
    #Create the images with their arrival time_seen
    med_images = cvg.create_medical_images(arrival_times)
    print(med_images)
    #Create the radiologists
    radiologists = cvg.create_radiologists(rads_count)
    #Create the image arrival events
    events = cvg.create_initial_events(med_images)
    s = cvg.SystemState(events, med_images, radiologists)
    return s 

#--------------------------------------------------
#Call Count Graph: Line Chart
#--------------------------------------------------
@app.callback(Output('live-update-graph', 'figure'),
              [Input('rad_table', 'children')])
def update_graph_live(img_table_json):
    '''
    '''
    #print('n is now:', n*1000)
    img_table_df_orig = pd.read_json(img_table_json, orient='split')
    img_table_df_orig['img_count'] = 1
    img_table_orig_pivot = pd.pivot_table(img_table_df_orig, values='img_count', index='intvl_start_time', aggfunc=np.sum)
    
    img_table_df = img_table_df_orig #[img_table_df_orig['intvl_time_elapsed']<n*500]
    img_table_pivot = pd.pivot_table(img_table_df, values='img_count', index='intvl_start_time', aggfunc=np.sum)
    #print(img_table_df)
    traces=[]
    
    traces.append(go.Scatter(
            x=img_table_pivot.index,
            y=img_table_pivot['call_count'],
            #customdata=s.time(img_table_pivot.index),
            mode='lines+markers', 
            opacity = 0.8,
            line = dict(color = ('rgb(22, 96, 167)'),
                        width = 4),     
            name='Image Count',
            marker = dict(size = 10)
            ))
    
    return {
        'data': traces,
        'layout': go.Layout(
            height=450,
            margin=margin,
            title="Image Count by Intervals",
            xaxis={'title': '', 'range':[min(img_table_df_orig['intvl_start_time']), max(img_table_df_orig['intvl_start_time'])], 'zeroline': False},
            yaxis={'title': '', 'range':[0, max(img_table_orig_pivot['call_count'])*1.1], 'zeroline': False},
            hovermode='closest',
            font=dict(family='Raleway')
        )
    }


#--------------------------------------------------
#Call Wait Time Graph: Scatter Plot
#--------------------------------------------------
@app.callback(Output('image-wait-time-graph', 'figure'),
              [Input('rad_table', 'children'),
               Input('live-update-graph', 'hoverData')])
def update_wait_time_graph(rad_table_json, time_filter):
    '''
    '''
    rad_table_df = pd.read_json(rad_table_json, orient='split')
    #print('agent_table: ', agent_table_df_orig)
    
    current_hover = None
    if time_filter is not None:
        if time_filter['points'][0]['customdata'] != 'showall':
            current_hover = dt.datetime.strptime(time_filter['points'][0]['customdata'], "%Y-%m-%d %H:%M:%S")
    
    if current_hover is not None:
            agent_table_df = agent_table_df[agent_table_df['intvl_time_elapsed'] == cvg.timeElapsed(current_hover)].reset_index()

    traces=[]
    colorlist = []
    
    for x in agent_table_df['img_wait_time_elapsed'].tolist():
        if x > 60:
            colorlist.append('rgb(244,109,67)') #Red
        else:
            colorlist.append('rgb(128,205,193)') #Green
            
    traces.append(go.Scatter(
            x=rad_table_df['img_handle_start_time'],
            y=rad_table_df['img_wait_time_elapsed'],
            mode='markers', 
            marker={'color': colorlist, 'opacity': 0.8, 'line': {'width': 0.5, 'color': 'white'}},
            name=''))
    
    return {
        'data': traces,
        'layout': go.Layout(
            height=225,
            margin=margin,
            title="Avg. Image Wait Time: {:.2f} sec".format(round(sum(rad_table_df['img_wait_time_elapsed'])/float(len(rad_table_df))),2),
            xaxis={'zeroline': False},
            yaxis={'title': '', 'range':[0, max(rad_table_df['img_wait_time_elapsed'])*1.1], 'zeroline': False},
            hovermode='closest',
            font=dict(family='Raleway')
        )
    }
    
#--------------------------------------------------
#Agent Status Graph: Horizontal Stacked Bar Chart
#--------------------------------------------------
@app.callback(Output('rad-view-graph', 'figure'),
              [Input('rad_table', 'children'),
               Input('live-update-graph', 'hoverData')])
def update_agent_view(rad_table_json, time_filter):
    '''
    '''
    rad_table_df_orig = pd.read_json(rad_table_json, orient='split')
    #print('agent_table: ', agent_table_df_orig)
    current_hover = None
    if time_filter is not None:
        if time_filter['points'][0]['customdata'] != 'showall':
            current_hover = dt.datetime.strptime(time_filter['points'][0]['customdata'], "%Y-%m-%d %H:%M:%S")
 
    rad_table_df = rad_table_df_orig 
    
    traces=[]
    hovertext=[]
    occupancy=[]
    total_busy_time=[]
    total_rad_time=[]
    
    for rad in rad_table_df['rad_index'].drop_duplicates().sort_values().tolist():
        curr_rad = cvg.agentStatusMatrix(rad_table_df[rad_table_df['rad_index']==rad][['img_handle_start_time', 'img_handle_time_elapsed', 'img_end_time', 'img_end_time_elapsed', 'img_aht']])
        if current_hover is not None:
            curr_rad = curr_rad[(curr_rad['img_handle_time_elapsed'] > cvg.timeElapsed(current_hover)) & (curr_rad['img_handle_time_elapsed'] < cvg.timeElapsed(cvg.timeAddition(current_hover, [0,30,0])))].reset_index()
        curr_rad['rad_index'] = 'Radiologist-' + str(rad)
        #print('-----------------')
        #print(curr_agent)
        #Create a colorlist for busy/available status
        colorlist = []
        #Create a list for agent status
        rad_status = []
        iterator=0
        
        for x in curr_rad['status'].tolist():
            
            if x == 1:
                colorlist.append('rgb(244,109,67)') #Red
                rad_status.append('Radiologist is Busy at: ' + str(curr_rad['img_handle_start_time'][iterator]))
            else:
                colorlist.append('rgb(166,217,106)') #Green
                rad_status.append('Radiologist is Idle at: ' + str(curr_rad['img_handle_start_time'][iterator]))
            iterator +=1
        
            total_busy_time.append(sum(curr_rad[curr_rad['status']==1]['time_gaps']))
            total_rad_time.append(sum(curr_rad['time_gaps']))
            occupancy.append(total_busy_time[rad]/total_rad_time[rad])
        
        traces.append(go.Bar(
                x=curr_rad['time_gaps'],
                y=curr_rad['agent_index'],
                text=rad_status,
                hoverinfo='text',
                orientation = 'h',
                marker = dict(color=colorlist, opacity=0.5),
                name=''))
    
    return {
        'data': traces,
        'layout': go.Layout(
            height=450,
            margin=margin,
            title="Overall Occupancy: {0:.1%}".format(float(sum(total_busy_time))/float(sum(total_rad_time))),
            xaxis={'title': '', 'zeroline': False, 'showgrid': False, 'showticklabels': False},
            yaxis={'zeroline': False, 'showgrid': False},
            hovermode='closest',
            barmode='stack',
            showlegend=False,
            font=dict(family='Raleway')
        )
    }
    
#--------------------------------------------------
#Brand Promise Graph: Vertical Bar Chart
#--------------------------------------------------
@app.callback(Output('bp-graph', 'figure'),
              [Input('rad_table', 'children'),
               Input('live-update-graph', 'hoverData')])
def update_bp(rad_table_json, time_filter):
    '''
    '''
    rad_table_df = pd.read_json(rad_table_json, orient='split')
    
    current_hover = None
    if time_filter is not None:
        if time_filter['points'][0]['customdata'] != 'showall':
            current_hover = dt.datetime.strptime(time_filter['points'][0]['customdata'], "%Y-%m-%d %H:%M:%S")
    
    if current_hover is not None:
            rad_table_df = rad_table_df[rad_table_df['intvl_time_elapsed'] == cvg.timeElapsed(current_hover)].reset_index()

    rad_table_df['img_count'] = 1
    bp_table = pd.pivot_table(rad_table_df, values=['img_count', 'bp_ind'], index='intvl_start_time', aggfunc=np.sum)
    bp_table['bp'] = bp_table['bp_ind']/bp_table['img_count']
    
    traces=[]
    colorlist = []
    
    for bp in bp_table['bp'].tolist():
        if bp < 0.90:
            colorlist.append('rgb(244,109,67)') #Red
        else:
            colorlist.append('rgb(128,205,193)') #Green

    traces.append(go.Bar(
                x=bp_table.index,
                y=bp_table['bp'],
                marker = dict(color=colorlist),
                name='Interval-level Brand Promise'))
    
    return {
        'data': traces,
        'layout': go.Layout(
            height=225,
            margin=margin,
            title="Brand Promise: {0:.1%}".format(sum(bp_table['bp'])/float(len(bp_table))),
            xaxis={'title': '', 'zeroline': False},
            yaxis={'title': '', 'range':[0, 1], 'zeroline': False, 'tickformat': ',.0%', 'hoverformat': ",.1%"},
            hovermode='closest',
            font=dict(family='Raleway')
        )
    }


external_css = ["https://cdnjs.cloudflare.com/ajax/libs/skeleton/2.0.4/skeleton.min.css",
                "//fonts.googleapis.com/css?family=Raleway:400,300,600",
                "//fonts.googleapis.com/css?family=Dosis:Medium",
                "https://cdn.rawgit.com/plotly/dash-app-stylesheets/0e463810ed36927caf20372b6411690692f94819/dash-drug-discovery-demo-stylesheet.css"]

for css in external_css:
    app.css.append_css({"external_url": css})

#app.css.append_css({"external_url": "https://codepen.io/chriddyp/pen/bWLwgP.css"})

if __name__ == '__main__':
    app.run_server(debug=True)
