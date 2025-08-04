import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.express as px
from PIL import Image
import io
import base64
import requests
from dash import dash_table 
import datetime
import plotly.graph_objects as go
import numpy as np
from scipy.stats import chi2


# 球種のパレットの作成
def set_palette():
    palette = ["#FF3333", "#FF9933", "#6666FF", "#9933FF", "#66B2FF",
            "#00CC66", "#009900", "#CC00CC", "#FF66B2", "#000000"]
    pitch_types = ["ストレート", "ツーシーム", "スライダー", "カット", "カーブ",
                "チェンジアップ", "フォーク", "シンカー", "シュート", "特殊球"]
    color_map = dict(zip(pitch_types, palette))
    return color_map
    
   



# 変化量の散布図
def mov_plot(data, sp_or_trj, color_map):
    x_col = f'HB ({sp_or_trj})'
    y_col = f'VB ({sp_or_trj})'

    # 元の散布図（透明度0.5）
    scatter_fig = px.scatter(
        data, x=x_col, y=y_col,
        color='球種',
        color_discrete_map=color_map,
        hover_data=[x_col, y_col, '日付'],
        title=f'{sp_or_trj} based',
        labels={x_col: '', y_col: ''},
        opacity=0.7
    )

    # 球種ごとの平均値をプロット（サイズ2倍、透明度1）
    mean_points = data.groupby('球種')[[x_col, y_col]].mean().reset_index()
    for _, row in mean_points.iterrows():
        scatter_fig.add_trace(go.Scatter(
            x=[row[x_col]],
            y=[row[y_col]],
            mode='markers',
            marker=dict(
                size=20,  # 通常のpx.scatterより大きめ
                color=color_map.get(row['球種'], 'gray'),
                opacity=1,
                line=dict(width=1, color='black')
            ),
            name=f"{row['球種']} 平均",
            showlegend=False  # 凡例は1つにしたければFalse
        ))

    # x=0の縦線
    scatter_fig.add_shape(
        type="line",
        x0=0, y0=data[y_col].min()-5,
        x1=0, y1=data[y_col].max()+5,
        line=dict(color="black", width=1)
    )
    # y=0の横線
    scatter_fig.add_shape(
        type="line",
        x0=data[x_col].min()-5, y0=0,
        x1=data[x_col].max()+5, y1=0,
        line=dict(color="black", width=1)
    )
    scatter_fig.update_xaxes(dtick=10)
    scatter_fig.update_yaxes(dtick=10)

    scatter_fig.update_layout(
        height=650,
        legend=dict(
            orientation="h",
            y=-0.2,
            x=0,
            xanchor='left',
            yanchor='top'
        ),
        title_x=0.5,
        margin=dict(l=0,r=0)
    )
    return scatter_fig



# ゾーンプロット
def zone_plot(df, plot_type):
    if plot_type == 'density':
        fig = go.Figure(go.Histogram2dContour(
                x = df['Strike Zone Side'],
                y = df['Strike Zone Height'],
                colorscale = 'Reds',
        ))
    elif plot_type == 'point':
        fig = px.scatter(df, x='Strike Zone Side', y='Strike Zone Height')
        
    fig.add_shape(
            type="line",
            x0=-25.3, y0=45,
            x1=25.3, y1=45,
            line=dict(color="black", width=3)
        )
    fig.add_shape(
            type="line",
            x0=-25.3, y0=107,
            x1=25.3, y1=107,
            line=dict(color="black", width=3)
        )
    fig.add_shape(
            type="line",
            x0=25.3, y0=45,
            x1=25.3, y1=107,
            line=dict(color="black", width=3)
        )
    fig.add_shape(
            type="line",
            x0=-25.3, y0=45,
            x1=-25.3, y1=107,
            line=dict(color="black", width=3)
        )
    fig.update_layout(
        xaxis=dict(visible=False, range=[-80, 80]),
        yaxis=dict(visible=False, range=[0, 170]),
        title_x=0.5,
        margin=dict(l=0,r=0)
    )
    return fig

# バイオリンプロット
def violin_plot(data, label, color_map):
    violin_fig = px.violin(
        data, x='球種', y=label,
        box=True, points="all",
        color='球種',
        color_discrete_map=color_map,
        title=label
    )
    violin_fig.update_layout(
        legend=dict(
            orientation="h",
            y=-0.2,
            x=0,
            xanchor='left',
            yanchor='top'
        ),
        title_x=0.5,
        margin=dict(l=0,r=0)
    )
    return violin_fig




# 推移グラフ
def line_plot(df, y_label, color_map):
    df['date'] = pd.to_datetime(df['日付'])
    summary = df.groupby(['date', '球種'])[y_label].mean().reset_index()

    fig = px.line(summary, x='date', y=y_label, color='球種',
                color_discrete_map=color_map,
                title=y_label)
    fig.update_layout(
        legend=dict(
            orientation="h",
            y=-0.2,
            x=0,
            xanchor='left',
            yanchor='top'
        ),
        title_x=0.5,
        margin=dict(l=0,r=0)
    )
    return fig



# リリース位置の散布図
def release_plot(df, x_axis, y_axis, color_map, x_s, x_e):
    fig = px.scatter(
        data_frame=df,
        x=x_axis,
        y=y_axis,
        color='球種',
        color_discrete_map=color_map,
        title='Release Position'
    )
    fig.update_yaxes(range=(0.5, 2.1))
    fig.update_xaxes(range=(x_s, x_e))
    fig.update_layout(
        legend=dict(
            orientation="h",
            y=-0.2,
            x=0,
            xanchor='left',
            yanchor='top'
        ),
        title_x=0.5,
        margin=dict(l=0,r=0)
    )
    return fig



