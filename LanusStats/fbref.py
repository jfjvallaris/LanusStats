import warnings
warnings.filterwarnings("ignore")
import requests
from bs4 import BeautifulSoup, Comment
import pandas as pd
from datetime import datetime
import time
from mplsoccer import PyPizza, add_image, FontManager
import matplotlib.pyplot as plt
from PIL import Image
import numpy as np
from .functions import get_possible_leagues_for_page, possible_stats_exception
from .exceptions import PlayerDoesntHaveInfo, MatchDoesntHaveInfo

class Fbref:

    ##############################################
    def __init__(self):
        self.possible_stats = [
            'stats',
            'keepers',
            'keepersadv',
            'shooting',
            'passing',
            'passing_types',
            'gca',
            'defense',
            'possession',
            'playingtime',
            'misc'
        ]

        self.font_normal = FontManager('https://raw.githubusercontent.com/googlefonts/roboto/main/'
                            'src/hinted/Roboto-Regular.ttf')
        self.font_italic = FontManager('https://raw.githubusercontent.com/googlefonts/roboto/main/'
                                'src/hinted/Roboto-Italic.ttf')
        self.font_bold = FontManager('https://raw.githubusercontent.com/google/fonts/main/apache/robotoslab/'
                                'RobotoSlab[wght].ttf')
        self.title = FontManager('https://github.com/google/fonts/blob/main/ofl/bungeeinline/BungeeInline-Regular.ttf?raw=true')
        
    ##############################################
        
    def match_info_exception(self, path):
        data = self.get_all_dfs(path)
        try:
            data[17]
        except IndexError:
            raise MatchDoesntHaveInfo(path)
    
    def player_info_exception(self, path):
        data = self.get_all_dfs(path)
        first_df = data[0]
        if first_df.columns[0] not in ['Statistic', 'Estadísticas']:
            raise PlayerDoesntHaveInfo('path')
    
    def get_teams_season_stats(self, stat, league, season=None, save_csv=False, stats_vs=False, change_columns_names=False, add_page_name=False):
        """Gets you a table of the stats for the teams in a certain league.

        Args:
            stat (str): Stat available for that league in Fbref
            league (str): Possible leagues in get_available_leagues("Fbref")
            season (str, optional): String showing the season for the data to be extracted. Defaults to None.
            save_excel (bool, optional): If true it save an excel file. Defaults to False.
            stats_vs (bool, optional): If true it gives you the VS stats of that table. Defaults to False.
            change_columns_names (bool, optional): If you would like to change the columns names. Defaults to False.
            add_page_name (bool, optional): It add the stat name to the columns. Defaults to False.

        Returns:
            data: DataFrame with the data of the stats of the teams.
        """
        
        print("Starting to scrape teams data from Fbref...")
        possible_stats_exception(self.possible_stats, stat)     
        leagues = get_possible_leagues_for_page(league, season, 'Fbref')
        
        if league == 'Big 5 European Leagues':
            path = f'https://fbref.com/en/comps/{leagues[league]["id"]}/{stat}/squads/{leagues[league]["slug"]}-Stats'
        elif season != None:
            path = f'https://fbref.com/en/comps/{leagues[league]["id"]}/{season}/{stat}/{season}/{leagues[league]["slug"]}-Stats'
        elif season != None and league == 'Big 5 European Leagues':
            path = f'https://fbref.com/en/comps/{leagues[league]["id"]}/{season}/{stat}/squads/{season}/{leagues[league]["slug"]}-Stats'
        else:
            path = f'https://fbref.com/en/comps/{leagues[league]["id"]}/{stat}/{leagues[league]["slug"]}-Stats'
            
        
        today = datetime.now().strftime('%Y-%m-%d')
        time.sleep(3)
        
        df_total = pd.read_html(path)

        if stats_vs:
              data = df_total[1]
        else:
              data = df_total[0]
        
        if change_columns_names:
            data.columns = data.columns \
                            .map(lambda x: x[1] if 'Unnamed:' in x[0] else '_'.join([part.replace(' ', '') for part in x]))
            if add_page_name:
                new_columns = [f'{stat}_' + col for col in data.columns]
                data.columns = new_columns
        else:
            data.columns = data.columns.droplevel(0)

        if save_csv:
              data.to_csv(f'{league} - {stat} - {today}.csv')
        return data

    def get_vs_and_teams_season_stats(self, stat, league, season=None, save_excel=False, change_columns_names=False, add_page_name=False):
        """Get For and VS Stats for a team in a season. The two tables show in any stat for any team in a league.

        Args:
            stat (str): Stat available for that league in Fbref
            league (str): Possible leagues in get_available_leagues("Fbref")
            season (str, optional): String showing the season for the data to be extracted. Defaults to None.
            save_excel (bool, optional): If true it save an excel file. Defaults to False.
            change_columns_names (bool, optional): If you would like to change the columns names. Defaults to False.
            add_page_name (bool, optional): It add the stat name to the columns. Defaults to False.

        Returns:
            df: DataFrame with the stat/stats for that team
            df_vs: DataFrame with the stat/stats against that team
        """
        df = self.get_teams_season_stats(stat, league, season, False, False, change_columns_names, add_page_name)
        df_vs = self.get_teams_season_stats(stat, league, season, False, True, change_columns_names, add_page_name)

        if save_excel:
            path = f'{league} - {stat} vs stats teams.xlsx'
            writer = pd.ExcelWriter(path, engine='xlsxwriter')
            df.to_excel(writer, sheet_name='Stats')
            df_vs.to_excel(writer, sheet_name='VS Stats')
            writer.close()

        return df, df_vs
    
    def concatenate_teams_df(self, df, df_vs, axis=1):
        df_total = pd.concat([df, df_vs], axis=axis)

        return df_total
        
    def get_all_teams_season_stats(self, league, save_csv=False, stats_vs=False, change_columns_names=False, add_page_name=False):
        
        today = datetime.now().strftime('%Y-%m-%d')
        data = pd.DataFrame()
        for stat in self.possible_stats:
            placeholder = self.get_teams_season_stats(f'{stat}',league, False, stats_vs, change_columns_names, add_page_name)
            data = pd.concat([data, placeholder], axis=1)
        
        if save_csv:
              data.to_csv(f'{league} - {stat} - {today}.csv')

        return data

    def get_table(self, soup):
        return soup.find_all('table')[0]

    def parse_row(self, row):
            cols = None
            cols = row.find_all('td')
            cols = [ele.text.strip() for ele in cols]
            return cols
         
    def get_player_season_stats(self, stat, league, season=None, save_csv=False, add_page_name=False):
        """Get players season stats for a particular stat.

        Args:
            stat (str): stat possible (is a list)
            league (str): Possible leagues in get_available_leagues("Fbref")
            season (str, optional): Possible season in get_available_season_for_leagues("Fbref", league). Defaults to None (that gets you the most recent season)
            save_csv (bool, optional): If true, it saves the tables as a csv. Defaults to False.
            add_page_name (bool, optional): If true it adds the stat name to all the columns. Defaults to False
            
        Returns:
            df_data: DataFrame with the data for that particular stat selected as a param
        """
        
        print("Starting to scrape player data from Fbref...")
        possible_stats_exception(self.possible_stats, stat)
        
        leagues = get_possible_leagues_for_page(league, season, 'Fbref')
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        if league == 'Big 5 European Leagues':
            path = f'https://fbref.com/en/comps/{leagues[league]["id"]}/{stat}/players/{leagues[league]["slug"]}-Stats'
        elif season != None:
            path = f'https://fbref.com/en/comps/{leagues[league]["id"]}/{season}/{stat}/{season}/{leagues[league]["slug"]}-Stats'
        elif season != None and league == 'Big 5 European Leagues':
            path = f'https://fbref.com/en/comps/{leagues[league]["id"]}/{season}/{stat}/players/{season}/{leagues[league]["slug"]}-Stats'
        else:
            path = f'https://fbref.com/en/comps/{leagues[league]["id"]}/{stat}/{leagues[league]["slug"]}-Stats'

        time.sleep(3)
        
        """Most of the code is from @BeGriffis (Twitter): 
        https://github.com/griffisben/griffis_soccer_analysis/blob/main/griffis_soccer_analysis/fbref_code.py
        """
        response = requests.get(path)
        soup = BeautifulSoup(response.content, "html.parser")
        comment = soup.find_all(text=lambda t: isinstance(t, Comment))
        comment_number=0
        for i in range(len(comment)):
            if comment[i].find('\n\n<div class="table_container"') != -1:
                comment_number = i
        comment_table = comment[comment_number]
        table = comment_table.find('table')
        table_html = BeautifulSoup(comment_table[table:], 'html.parser')
        table = self.get_table(table_html)
        data = []
        headings=[]
        headtext = table_html.find_all("th",scope="col")
        for i in range(len(headtext)):
            heading = headtext[i].get_text()
            headings.append(heading)
        headings=headings[1:len(headings)]
        data.append(headings)
        table_body = table.find('tbody')
        rows = table_body.find_all('tr')

        for row_index in range(len(rows)):
            row = rows[row_index]
            cols = self.parse_row(row)
            data.append(cols)
         
        df_data = pd.DataFrame(data)
        df_data = df_data.rename(columns=df_data.iloc[0])
        df_data = df_data.reindex(df_data.index.drop(0))
        df_data = df_data.replace('',0).drop(columns=['Matches'])
        df_data.insert(4, 'Comp', [league]*len(df_data))
        df_data = df_data.dropna().reset_index(drop=True)


        if add_page_name:
                new_columns = [f'{stat}_' + col if col != 'Player' else col for col in df_data.columns]
                df_data.columns = new_columns

        if save_csv:
              df_data.to_csv(f'{league} - {stat} - {today}.csv')
        
        return df_data

    def get_all_player_season_stats(self, league, save_csv=False):
        """Gets a table of ALL the stats in a players page.

        Args:
            league (str): Possible leagues in get_available_leagues("Fbref")
            save_csv (bool, optional): If true, it saves the tables as a csv. Defaults to False.

        Returns:
            data: DataFrame with all the stats of players
            gk_data: DataFrame with all the stats relevant to goalkeepers
        """
        
        today = datetime.now().strftime('%Y-%m-%d')
        data = pd.DataFrame()
        gk_data = pd.DataFrame()
        for stat in self.possible_stats:
            print(stat)
            if stat in ['keepers', 'keepersadv']:
                placeholder = self.get_player_season_stats(f'{stat}',league, False, True)
                if len(gk_data) == 0:
                    gk_data = pd.concat([gk_data, placeholder], axis=1)
                else:
                    gk_data = gk_data.merge(placeholder, on='Player', how='left')
            else:
                placeholder = self.get_player_season_stats(f'{stat}',league, False, True)
                if len(data) == 0:
                    data = pd.concat([data, placeholder], axis=1)
                else:
                    data = data.merge(placeholder, on='Player', how='left')
        
        if save_csv:
              data.to_csv(f'{league} - {stat} - {today}.csv')

        #To avoid duplicates of players that played for two clubs in the same competition
        data = data.drop_duplicates(subset=['Player', 'stats_Squad']).reset_index(drop=True)
        gk_data = gk_data.drop_duplicates(subset=['Player', 'keepers_Squad']).reset_index(drop=True)

        return data, gk_data
    
    def get_slice_text_colors(self, player_df):
        sublists, sublist = [], []
        for item in list(player_df.iloc[:, 0]):
            if item is np.nan:
                if sublist:  # Si la sublist no está vacía
                    sublists.append(sublist.copy())
                    sublist.clear()  # Reiniciar la sublist
            else:
                sublist.append(item)
        if sublist:
            sublists.append(sublist.copy())

        slice_colors = ["#2a6f97"] * len(sublists[0]) + ["#588b8b"] * len(sublists[1]) + ["#8d0801"] * len(sublists[2])
        text_colors = ["#FFFFFF"] * len(sublists[0]) + ["#000000"] * len(sublists[1]) + ["#FFFFFF"] * len(sublists[2])
        return slice_colors, text_colors
    
    def get_player_percentiles(self, path):
        """Gets you a table with the stats and percentiles of a certain player, if they have them.

        Args:
            path (str): URL to a player page in Fbref. Example: https://fbref.com/en/players/90a0bb3b/Victor-Malcorra

        Returns:
            player_df: DataFrame with the stats and values of the percentiles.
        """
        self.player_info_exception(path)
        player_df = pd.read_html(path)[0]
        time.sleep(3)
        return player_df

    def plot_player_percentiles(self, path, image=None, chart_stats=None, save_image=False, name_extra='', credit_extra=''):
        """Does a pizza plot with percentiles (eg: https://mplsoccer.readthedocs.io/en/latest/gallery/pizza_plots/plot_pizza_dark_theme.html#sphx-glr-gallery-pizza-plots-plot-pizza-dark-theme-py)
        for a specific player, if they have their percentiles in their fbref page.

        Args:
            path (str): URL to a player page in Fbref. Example: https://fbref.com/en/players/90a0bb3b/Victor-Malcorra
            image (str, optional): Path to an image so it can be at the center of the plot. Defaults to None. Recommended to use this: https://crop-circle.imageonline.co/
            chart_stats (list, optional): Adds rectangles above the image to indicate sections of the plot. Defaults to None. Use a list.
            save_image (bool, optional): Saves a png of the plot. Defaults to False.
            name_extra (str, optional): Something to add to the title. Defaults to ''.
            credit_extra (str, optional): Something to add to the credits. Defaults to ''.
        """
        
        #Define player dataframe and also colors of the plot
        player_df = self.get_player_percentiles(path=path)
        
        slice_colors, text_colors = self.get_slice_text_colors(player_df)

        #Define strings of parameters and shortens some that are long. You can add more.
        params = list(player_df.iloc[:, 0].dropna())
        params_short = {
            'npxG: Goles esperados (xG) sin contar penaltis': 'npxG',
            'npxG: Non-Penalty xG': 'npxG'
        }
        for index, value in enumerate(params):
            if value in params_short:
                params[index] = params_short[value]
        plot_params = []
        for param in params:
            if len(param.split(' ')) > 2:
                initial_list, final_list = param.split(' ')[:2], param.split(' ')[2:]
                final_string = ' '.join(initial_list) + '\n' + ' '.join(final_list)
                new_param = final_string
            else:
                new_param = param
            plot_params.append(new_param)

        #Define values for the plot
        values = list(player_df.iloc[:, 2].dropna().astype(int))

        #Define PyPizza class and plot it
        baker = PyPizza(
            params=plot_params,                  
            background_color="#222222",     
            straight_line_color="#000000",  
            straight_line_lw=1,             
            last_circle_color="#000000",    
            last_circle_lw=1,               
            other_circle_lw=0,              
            inner_circle_size=20            
        )

        fig, ax = baker.make_pizza(
            values,                          
            figsize=(8, 8.5),                
            color_blank_space="same",        
            slice_colors=slice_colors,        
            value_colors=text_colors,         
            value_bck_colors=slice_colors,    
            blank_alpha=0.4,
            kwargs_slices=dict(
                edgecolor="#000000", zorder=2, linewidth=1
            ),                               
            kwargs_params=dict(
                color="#F2F2F2", fontsize=10,
                fontproperties=self.font_bold.prop, va="center"
            ),                               
            kwargs_values=dict(
                color="#F2F2F2", fontsize=11,
                fontproperties=self.font_normal.prop, zorder=3,
                bbox=dict(
                    edgecolor="#000000", facecolor="cornflowerblue",
                    boxstyle="round,pad=0.2", lw=1
                )
            )                               
        )

        #Define all the text in the plot
        name = path.split('/')[-1].replace('-', ' ')
        
        #Credits. Don't delete them. I will find you.
        if path.split('/')[3] == 'es':
            CREDIT_1 = f"Data: Fbref | Código: LanusStats | Inspirado por: MPLSoccer {credit_extra}"
            CREDIT_2 = "A mayor valor de la barra, signfica que está entre los números más altos de la categoría"
            CREDIT_3 = "Jugador comparado con otros de su misma posición en ligas de nivel similar el último año."
        else:
            CREDIT_1 = f"Data: Fbref | Code: LanusStats | Inspired by: MPLSoccer {credit_extra}"
            CREDIT_2 = "If the value of the bar is larger, it's in the highest values of the category"
            CREDIT_3 = "Player compared to positional peers in leagues of the same caliber over the last 365 days."

        fig.text(0.99, 0.02, f"{CREDIT_1}\n{CREDIT_2}\n{CREDIT_3}", size=10, fontproperties=self.font_italic.prop, color="#F2F2F2",ha="right")

        if chart_stats:
            #Add text near the rectangles
            fig.text(0.34, 0.925, f"{chart_stats[0]}", size=16, fontproperties=self.font_bold.prop, color="#F2F2F2")
            fig.text(0.492, 0.925, f"{chart_stats[1]}", size=16, fontproperties=self.font_bold.prop, color="#F2F2F2")
            fig.text(0.662, 0.925, f"{chart_stats[2]}", size=16, fontproperties=self.font_bold.prop, color="#F2F2F2")

            # add rectangles
            fig.patches.extend([
                plt.Rectangle(
                    (0.31, 0.9225), 0.025, 0.021, fill=True, color="#1a78cf",
                    transform=fig.transFigure, figure=fig
                ),
                plt.Rectangle(
                    (0.462, 0.9225), 0.025, 0.021, fill=True, color="#ff9300",
                    transform=fig.transFigure, figure=fig
                ),
                plt.Rectangle(
                    (0.632, 0.9225), 0.025, 0.021, fill=True, color="#d70232",
                    transform=fig.transFigure, figure=fig
                ),
            ])
            fig.text(
                0.515, 0.975, f"{name}{name_extra}", size=30,
                ha="center", fontproperties=self.title.prop, color="#F2F2F2"
                )
        else:
            fig.text(
                0.515, 0.94, f"{name}{name_extra}", size=30,
                ha="center", fontproperties=self.title.prop, color="#F2F2F2"
                )

        #Define image
        if image:
            #Page to generate round images: https://crop-circle.imageonline.co/
            ax_image = add_image(
                Image.open(image), fig, left=0.4478, bottom=0.4315, width=0.13, height=0.127
            )

        if save_image:
            plt.savefig(f'{name} fbref percentile plot.png', dpi=300, bbox_inches='tight')
    
    def get_all_dfs(self, path):
        data = pd.read_html(path)
        time.sleep(3)
        return data
    
    def get_player_similarities(self, path):
        """Gets you a table of player similarities.

        Args:
            path (str): URL to a player page in Fbref. Example: https://fbref.com/en/players/90a0bb3b/Victor-Malcorra

        Returns:
            data: DataFrame with the names of the players similar.
        """
        self.player_info_exception(path)
        data = pd.read_html(path)[1]
        time.sleep(3)
        return data
    
    def get_match_shots(self, path):
        self.match_info_exception(path)
        data = self.get_all_dfs(path)[17]
        data.columns = data.columns.droplevel(0)
        return data
    
    def get_general_match_team_stats(self, path):
        self.match_info_exception(path)
        data = self.get_all_dfs(path)
        local_df, visit_df = data[3], data[10]
        return local_df, visit_df

    def get_tournament_table(self, path):
        """Gets you the table of the league.

        Args:
            path (str): URL of the page of the league. Example: https://fbref.com/en/comps/21/Primera-Division-Stats

        Returns:
            data: DataFrame with the table.
        """
        data = self.get_all_dfs(path)[0]
        return data