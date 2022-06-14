# -*- coding: utf-8 -*-
"""
Created on Sat Mar 20 07:21:12 2021

Imported values: 
    - date_time     [xxx]
    - lat           [deg]
    - lon           [deg]
    - alt           [m]
    - delta_time    [s]     - time between recorded points
    - recordingTime [s]
    
Calculated values:
    - distance      [m]     - distance between recorded points
    - GS            [kts]
    - TH            [deg]
    - bank_angle    [deg]
    - pitch_angle   [deg]
    - VVI           [ft/min]
    - cum_distance_3D [m]   - cumulated 3D distance
    
2do:
    - add TH filter from AutomaticFlightAnalysis
    - better filter GS

@author: preis
"""

import ddf
import struct
import pandas as pd
import math
from pykalman import KalmanFilter
import numpy as np

class ReadData:
    
    @staticmethod
    def calc_delta_time(seconds):
        delta_time = [0]
        for i in range(1,len(seconds)):
            delta_time.append((seconds[i]-seconds[i-1]))
        return delta_time
    
    def  __init__(self, filename,lat,lon,alt,date_time,recordingTime):
        [name, ext] = filename.split('.')
        self.filename = filename
        self.name = name
        self.ext = ext
        delta_time = ReadData.calc_delta_time(recordingTime)

        self.df = pd.DataFrame({'date_time':date_time, 'lat':lat, 'lon':lon, 'alt':alt, 'delta_time':delta_time, 'recordingTime':recordingTime})
        # self.df = pd.DataFrame({'date_time':date_time, 'lat':lat, 'lon':lon, 'alt':alt, 'recordingTime':recordingTime})



    @classmethod
    def get_data(cls, filename):
        # import calc_delta_time
        [name, ext] = filename.split('.')
        lon = []
        lat = []
        alt_m = []
        alt = []
        date_time = []
        seconds = []
        recordingTime = []
        if ext == 'kml': 
            with open(filename, "rt") as f:
                lines = f.read().split("\n")
            for line in lines:
                if '<gx:coord>' in line: # or word in line.split() to search for full words
                    pos = line.split('>')
                    pos = pos[1].split('<')
                    pos = pos[0]
                    pos = pos.split(' ')
                    lon.append(float(pos[0]))
                    lat.append(float(pos[1]))
                    alt.append(float(pos[2])) 
                elif '<when>' in line: 
                    time_line = line.split('>')
                    time_line = time_line[1].split('Z<')
                    my_time = time_line[0]
                    date_time.append(my_time)
                    time_line = time_line[0].split('T')
                    time_line = time_line[1].split(':')
                    time_line = float(time_line[0])*3600 + float(time_line[1])*60 + float(time_line[2])
                    seconds.append(time_line)
                    recordingTime.append(time_line - seconds[0])
            return cls(filename,lat,lon,alt,date_time,recordingTime)
        elif ext == 'gpx': 
            with open("test.gpx", "rt") as f:
                lines = f.read().split("\n")
                for line in lines:
                    if 'lat=' in line: # or word in line.split() to search for full words
                        pos = line.split('"')
                        lat.append(float(pos[1]))
                        lon.append(float(pos[3]))
                    elif '<ele>' in line: # or word in line.split() to search for full words
                        alt_calc = line.split('>')
                        alt_calc = alt_calc[1].split('<')
                        alt_m.append(alt_calc[0])
                        alt.append(float(alt_calc[0]))
                    elif 'Z</time>' in line: 
                        time_line = line.split('>')
                        time_line = time_line[1].split('Z<')
                        my_time = time_line[0]
                        date_time.append(my_time)
                        time_line = time_line[0].split('T')
                        time_line = time_line[1].split(':')
                        time_line = float(time_line[0])*3600 + float(time_line[1])*60 + float(time_line[2])
                        seconds.append(time_line)
                        recordingTime.append(time_line - seconds[0])
            return cls(filename,lat,lon,alt,date_time,recordingTime)
          

            
            
    def interpolate_my_data(self, frq=1):
        if 'date_time' in self.df:
            self.df["date_time"] = pd.to_datetime(self.df["date_time"])
            self.df.drop_duplicates('date_time', inplace=True)
            self.df.set_index("date_time", inplace=True)
        if frq > 100:
            upsampled = self.df.resample('5ms')
            n_every = round(200/frq)
        else:
            upsampled = self.df.resample('10ms')
            n_every = round(100/frq)
        interpolated = upsampled.interpolate(method='linear')    
        interpolated = interpolated[::n_every]
        self.df = interpolated
        self.df['delta_time'] = ReadData.calc_delta_time(self.df.recordingTime)


    
    def kalman_filter(self, n_iter=42):
        # measurements = np.column_stack([self.df.lon,self.df.lat,self.df.alt])
        measurements = np.column_stack([self.df.lon,self.df.lat,self.df.alt])
        initial_state_mean = np.hstack([measurements[0,:],3*[0.]])
        initial_state_covariance = np.diag([1e-4, 4e-4, 50, 1e-6, 1e-6, 1e-6])**2
        transition_matrix = [[1, 0, 0, 1, 0, 0],
                              [0, 1, 0, 0, 1, 0],
                              [0, 0, 1, 0, 0, 1],
                              [0, 0, 0, 1, 0, 0],
                              [0, 0, 0, 0, 1, 0],
                              [0, 0, 0, 0, 0, 1]]
        
        observation_matrix = [[1, 0, 0, 0, 0, 0],
                              [0, 1, 0, 0, 0, 0],
                              [0, 0, 1, 0, 0, 0]]
        
        observation_covariance = np.diag([1e-4, 1e-4, 10])**2
        
        kf1 = KalmanFilter(transition_matrices=transition_matrix,
                          observation_matrices=observation_matrix,
                          observation_covariance=observation_covariance,
                          initial_state_mean=initial_state_mean,
                          initial_state_covariance=initial_state_covariance,
                          em_vars=['transition_covariance'])
        
        kf1 = kf1.em(measurements, n_iter=n_iter)
        (smoothed_state_means, smoothed_state_covariances) = kf1.smooth(measurements)
        # filtered_position = [smoothed_state_means[:, 0], smoothed_state_means[:, 1], smoothed_state_means[:, 2]]  # lon, lat, alt
        self.df['lon'] = smoothed_state_means[:, 0]
        self.df['lat'] = smoothed_state_means[:, 1]
        self.df['alt'] = smoothed_state_means[:, 2]
    
 
    def calc_speed_distance(self): 
        distance = []
        cum_distance_3D = [0]
        GS = [0]
        for i in range(0,len(self.df.lat)-1):
            lat1 = float(self.df.lat[i])
            lon1 = float(self.df.lon[i])
            alt1 = float(self.df.alt[i])
            lat2 = float(self.df.lat[i+1])
            lon2 = float(self.df.lon[i+1])
            alt2 = float(self.df.alt[i+1])
            R = 6371e3 #; // metres
            phi1 = lat1 * math.pi/180 #; // φ, λ in radians
            phi2 = lat2 * math.pi/180
            delta_phi = (lat2-lat1) * math.pi/180
            delta_lambda = (lon2-lon1) * math.pi/180
            a = math.sin(delta_phi/2) * math.sin(delta_phi/2) + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2) * math.sin(delta_lambda/2)
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
            d = (R * c) #; // in metres 2D
            distance.append(math.sqrt(d**2 + (alt2-alt1)**2)) # 3D distance     
            cum_distance_3D.append(cum_distance_3D[-1] + distance[-1])   
            if self.df.delta_time[i]:
                GS.append((distance[-1] / self.df.delta_time[i])*(3.6/1.892)) # kts
            else:  # if delta_time is zero
                GS.append(GS[i-1])
        distance.append(distance[-1])
        # cum_distance_3D.append(cum_distance_3D[-1] + distance[-1])
        if 'distance' in self.df:
            self.df['distance'] = distance
            self.df['GS'] = GS
            self.df['cum_distance_3D'] = cum_distance_3D
        else:
            self.df.insert(len(self.df._info_axis)-1,'distance',distance)
            self.df.insert(len(self.df._info_axis)-1,'GS',GS)
            self.df.insert(len(self.df._info_axis)-1,'cum_distance_3D',cum_distance_3D)
    
    

    def calc_fake_values(self):
        TH = []
        energy = []
        h0 = self.df.alt.iloc[0:100].mean()  # [m]
        g = 9.81  # [m/s^2]
        if 'GS' not in self.df: 
            ReadData.calc_speed_distance(self)
        
        for i in range(0,len(self.df.lat)-1):
            lat1 = float(self.df.lat[i])
            lon1 = float(self.df.lon[i])
            lat2 = float(self.df.lat[i+1])
            lon2 = float(self.df.lon[i+1])
            phi1 = lat1 * math.pi/180 #; // φ, λ in radians
            phi2 = lat2 * math.pi/180
            delta_lambda = (lon2-lon1) * math.pi/180        
            # calc TH      
            y = math.sin(delta_lambda) * math.cos(phi2)
            x = math.cos(phi1)*math.sin(phi2) - math.sin(phi1)*math.cos(phi2)*math.cos(delta_lambda)
            theta = math.atan2(y, x)
            TH.append((theta*180/math.pi + 360) % 360) #; // in degrees 
            # Normalized energy:
            energy.append((g*self.df.alt[i] + 0.5*(self.df.GS[i]*1.892/3.6)**2) / (g*h0))              
        TH.append(TH[-1])      
        energy.append(energy[-1])
        if 'TH' in self.df:
            self.df['TH'] = TH
        else:
            self.df.insert(len(self.df._info_axis)-1,'TH',TH)

        import numpy as np
        v = np.array(self.df.GS) / (3.6/1.892)  # convert kts 2 m/s
        phi = np.array(TH) * np.pi/180
        omega = np.diff(phi)
        omega = np.append(omega,[0])
        # for count, value in enumerate(values):
    # ...     print(count, value)
        for i, psi_dot in enumerate(omega):
            if abs(psi_dot) > 2:
                omega[i] = 0.0
        bank_angle = np.arctan(v*omega/9.81)
        bank_angle = bank_angle*180/np.pi
        if 'bank_angle' in self.df:
            self.df['bank_angle'] = bank_angle
        else:
            self.df.insert(len(self.df._info_axis)-1,'bank_angle',bank_angle)
    

        m2ft = 3.28084
        VVI = np.diff(self.df.alt/m2ft)  # m/s
        VVI = np.append(VVI,[0])
        vel = np.array(self.df.GS) / (3.6/1.892)  # convert kts 2 m/s
        pitch_angle = []
        for i, v in enumerate(vel): 
            if v:
                pitch_angle.append(np.arctan(VVI[i]/v)*180/np.pi)
            else:
                pitch_angle.append(0.0)
        VVI = VVI * m2ft*60  # ft/min
        if 'VVI' in self.df:
            self.df['VVI'] = VVI
            self.df['pitch_angle'] = pitch_angle
            self.df['energy'] = energy
        else:
            self.df.insert(len(self.df._info_axis)-1,'VVI',VVI)
            self.df.insert(len(self.df._info_axis)-1,'pitch_angle',pitch_angle)
            self.df.insert(len(self.df._info_axis)-1,'energy',energy)
            

    def filter_data(self, MEAN_SPAN):
        self.df['GS'] = self.df['GS'].ewm(span=MEAN_SPAN).mean()
        self.df['pitch_angle'] = self.df['pitch_angle'].ewm(span=MEAN_SPAN).mean()
        self.df['TH'] = self.df['TH'].ewm(span=MEAN_SPAN).mean()
        self.df['VVI'] = self.df['VVI'].ewm(span=MEAN_SPAN).mean()
        self.df['energy'] = self.df['energy'].ewm(span=MEAN_SPAN).mean()
        
        
    def plot_on_map(self): 
        import matplotlib.pyplot as plt
        import mplleaflet
        plt.plot(self.df.lon, self.df.lat, 'b') # Draw blue line
        mplleaflet.show()
        
    def write_xplane_fdr(self, filename):
        new_line = ''
        m2ft = 3.28084
        filename = filename.split('.')[0] + '.fdr'
        for i in range(0,len(self.df.lat)):
            new_line = new_line + 'DATA, ' + str(self.df.recordingTime[i]) + ', 15, ' + str(self.df.lon[i]) + ', ' + str(self.df.lat[i]) + ', ' + str(self.df.alt[i] * m2ft) + ', 0,0,0,0, ' + str(self.df.pitch_angle[i]) + ', ' + str(self.df.bank_angle[i]) + ', ' + str(self.df.TH[i]) + ',' + str(self.df.GS[i])  + ',' + str(self.df.VVI[i]) + ',0,0,0.5, 0,0, 0,0,0,0,1,1,1,1,0, 11010,10930,4,4,90,270,0,0,10,10,1,1,10,10,0,0,0,0,10,10,0,0,0,0,0,0,0,0,0,0,500, 29.92,0,0,0,0,0,0 , 1,1,0,0 , 2000,2000,0,0 , 2000,2000,0,0 , 30,30,0,0 , 100,100,0,0 , 100,100,0,0 , 0,0,0,0 , 0,0,0,0 , 1500,1500,0,0 , 400,400,0,0 , 1000,1000,0,0 , 1000,1000,0,0 , 0,0,0,0,\n'
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

    def write_track(self):
        # use template.ddf for the output
        datadescription = ddf.DDF('template')

        fout = open('track.bin', 'wb')

        for i in range(0,len(self.df.lat)):
            # set all values to 0
            data = {key: 0 for key in datadescription.itemindex}

            data['Header.Timestamp']     = self.df.recordingTime[i]
            data['MSIout.Ownship.lon']   = self.df.lon[i]
            data['MSIout.Ownship.lat']   = self.df.lat[i]
            data['MSIout.Ownship.alt']   = self.df.alt[i]
            data['MSIout.Ownship.theta'] = self.df.pitch_angle[i]
            data['MSIout.Ownship.phi']   = self.df.bank_angle[i]
            data['MSIout.Ownship.psi']   = self.df.TH[i]
            data['HUD.HUD_vertical_speed'] = self.df.VVI[i]  # [ft/min]
            data['HUD.HUD_groundspee'] = self.df.GS[i]  # [kts]

            values = list(data.values())
            fout.write(struct.pack(datadescription.packetformat, *values))

        fout.close()
        print("'track.bin' written to file...")
		
    
    def write_csv(self, filename):
	    self.df.to_csv(filename.split('.')[0] + '.csv')


    def get_df(self):
        return self.df
            
            
    def write_kml(self, filename):
        from Kml import KML 
        filename = filename.split('.')[0] + '_debug.kml'
        output = KML(filename)
        output.write_header()
        for i in range(0,len(self.df)):
            output.write_point(self.df['lat'].iloc[i], 
                  self.df['lon'].iloc[i], 
                  self.df['alt'].iloc[i])
        print('-> Footer now...')
        output.write_footer()
          