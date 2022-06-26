import numpy as np
import pandas as pd
import shapefile as shp
import matplotlib as mpl
import matplotlib.pyplot as plt
import seaborn as sns
import geopandas as gpd
import matplotlib.patches as mpatches
from cycler import cycler
mpl.rcParams['axes.prop_cycle'] = cycler(color='bgrcmyk')
from time import time

class MapInterventionsVisualization:

    def __init__(self):
        pass

    def read_shapefile(self, shapefiles):
        new_df = pd.DataFrame()
        for sf in shapefiles:
            fields = [x[0] for x in sf.fields][1:]
            records = sf.records()
            shps = [s.points for s in sf.shapes()]
            df = pd.DataFrame(columns=fields, data=records)
            df = df.assign(coords=shps)
            new_df = pd.concat([new_df, df], axis=0)
        return new_df

    def calculate_interventions_stats(self,
            big_dataset, countries=["Kenya"], save_to_file=False, unique_interv=False):
        unique_interv = False
        country_map = {}
        for country in countries:
            districts_dict = {}
            districts_dict_interv = {}
            for i in range(len(big_dataset)):
                for district in big_dataset["provinces"].values[i]:
                    if country in district:
                        if district not in districts_dict:
                            districts_dict[district] = 0
                        districts_dict[district] += 1
                        if district not in districts_dict_interv:
                            if unique_interv:
                                districts_dict_interv[district] = {
                                    "technology intervention": set(), "socioeconomic intervention": set(), "ecosystem intervention": set(), "all": set()}
                            else:
                                districts_dict_interv[district] = {
                                    "technology intervention": 0, "socioeconomic intervention": 0, "ecosystem intervention": 0, "all": 0}
                        cnt = 0
                        for column in ["technology intervention", "socioeconomic intervention", "ecosystem intervention"]:
                            if len(big_dataset[column].values[i]) > 0:
                                if unique_interv:
                                    districts_dict_interv[district][column] = districts_dict_interv[district][column].union(set(big_dataset[column].values[i]))
                                else:
                                    districts_dict_interv[district][column] += 1
                                cnt += 1
                        if cnt > 0:
                            if unique_interv:
                                districts_dict_interv[district]["all"] = districts_dict_interv[district]["all"].union(big_dataset["interventions_found"].values[i])
                            else:
                                districts_dict_interv[district]["all"] += 1
            
            
            if unique_interv:
                result = sorted([(name, (len(interv_val["technology intervention"]), len(interv_val["socioeconomic intervention"]), 
                                         len(interv_val["ecosystem intervention"])),\
                                  len(interv_val["all"])) for name,interv_val in districts_dict_interv.items()],key=lambda x: x[2], reverse = True)
            else:
                result = sorted([(name, (interv_val["technology intervention"], interv_val["socioeconomic intervention"], interv_val["ecosystem intervention"]),\
                                  interv_val["all"]) for name,interv_val in districts_dict_interv.items()],key=lambda x: x[2], reverse = True)
            print(result)
            data = []
            for r in result:
                data.append((r[0].split("/")[1],"", r[1][0], r[1][1], r[1][2], r[2]))
            country_map[country] = pd.DataFrame(data, columns=["Province", "District", "Technology interventions",
                    "Socioeconomic interventions", "Ecosystem interventions", "All interventions"])
            if save_to_file:
                excel_writer.ExcelWriter().save_df_in_excel(
                    country_map[country],
                    "provinces_%s%s.xlsx"%(country,"_unique" if unique_interv else ""))
        return country_map

    def plot_map(self, shapefilename, x_lim = None, y_lim = None, figsize = (11,9)):
        '''
        Plot map with lim coordinates
        '''
        sf = shp.Reader(shapefilename)
        plt.figure(figsize = figsize)
        id=0
        for shape in sf.shapeRecords():
            x = [i[0] for i in shape.shape.points[:]]
            y = [i[1] for i in shape.shape.points[:]]
            plt.plot(x, y, 'k')
            
            if (x_lim == None) & (y_lim == None):
                x0 = np.mean(x)
                y0 = np.mean(y)
                plt.text(x0, y0, id, fontsize=10)
            id = id+1
        
        if (x_lim != None) & (y_lim != None):     
            plt.xlim(x_lim)
            plt.ylim(y_lim)

    def find_zone_locations(self, zone_filename):
        zone_names = {}
        zones = gpd.read_file(zone_filename)

        for i in range(0,len(zones)):
            zones.loc[i,'centroid_lon'] = zones.geometry.centroid.x.iloc[i]
            zones.loc[i,'centroid_lat'] = zones.geometry.centroid.y.iloc[i]
            zone_names[zones["NAME_1"].values[i]] = (zones.geometry.centroid.x.iloc[i], zones.geometry.centroid.y.iloc[i])
        return zone_names

    def calc_color(self, data, color=None, num=6):
        if color== 1:
            color_sq =  ['#dadaebFF','#bcbddcF0','#9e9ac8F0',
                        '#807dbaF0','#6a51a3F0','#54278fF0']; 
            colors = 'Purples';
        elif color == 2:
            color_sq = ['#c7e9b4','#7fcdbb','#41b6c4',
                        '#1d91c0','#225ea8','#253494']; 
            colors = 'YlGnBu';
        elif color == 3:
            color_sq = ['#f7f7f7','#d9d9d9','#bdbdbd',
                        '#969696','#636363','#252525']; 
            colors = 'Greys';
        elif color == 9:
            color_sq = ['#ff0000','#ff0000','#ff0000',
                        '#ff0000','#ff0000','#ff0000']
        else:            
            color_sq = ['#ffffd4','#fee391','#fec44f',
                        '#fe9929','#d95f0e','#993404']; 
            colors = 'YlOrBr';
        bins_to_use = [0,10, 25, 50, 100, 200, 500] #[0, 50, 100, 200, 400, 800, 1000]#[0,10, 25, 50, 100, 200, 500]
        new_data = pd.cut(data, bins=bins_to_use,  labels=list(range(num)))#pd.qcut(data, num, retbins=True, labels=list(range(num)))
        color_ton = []
        for val in new_data:
            if val != val:
                color_ton.append(color_sq[0]) 
            else:
                color_ton.append(color_sq[val]) 
        if color != 9:
            colors = sns.color_palette(colors, n_colors=6) 
        return color_ton, bins_to_use, colors

    def plot_map_fill_multiples_ids(self, title, used_sfs, comuna,  
                                         print_id, color_ton, 
                                         bins, 
                                         x_lim = None, 
                                         y_lim = None, 
                                         figsize = (11,9),
                                         colors=None,
                                         zone_names={}):
        '''
        Plot map with lim coordinates
        '''
            
        plt.figure(figsize = figsize, dpi=300)
        fig, ax = plt.subplots(figsize = figsize)
        fig.suptitle(title, fontsize=16)
        
        for sf in used_sfs:
            for shape in sf.shapeRecords():
                x = [i[0] for i in shape.shape.points[:]]
                y = [i[1] for i in shape.shape.points[:]]
                ax.plot(x, y, 'k')
            
        for idx, (id, name, sf) in enumerate(comuna):
            
            shape_ex = sf.shape(id)
            x_lon = np.zeros((len(shape_ex.points),1))
            y_lat = np.zeros((len(shape_ex.points),1))
            for ip in range(len(shape_ex.points)):
                x_lon[ip] = shape_ex.points[ip][0]
                y_lat[ip] = shape_ex.points[ip][1]
            ax.fill(x_lon,y_lat, color_ton[idx])
            if print_id != False:
                if name in ["Mandera", "Marsabit", "Turkana", "Wajir", "West Pokot", "Samburu", "Isiolo", "Garissa", 
                            "Tana River", "Kilifi","Kwale", "Taita Taveta", "Makueni", "Kajiado", "Narok", "Machakos", 
                            "Nakuru", "Meru", "Laikipia", "Baringo", "Kiambu", "Bungoma", "Siaya", "Homa Bay", "Migori", 
                            "Busia", "Kisumu", "Kitui", "Kakamega"]:
                    if name in zone_names:
                        x0 = zone_names[name][0]
                        y0 = zone_names[name][1]
                    else:
                        x0 = np.mean(x_lon)
                        y0 = np.mean(y_lat)
                    plt.text(x0-0.25, y0, name, fontsize=10, fontweight="heavy")
        if (x_lim != None) & (y_lim != None):     
            plt.xlim(x_lim)
            plt.ylim(y_lim)
        handles = []
        if colors is not None:
            for idx, color in enumerate(colors):
                lb = bins[idx]
                rb =  bins[idx+1]
                handles.append(mpatches.Patch(color=color, label='%d-%d'%(lb, rb)))
        ax.legend(handles=handles)
        plt.axis('off')
        fig.savefig("%s_%d.svg"%(title, int(time())), format="svg", dpi=300)
        fig.savefig("%s_%d.eps"%(title, int(time())), format="eps", dpi=300)
        

    def plot_map_data(self, big_dataset, country_shapefiles={"Kenya":[
            "../tmp/gadm36_KEN_shp/gadm36_KEN_1.shp",
            "../tmp/gadm36_KEN_shp/gadm36_KEN_2.shp"]},
            title="", data_column="All interventions",
            color=None, print_id=False, save_to_file=False, unique_interv=False):
        '''
        Plot map with selected comunes, using specific color
        '''
        country_map = self.calculate_interventions_stats(
            big_dataset, countries=country_shapefiles.keys(),
            save_to_file=save_to_file, unique_interv=unique_interv)
        for country in country_shapefiles:
            sfs = [shp.Reader(file) for file in country_shapefiles[country]]
            color_ton, bins, colors = calc_color(country_map[country][data_column], color)
            province_ids = []
            used_shapefiles = set()
            for province in provinces:
                print(province)
                found = False
                for idx, sf in enumerate(sfs):
                    df = read_shapefile([sf])
                    if not found:
                        if "NAME_2" in df.columns and len(df[df.NAME_2 == province]) > 0:
                            province_ids.append((df[df.NAME_2 == province].index.get_values()[0], comuna, sf))
                            found = True
                            used_shapefiles.add(idx)
                        if "NAME_1" in df.columns and len(df[df.NAME_1 == province]) > 0:
                            province_ids.append((df[df.NAME_1 == province].index.get_values()[0], comuna, sf))
                            found = True
                            used_shapefiles.add(idx)
                if not found:
                    print(" Not found ", province)
            used_sfs = []
            for i in used_shapefiles:
                used_sfs.append(sfs[i])
            y_lim = None#(-4, 4) # latitude 
            x_lim = None#(34, 39) # longitude
            self.plot_map_fill_multiples_ids(country + " " + title,
                                             used_sfs, province_ids, 
                                             print_id, 
                                             color_ton, 
                                             bins, 
                                             x_lim = x_lim, 
                                             y_lim = y_lim, 
                                             figsize = (11,9),
                                             colors=colors,
                                             zone_names=self.find_zone_locations(
                                                country_shapefiles[country][0]))
