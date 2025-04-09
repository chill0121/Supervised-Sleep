import dash
from dash import html, dcc
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from config import settings

# Initialize Dash app
app = dash.Dash(__name__)
app.title = "Sleep Dashboard"

# Load data
sleep_calendar_data = pd.read_json(settings.TAB_DATA_DIR + "/sleep_calendar.json")
heartrate_data = pd.read_json(settings.TAB_DATA_DIR + "/heartrate_trends.json")
summary_stats_data = pd.read_json(settings.TAB_DATA_DIR + "/summary_statistics.json")

# Prepare data
sleep_calendar_data['day'] = pd.to_datetime(sleep_calendar_data['day'])
sleep_calendar_data['month'] = sleep_calendar_data['day'].dt.month
sleep_calendar_data['year'] = sleep_calendar_data['day'].dt.year
sleep_calendar_data['date_str'] = sleep_calendar_data['day'].dt.strftime('%Y-%m-%d')
sleep_calendar_data['year_month'] = pd.to_datetime(sleep_calendar_data['day']).dt.to_period('M')

def create_mini_calendar(month_data, zmin=None, zmax=None, show_legend=False):
    if month_data.empty:
        return px.imshow(
            [[None]*7]*6,
            labels=dict(x="", y="", color="Sleep Score"),
            x=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
            color_continuous_scale="Viridis",
            aspect="auto",
            zmin=zmin,
            zmax=zmax
        ).update_layout(
            title="No Data Available",
            height=250,
            width=250,
            margin=dict(l=10, r=10, t=30, b=10),
            xaxis=dict(showticklabels=True, tickvals=list(range(7)), ticktext=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]),
            yaxis=dict(showticklabels=False),
            coloraxis_showscale=show_legend
        )

    month_data = month_data.copy()
    month_data['day'] = pd.to_datetime(month_data['day'])

    first_day = month_data['day'].min().replace(day=1)
    last_day = (first_day + pd.offsets.MonthEnd(1)).normalize()

    calendar_start = first_day - pd.Timedelta(days=first_day.weekday())
    calendar_end = last_day + pd.Timedelta(days=6 - last_day.weekday())

    full_range = pd.date_range(calendar_start, calendar_end, freq='D')
    calendar_df = pd.DataFrame({'day': full_range})
    calendar_df['week'] = ((calendar_df['day'] - calendar_start).dt.days // 7).astype(int)
    calendar_df['weekday'] = calendar_df['day'].dt.weekday
    calendar_df['day_number'] = calendar_df['day'].dt.day
    calendar_df['date_str'] = calendar_df['day'].dt.strftime('%Y-%m-%d')

    merged = calendar_df.merge(month_data[['day', 'sleep_score']], on='day', how='left')

    calendar_grid = merged.pivot(index='week', columns='weekday', values='sleep_score')
    day_number_grid = merged.pivot(index='week', columns='weekday', values='day_number')
    date_str_grid = merged.pivot(index='week', columns='weekday', values='date_str')

    for col in range(7):
        if col not in calendar_grid.columns:
            calendar_grid[col] = None
            day_number_grid[col] = None
            date_str_grid[col] = None

    calendar_grid = calendar_grid[[0,1,2,3,4,5,6]]
    day_number_grid = day_number_grid[[0,1,2,3,4,5,6]]
    date_str_grid = date_str_grid[[0,1,2,3,4,5,6]]

    z_values = calendar_grid.values
    custom_hover = [
    [
        f"Sleep Score: {int(z_values[i][j])}" if not pd.isna(z_values[i][j]) else ""
        for j in range(7)
    ]
    for i in range(len(z_values))
]

    fig = go.Figure()

    # Add heatmap
    fig.add_trace(go.Heatmap(
        z=z_values,
        x=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        y=list(range(len(calendar_grid))),  # fake y-axis
        hoverinfo='text',
        text=custom_hover,
        colorscale='Viridis',
        zmin=zmin,
        zmax=zmax,
        showscale=show_legend,
        colorbar=dict(title="Sleep Score") if show_legend else None
    ))

    # Overlay day numbers in top-right of each cell
    annotations = []
    for i in range(len(day_number_grid)):
        for j in range(7):
            val = day_number_grid.iloc[i, j]
            if pd.notna(val):
                annotations.append(dict(
                    text=str(int(val)),
                    x=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][j],
                    y=i,
                    xanchor='right',
                    yanchor='top',
                    showarrow=False,
                    font=dict(size=10, color="white"),
                    xshift=17,  # adjust position
                    yshift=20  # adjust position
                ))

    fig.update_layout(
        title=first_day.strftime('%B %Y'),
        height=250,
        width=250,
        margin=dict(l=10, r=10, t=30, b=10),
        xaxis=dict(
            tickvals=list(range(7)),
            ticktext=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
            showticklabels=True
        ),
        yaxis=dict(showticklabels=False),
        annotations=annotations
    )

    return fig