# リリース角度(鉛直方向)の描写
def release_angle(df, color_map):
    mean_angles = df.groupby('球種')['Release Angle'].mean().reset_index()
    mean_angles['Release Angle_rad'] = np.deg2rad(mean_angles['Release Angle'])

    theta = np.linspace(-np.pi/4, np.pi/4, 360)
    x_circle = np.cos(theta)
    y_circle = np.sin(theta)

    fig = go.Figure()
    # 単位円の描画
    fig.add_trace(go.Scatter(
        x=x_circle,
        y=y_circle,
        mode='lines',
        name='Unit Circle',
        line=dict(color='lightgray', width=2), 
        hoverinfo='none'))

    # 各球種の平均Release Angleをプロット
    for index, row in mean_angles.iterrows():
        pitch_type = row['球種']
        angle_rad = row['Release Angle_rad']
        
        # 線の描画
        fig.add_trace(go.Scatter(
            x=[0, np.cos(angle_rad)],
            y=[0, np.sin(angle_rad)],
            mode='lines',
            name=f'{pitch_type}', # 球種名で凡例を表示
            line=dict(color=color_map.get(pitch_type, '#CCCCCC'), width=3), # 色をcolor_mapから取得、見つからない場合は灰色
            showlegend=True, # 凡例を表示
        ))
        
        # 角度の終点にマーカーを追加
        fig.add_trace(go.Scatter(
            x=[np.cos(angle_rad)],
            y=[np.sin(angle_rad)],
            mode='markers',
            marker=dict(size=8, color=color_map.get(pitch_type, '#CCCCCC')),
            name=f'{pitch_type} Point', # ポイント用の凡例（通常は非表示）
            showlegend=False, # ポイントの凡例は非表示にする
            hoverinfo='text',
            text=f'球種: {pitch_type}<br>角度: {row["Release Angle"]:.1f}°' # ホバー情報
        ))

    # 軸の設定（アスペクト比を1:1に）
    fig.update_layout(
        xaxis=dict(scaleanchor='y', scaleratio=1, range=[0, 1.2], title=''), # Cos/Sinであることを明示
        yaxis=dict(range=[-0.2, 0.2], title=''),
        showlegend=True, # 凡例全体を表示
        title='Release Angle',
        title_x=0.5,
        margin=dict(l=0,r=0)
    )
    return fig



# 平均値テーブルの作成
def mean_table(df):
    投球数 = df['Velocity'].groupby(df['球種']).size()
    平均球速 = df['Velocity'].groupby(df['球種']).mean().round(1)
    最速 = df['Velocity'].groupby(df['球種']).max().round(1)
    回転数 = df['Total Spin'].groupby(df['球種']).mean().round(1)
    回転効率 = df['Spin Efficiency (release)'].groupby(df['球種']).mean().round(1)
    VB_Spin = df['VB (spin)'].groupby(df['球種']).mean().round(1)
    HB_Spin = df['HB (spin)'].groupby(df['球種']).mean().round(1)
    VB_Trj = df['VB (trajectory)'].groupby(df['球種']).mean().round(1)
    HB_Trj = df['HB (trajectory)'].groupby(df['球種']).mean().round(1)

    rap_list = [投球数, 平均球速, 最速, 回転数, 回転効率, VB_Spin, HB_Spin, VB_Trj, HB_Trj]
    labels = ['N', 'Velo(Mean)', 'Velo(Max)', 'Total_Spin', 'Spin_Eff', 'VB(Spin)', 'HB(Spin)', 'VB(Traj)', 'HB(Traj)']
    output = pd.DataFrame({label: stat for label, stat in zip(labels, rap_list)})
    output = output.reset_index()
    output = output.sort_values(by='N', ascending=False)
    return output

def mean_table2(df):
    N = df['Velocity'].groupby(df['球種']).size()
    RelX = df['Release Side'].groupby(df['球種']).mean().round(2)
    RelZ = df['Release Height'].groupby(df['球種']).max().round(2)
    RelAng = df['Release Angle'].groupby(df['球種']).mean().round(2)
    RelEx = df['Release Extension (ft)'].groupby(df['球種']).mean().round(2)
    VAA = round(0.348*df['Vertical Approach Angle'].groupby(df['球種']).mean(), 1)
    ストライク率 = round(100* df[df['Is Strike']=='Y'].groupby(df['球種']).size() / N, 1)

    rap_list = [N, RelZ, RelX, RelAng, RelEx, VAA, ストライク率]
    labels = ['N', 'Release Height[m]', 'Release Side[m]', 'Release Angle[°]', 'Extension[m]', 'VAA[°]', 'Zone%']
    output = pd.DataFrame({label: stat for label, stat in zip(labels, rap_list)})
    output = output.reset_index()
    output = output.sort_values(by='N', ascending=False)
    return output



# youtube埋め込み用に変換
def get_youtube_embed_url(link):
    if not isinstance(link, str):
        return None

    video_id = None

    if 'watch?v=' in link:
        video_id = link.split('watch?v=')[-1].split('&')[0]
    elif 'youtu.be/' in link:
        video_id = link.split('youtu.be/')[-1].split('?')[0]
    elif 'youtube.com/embed/' in link:
        video_id = link.split('youtube.com/embed/')[-1].split('?')[0]

    if video_id:
        return f"https://www.youtube.com/embed/{video_id}"
    
    return None

