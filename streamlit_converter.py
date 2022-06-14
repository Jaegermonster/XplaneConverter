# -*- coding: utf-8 -*-
"""
Created on Sat Mar 20 13:27:20 2021
Venv: xplane_converter
2do:
    - 
@author: preis
"""

from ReadData import ReadData
import streamlit as st
import os
import pandas as pd 
from plotly.subplots import make_subplots
import plotly.graph_objects as go
# import matplotlib.pyplot as plt

def get_file_list(suffix):
    files = [None]
    for x in os.listdir('.'+suffix):
        files.append(x)
    return files
   
    
@st.experimental_memo
def load_data(filename, MEAN_SPAN, DELTA_T):
    print('Reading data...\n') 
    data1 = ReadData.get_data(filename)
    print('Interpolating data...\n')
    data1.interpolate_my_data(frq=1/DELTA_T)   
    print('Filtering data...\n')
    data1.kalman_filter(n_iter=50)
    print('Calculating fake values...\n')
    data1.calc_fake_values()
    print('ewm filtering...\n')
    data1.filter_data(MEAN_SPAN)
    print('Getting df...\n')
    df = data1.get_df()
    print('FINISHED...\n')
    m2ft = 3.28084
    df['altitude'] = df.alt * m2ft
    return df, data1
   
def plot_subplots(df, ROW_HEIGHT, ROW_WIDTH, plot_list, units):  
    time = df.recordingTime.values
    rows = len(plot_list)
    fig = make_subplots(rows=rows, cols=1, shared_xaxes=True)
    fig['layout'].update(height=rows*ROW_HEIGHT)            
    for idx, signal in enumerate(plot_list):
        chart = go.Scatter(x=time, y=df[signal], mode='lines', name=signal)
        fig.append_trace(chart, idx+1, 1)
        unit = units[idx]
        fig.update_yaxes(title_text=signal + '<br>' + unit, row = idx+1, col = 1)
    fig.update_layout( autosize=False, width=ROW_WIDTH )
    c1.plotly_chart(fig)
    
def write_xplane_fdr(df, filename):
    new_line = ''
    m2ft = 3.28084
    filename = filename.split('.')[0] + '.fdr'
    for i in range(0,len(df.lat)):
        new_line = new_line + 'DATA, ' + str(df.recordingTime[i]) + ', 15, ' + str(df.lon[i]) + ', ' + str(df.lat[i]) + ', ' + str(df.alt[i] * m2ft) + ', 0,0,0,0, ' + str(df.pitch_angle[i]) + ', ' + str(df.bank_angle[i]) + ', ' + str(df.TH[i]) + ',' + str(df.GS[i])  + ',' + str(df.VVI[i]) + ',0,0,0.5, 0,0, 0,0,0,0,1,1,1,1,0, 11010,10930,4,4,90,270,0,0,10,10,1,1,10,10,0,0,0,0,10,10,0,0,0,0,0,0,0,0,0,0,500, 29.92,0,0,0,0,0,0 , 1,1,0,0 , 2000,2000,0,0 , 2000,2000,0,0 , 30,30,0,0 , 100,100,0,0 , 100,100,0,0 , 0,0,0,0 , 0,0,0,0 , 1500,1500,0,0 , 400,400,0,0 , 1000,1000,0,0 , 1000,1000,0,0 , 0,0,0,0,\n'
    #input file
    fin = open('template.fdr', "rt")
    #output file to write the result to
    fout = open(filename, "wt")  # Name newTexFile with a consecutive name (Rechnungsnummer). 
    # Manipulate texfile: Import calculated values into mainTEX lines. 
    #for each line in the input file
    for line in fin:
     	#read replace the string and write to output file
     	fout.write(line.replace('xxx', str(new_line)))
    # #close input and output files
    fin.close()
    fout.close()
    

if __name__ == '__main__':
    DELTA_T = 1.0  # UPT/ASD = 0.005 | KML = 0.1 | FDR = 1.0
    MEAN_SPAN = 10/DELTA_T  # time [s] used for mean values
    st.set_page_config(layout="wide")  # Use the full page instead of a narrow central column
    c1, c2 = st.columns((2, 1))  # Space out the colums over 2 columns of the same size
    
    st.sidebar.image("unicorn2.png", use_column_width=True)
    st.sidebar.write('_____________')
    
    loading_exp = st.sidebar.expander("Load kml...")
    with loading_exp:
        filename = loading_exp.file_uploader("Choose KML files", type='kml', accept_multiple_files=False)
        # st.write(filename)
    # filename = 'temp.kml'
    try:
        filename = filename.name
        df, data1 = load_data(filename, MEAN_SPAN, DELTA_T)
    
        df_short = df.loc[::100]
        plot_list = ['altitude', 'VVI', 'GS', 'TH', 'pitch_angle', 'bank_angle', 'cum_distance_3D',  'energy']
        units = ['[ ft ]', '[ ft/min ]', '[ kts ]', '[ deg ]', '[ deg ]', '[ deg ]', '[ m ]', '[ - ]']
        
        with c1.expander("Change plot size"):
            ROW_HEIGHT = st.slider('Height:',100, 1000, 300)
            ROW_WIDTH = st.slider('Width:',800, 3200, 900)
        
        plot_subplots(df, ROW_HEIGHT, ROW_WIDTH, plot_list, units)    
        
        SEC = 5
        with c2.expander("Show Map... [every " + str(SEC) + ' sec]'):
            df_map = pd.DataFrame()
            df_map['lat'] = df['lat'].iloc[::SEC]
            df_map['lon'] = df['lon'].iloc[::SEC]
            st.map(df_map)
    
        st.sidebar.write('_____________')
        if st.sidebar.button("Create XplaneFDR..."):
            # write_xplane_fdr(df, filename)
            data1.write_xplane_fdr(filename)
            

    except:
        st.title('MOIN !')
    #     pass