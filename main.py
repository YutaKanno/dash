import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.express as px
from PIL import Image
import io
import base64
from dash import dash_table  
import functions
import import_data
import os
from dotenv import load_dotenv  # ← 追加

# データの読み込み
load_dotenv()
SERVICE_ACCOUNT_JSON = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')
FILE_ID = os.getenv('GOOGLE_DRIVE_FILE_ID')

try:
    df = import_data.read_uploaded_csv_from_drive(FILE_ID)
    #df = pd.read_csv('csv_files/rapsodo_kunimoto.csv')
    df['日付'] = pd.to_datetime(df['日付'])
    df['Release Extension (m)'] = 0.3048*df['Release Extension (ft)']
except FileNotFoundError:
    print("エラー: 'csv_files/rapsodo_kunimoto.csv' が見つかりません。")
    exit()

# Dashアプリケーションの初期化
app = dash.Dash(__name__)
server = app.server

# 背景を透過して画像を正方形に切り抜きBase64で返す関数
def process_image_to_square_base64_with_transparency(image_bytes):
    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")

        # 背景色を左上ピクセルと仮定して透過処理
        bg_color = (244, 247, 246)
        datas = img.getdata()
        newData = []
        for item in datas:
            if all(abs(item[i] - bg_color[i]) < 10 for i in range(3)):
                newData.append((255, 255, 255, 0))  # 背景透過
            else:
                newData.append(item)
        img.putdata(newData)

        # 正方形に中央トリミング
        width, height = img.size
        new_size = min(width, height)
        left = (width - new_size) / 2
        top = (height - new_size) / 2
        right = (width + new_size) / 2
        bottom = (height + new_size) / 2
        img_cropped = img.crop((left, top, right, bottom))

        buffered = io.BytesIO()
        img_cropped.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return f"data:image/png;base64,{img_str}"
    except Exception as e:
        print(f"画像処理エラー（透過）: {e}")
        return None


# Dashアプリのレイアウト
app.layout = html.Div(className='dash-container', children=[
    html.Div(
        className='header-container',
        style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center', 'marginTop': '20px', 'marginBottom': '40px'},
        children=[
            html.Img(
                src='tsukuba_logo.png',  # ← assets フォルダに置いた場合のパス
                style={'height': '60px', 'marginRight': '20px'}
            ),
            html.H1(
                "Rapsodo DashBoard",
                style={'color': '#2C3E50', 'margin': 0}
            ),
            
        ]
    ),


    html.Div(className='name-selection-and-image-row', children=[
        html.Div(className='dash-dropdown-container two-third-width', children=[
            html.Label("名前を選択:"),
            dcc.Dropdown(
                id='name-dropdown',
                options=[{'label': i, 'value': i} for i in df['名前'].unique()],
                value=df['名前'].unique()[0],
                clearable=False
            ),
            html.Label("日付範囲を選択:", style={'marginTop': '25px'}),
            dcc.DatePickerRange(
                id='date-picker-range',
                start_date=df['日付'].min(),
                end_date=df['日付'].max(),
                display_format='YYYY-MM-DD'
            ),
        ]),

        html.Div(className='image-display-container one-third-width', children=[
            html.Img(id='player-image', style={
                'width': '200px', 'height': '200px',
                'objectFit': 'cover', 'borderRadius': '0%',
                'border': '0px solid #ddd', 'display': 'block',
                'margin': '0 auto'
            })
        ]),
    ]),

    
    html.H2("球種別 平均値"),
        html.Div(className='dash-table-container', children=[
            dash_table.DataTable(
                id='summary-table',
                style_table={'overflowX': 'auto'},
                style_cell={'textAlign': 'center'},
                style_header={'backgroundColor': '#f2f2f2', 'fontWeight': 'bold'}
            ),
            dash_table.DataTable(
                id='summary-table2',
                style_table={'overflowX': 'auto', 'marginTop': '25px'},
                style_cell={'textAlign': 'center'},
                style_header={'backgroundColor': '#f2f2f2', 'fontWeight': 'bold'}
            ),
        ]),
        
    html.Div("", className="page-break"),


    html.H2("変化量 散布図"),
    html.Div(className='scatter-wrapper', children=[
        html.Div(dcc.Graph(id='scatter-plot'), className='scatter-plot-box'),
        html.Div(dcc.Graph(id='scatter-plot2'), className='scatter-plot-box'),
    ]),
    html.Div("", className="page-break"),
    
    
    html.H2("投球位置 散布図"),
    html.Div(className='dash-dropdown-container2', children=[
        html.Label("球種を選択:"),
        dcc.Dropdown(
            id='zone-pt-dropdown',
            clearable=False,
            value='ストレート'
        )
    ]),
    html.Div(className='scatter-wrapper', children=[
        html.Div(dcc.Graph(id='zone-plot'), className='scatter-plot-box'),
        html.Div(dcc.Graph(id='zone-plot2'), className='scatter-plot-box'),
    ]),
    html.Div("", className="page-break"),

    
    
    html.H2('リリース位置'),
    html.Div(className='release-wrapper', children=[
        html.Div(dcc.Graph(id='release-plot'), className='release-plot-box'),
        html.Div(dcc.Graph(id='release-angle-plot'), className='release-plot-box'),
    ]),
    html.Div("", className="page-break"),

    # Extensionプロット（1つだけ）
    html.Div(className='release-wrapper', children=[
        html.Div(dcc.Graph(id='extension-plot'), className='release-plot-box'),
    ]),
    html.Div("", className="page-break"),

    
    html.H2("球種別 バイオリンプロット & 推移グラフ"),
    html.Div(className='dash-dropdown-container2', children=[
        html.Label("Y軸を選択:"),
        dcc.Dropdown(
            id='y-axis-value-dropdown',
            options=['Velocity', 'Total Spin', 'True Spin (release)', 'Spin Efficiency (release)', 
                     'VB (trajectory)', 'HB (trajectory)', 'VB (spin)', 'HB (spin)', 'Release Angle', 
                     'Release Height', 'Release Side', 'Horizontal Approach Angle', 'Vertical Approach Angle',
                     'Release Extension (m)'],
            value='Velocity',
            clearable=False
        )
    ]),
    dcc.Graph(id='violin-plot'),
    html.Div("", className="page-break"),
    dcc.Graph(id='line-plot'),
    html.Div("", className="page-break"),
    
     
    html.H2('動画'),
    html.Div([
        html.Label("動画の日付を選択:"),
        dcc.Dropdown(id='date-dropdown', placeholder='日付を選択'),
        html.Div(id='youtube-player', style={'marginTop': '20px'}),
    ]),
    
    html.Footer(
        style={
            'textAlign': 'center',
            'padding': '20px',
            'marginTop': '50px',
            'borderTop': '1px solid #ddd',
            'color': '#888',
            'fontSize': '14px',
            'backgroundColor': '#f9f9f9',
        },
        children="© 2025 Yuta Kanno. University of Tsukuba."
    )
])