# Calculate global min and max for color scaling
global_min = sleep_calendar_data['sleep_score'].min()
global_max = sleep_calendar_data['sleep_score'].max()

# Create a standalone figure for the master colorbar
legend_fig = go.Figure()

# Add a dummy heatmap just to generate the colorbar
legend_fig.add_trace(go.Heatmap(
    z=[[global_min, global_max]],
    colorscale="Viridis",
    showscale=True,
    opacity=0, # Hides the dumby heatmap plot
    colorbar=dict(
        title="Sleep Score",
        titleside="right",
        ticks="outside",
        len=1.0,
        thickness=20,
        tickfont=dict(size=12),
        titlefont=dict(size=14),
        yanchor="middle",
        y=0.5
    )
))

# Hide axes and margins
legend_fig.update_layout(
    height=500,
    width=200,
    margin=dict(l=0, r=0, t=30, b=0),
    xaxis=dict(visible=False),
    yaxis=dict(visible=False),
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)"
)

# Generate mini calendars for the last 6 months using shared scale
calendar_figs = []

for idx, period in enumerate(pd.period_range(
    pd.to_datetime('today').normalize().to_period('M') - 5,
    pd.to_datetime('today').normalize().to_period('M'),
    freq='M'
)):
    month_data = sleep_calendar_data[sleep_calendar_data['year_month'] == period]
    calendar_figs.append(create_mini_calendar(
        month_data, zmin=global_min, zmax=global_max, show_legend=False  # Only show legend on first calendar
    ))

# Create heartrate line chart
hr_fig = px.line(
    heartrate_data,
    x="day",
    y="avg_heart_rate",
    title="Average Sleep Heart Rate",
    markers=True
)
hr_fig.update_layout(height=300, margin=dict(l=10, r=10, t=30, b=10))

# Create summary stats display
def summary_cards():
    df = summary_stats_data.sort_values("day", ascending=False)  # Most recent first

    cards = []
    for _, row in df.iterrows():
        card = html.Div([
            html.H4(pd.to_datetime(row['day']).strftime("%b %d"), style={"marginBottom": "5px"}),
            html.P(f"Sleep Score: {row['sleep_score']}", style={"margin": "2px"}),
            html.P(f"Activity Score: {row['activity_score']}", style={"margin": "2px"}),
            html.P(f"Readiness Score: {row['readiness_score']}", style={"margin": "2px"}),
        ], style={
            "border": "1px solid #ccc",
            "padding": "10px",
            "marginBottom": "10px",
            "borderRadius": "10px",
            "boxShadow": "0 2px 4px rgba(0, 0, 0, 0.1)",
            "backgroundColor": "#f9f9f9"
        })
        cards.append(card)

    return html.Div(cards, style={
        "width": "45%",
        "height": "700px",  # adjust as needed
        "overflowY": "scroll",
        "display": "inline-block",
        "verticalAlign": "top",
        "paddingRight": "10px"
    })

# Layout
app.layout = html.Div([
    html.H1("Sleep Dashboard", style={"textAlign": "center"}),

    html.Div([
        # Left section: master legend and mini calendars
        html.Div([
            # Master legend
            html.Div(
                dcc.Graph(figure=legend_fig, config={"displayModeBar": False}),
                style={"marginRight": "20px"}
            ),

            # Mini calendars
            html.Div(
                [dcc.Graph(figure=fig, config={"displayModeBar": False}) for fig in calendar_figs],
                style={"display": "flex", "flexWrap": "wrap", "gap": "20px"}
            )
        ], style={"display": "flex", "alignItems": "flex-start"}),

        # Heart rate figure
        dcc.Graph(figure=hr_fig, config={"displayModeBar": False}),
    ], style={"width": "70%", "display": "inline-block", "padding": "0 20px"}),

    # Summary cards on the right
    html.Div(summary_cards(), style={"width": "25%", "display": "inline-block", "verticalAlign": "top"}),

], style={"padding": "20px", "fontFamily": "Arial"})

# Run server
if __name__ == '__main__':
    app.run(debug=True, port=8050)