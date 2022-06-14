# -*- coding: utf-8 -*-
"""
Created on Sat Mar 20 13:27:20 2021
Venv: xplane_converter
2do:
    - Find outliers! (Refer to 'Schafbergrunde.kml'. )
@author: preis
"""

from ReadData import ReadData
# import matplotlib.pyplot as plt

filename = 'temp.kml'
DELTA_T = 1.0  # UPT/ASD = 0.005 | KML = 0.1 | FDR = 1.0
MEAN_SPAN = 10/DELTA_T  # time [s] used for mean values


print('Reading data...\n') 
data1 = ReadData.get_data(filename)
print('Interpolating data...\n')
data1.interpolate_my_data(frq=1/DELTA_T)   
# data1.write_kml('test0')
print('Filtering data...\n')
data1.kalman_filter(n_iter=50)
print('Calculating fake values...\n')
data1.calc_fake_values()
print('ewm filtering...\n')
data1.filter_data(MEAN_SPAN)
# print('Plot on map...\n')
# data1.plot_on_map()
print('Writin Xplane track...\n')
data1.write_xplane_fdr(filename)   
# print('Writing AMST track...\n')
# data1.write_track()

print('Writing CSV-file... \n')
data1.write_csv(filename)
print('Getting df...\n')
df = data1.get_df()
print('write kml...\n')
data1.write_kml(filename)



# m2ft = 3.28084

# data1.df['alt'] = data1.df.alt / m2ft
# data1.df['Hm']  = data1.df.alt.diff()

# KrakzelMeter = 0
# for value in data1.df.Hm.values:
#     if value > 0:
#         KrakzelMeter += value
        
# print(KrakzelMeter) 