# コールバック: グラフと画像を更新
@app.callback(
    [Output('scatter-plot', 'figure'),
     Output('scatter-plot2', 'figure'),
     Output('release-plot', 'figure'),
     Output('release-angle-plot', 'figure'),
     Output('extension-plot', 'figure'),
     Output('violin-plot', 'figure'),
     Output('line-plot', 'figure'),
     Output('player-image', 'src'),
     Output('summary-table', 'data'),
     Output('summary-table', 'columns'),
     Output('summary-table2', 'data'),
     Output('summary-table2', 'columns'),
     Output('date-dropdown', 'options'),
     Output('date-dropdown', 'value'),
     Output('zone-pt-dropdown', 'options')],
    [Input('name-dropdown', 'value'),
     Input('date-picker-range', 'start_date'),
     Input('date-picker-range', 'end_date'),
     Input('y-axis-value-dropdown', 'value'),]
)




def update_graphs(selected_name, start_date, end_date, y_axis):
    filtered_df = df[
        (df['名前'] == selected_name) &
        (df['日付'] >= start_date) &
        (df['日付'] <= end_date)
    ]
    
    color_map = functions.set_palette()
    
    scatter_fig = functions.mov_plot(filtered_df, 'spin', color_map)
    
    scatter_fig2 = functions.mov_plot(filtered_df, 'trajectory', color_map)
    
    release_plot = functions.release_plot(filtered_df, 'Release Side', 'Release Height', color_map, -2, 2)
    
    release_angle_plot = functions.release_angle(filtered_df, color_map)
    
    extension_plot = functions.release_plot(filtered_df, 'Release Extension (m)', 'Release Height', color_map, 0, 3)
    
    violin_fig = functions.violin_plot(filtered_df, y_axis, color_map)
    
    line_plot = functions.line_plot(filtered_df, y_axis, color_map)

    mean_table = functions.mean_table(filtered_df)
    
    mean_table_columns = [{"name": i, "id": i} for i in mean_table.columns]
    
    mean_table2 = functions.mean_table2(filtered_df)
    
    mean_table2_columns = [{"name": i, "id": i} for i in mean_table2.columns]
    

    # 画像の取得・処理
    local_image_path = f'{selected_name}.png'
    if os.path.exists(local_image_path):
        with open(local_image_path, "rb") as f:
            image_bytes = f.read()
        image_src = process_image_to_square_base64_with_transparency(image_bytes)
    else:
        image_src = 'rapsodo_logo.png'  # または '/assets/no_image.png' 等
            
    
    options = [{'label': d, 'value': d} for d in sorted(filtered_df['日付'].unique())]
    value = options[0]['value'] if options else None
    
    zone_pt_options = filtered_df['球種'].unique()

    return (
        scatter_fig, scatter_fig2, release_plot, release_angle_plot, extension_plot,
        violin_fig, line_plot, 
        image_src, mean_table.to_dict('records'), mean_table_columns, mean_table2.to_dict('records'), mean_table2_columns,
        options, value,
        zone_pt_options
        )




@app.callback(
    [Output('youtube-player', 'children'),
     Output('zone-plot', 'figure'),
     Output('zone-plot2', 'figure')],
    [Input('name-dropdown', 'value'),
     Input('date-picker-range', 'start_date'),  
     Input('date-picker-range', 'end_date'),   
     Input('date-dropdown', 'value'),
     Input('zone-pt-dropdown', 'value')]
)
def update_video_embed(selected_name, start_date, end_date, selected_date, pt):
    filtered_df = df[
        (df['名前'] == selected_name) &
        (df['日付'] >= start_date) &
        (df['日付'] <= end_date)
    ]
    row = filtered_df[filtered_df['日付'] == selected_date].head(1)
    if row.empty:
        return html.Div("動画はありません")

    video_link = row.iloc[0].get('VideoLink', None)
    embed_url = functions.get_youtube_embed_url(video_link)
    
    if embed_url:
        return_url = html.Iframe(src=embed_url, width="560", height="315", style={'border': 'none'})
    else:
        return_url =  html.Div("動画が登録されていません")
    
    
    for_zone_df = filtered_df[filtered_df['球種'] == pt]
    zone_plot = functions.zone_plot(for_zone_df, 'density')
    zone_plot2 = functions.zone_plot(for_zone_df, 'point')
    
    
    
    return return_url, zone_plot, zone_plot2

    
    

# アプリケーション実行
if __name__ == '__main__':
    app.run(debug=False)
