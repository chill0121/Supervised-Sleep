import dash
from dash import html, dcc
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import pandas as pd
from config import settings
import calendar
from datetime import datetime

# Initialize Dash app
app = dash.Dash(__name__)
app.title = "Sleep Dashboard"

# Load data
sleep_calendar_data = pd.read_json(settings.TAB_DATA_DIR + "/sleep_calendar.json")
heartrate_data = pd.read_json(settings.TAB_DATA_DIR + "/heartrate_trends.json")
summary_stats_data = pd.read_json(settings.TAB_DATA_DIR + "/summary_statistics.json")
weekly_averages_data = pd.read_json(settings.TAB_DATA_DIR + "/weekly_averages.json")
week_comparison_data = pd.read_json(settings.TAB_DATA_DIR + "/week_comparison.json")
sleep_breakdown_data = pd.read_json(settings.TAB_DATA_DIR + "/sleep_breakdown.json")
chronotype_data = pd.read_json(settings.TAB_DATA_DIR + "/chronotype_stats.json", convert_dates=False)

# Prepare data
sleep_calendar_data['day'] = pd.to_datetime(sleep_calendar_data['day'])
sleep_calendar_data['month'] = sleep_calendar_data['day'].dt.month
sleep_calendar_data['year'] = sleep_calendar_data['day'].dt.year
sleep_calendar_data['date_str'] = sleep_calendar_data['day'].dt.strftime('%Y-%m-%d')
sleep_calendar_data['year_month'] = pd.to_datetime(sleep_calendar_data['day']).dt.to_period('M')

# Calculate global min and max for color scaling
sleep_min = sleep_calendar_data['sleep_score'].min()
sleep_max = sleep_calendar_data['sleep_score'].max()

def create_sleep_score_heatmap(sleep_calendar_data):
    # Gracefully handle incomplete latest data
    latest_available_day = sleep_calendar_data[sleep_calendar_data['sleep_score'].notna()]['day'].max()
    if pd.isna(latest_available_day):
        latest_available_day = pd.to_datetime('today').normalize()

    end_date = latest_available_day
    start_date = (end_date - pd.DateOffset(months=6)).normalize()

    # Create continuous date range
    full_range = pd.date_range(start=start_date, end=end_date, freq='D')

    # Reindex to include all days
    sleep_data = sleep_calendar_data.set_index('day').reindex(full_range).reset_index()
    sleep_data.rename(columns={'index': 'day'}, inplace=True)
    # Sunday = 0, Saturday = 6
    sleep_data['weekday'] = sleep_data['day'].dt.weekday.apply(lambda x: (x + 1) % 7)
    # Anchor weeks to the Sunday on or before the start date
    calendar_start = start_date - pd.Timedelta(days=((start_date.weekday() + 1) % 7))
    sleep_data['week'] = ((sleep_data['day'] - calendar_start).dt.days // 7).astype(int)
    sleep_data['month_str'] = sleep_data['day'].dt.strftime('%b')
    sleep_data['day_number'] = sleep_data['day'].dt.day

    # Create 7xN matrix of sleep scores
    weeks = sleep_data['week'].max() + 1
    z = [[None for _ in range(weeks)] for _ in range(7)]
    text = [["" for _ in range(weeks)] for _ in range(7)]

    for _, row in sleep_data.iterrows():
        week = row['week']
        weekday = row['weekday']
        score = row['sleep_score']
        date_str = row['day'].strftime('%Y-%m-%d')
        z[weekday][week] = score
        text[weekday][week] = f"{date_str}<br>Sleep Score: {score:.0f}" if pd.notna(score) else f"{date_str}<br>No data"

    # Plot annotations (month label and day numbers)
    # month_labels = sleep_data.groupby('week').first().reset_index()
    seen_month = set() # Tracks if month has been annotated already
    annotations = []
    for _, row in sleep_data.iterrows():
        # Month label
        label = row['month_str']
        if label not in seen_month:
            annotations.append(dict(
                x=row['week'],
                y=6.75,
                text=label,
                showarrow=False,
                font=dict(size=12)
            ))
            seen_month.add(label)
        # Tile day number
        annotations.append(dict(
                x=row['week'],
                y=row['weekday'],
                text=row['day_number'],
                showarrow=False,
                font=dict(size=8),
                xshift=11,
                yshift=17
            ))

    # Heatmap
    fig = go.Figure(data=go.Heatmap(
        z=z,
        x=list(range(weeks)),
        y=["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"],
        colorscale='Viridis',
        showscale=True,
        zmin=sleep_min,
        zmax=sleep_max,
        hoverinfo='text',
        text=text
    ))

    fig.update_layout(
        title=None,
        yaxis=dict(autorange="reversed"),
        annotations=annotations,
        margin=dict(t=40, l=10, r=10, b=10),
        height=400,
        width=1140,
    )
    fig.update_xaxes(showgrid = False, showticklabels = False)
    fig.update_yaxes(showgrid = False)

    return fig

# Create heartrate line chart
hr_fig = px.line(
    heartrate_data,
    x="day",
    y="avg_heart_rate",
    title=None,
    markers=True
)
hr_fig.update_layout(height=300, margin=dict(l=10, r=10, t=30, b=10))

# Create summary stats display
def summary_cards():
    df = summary_stats_data.sort_values("day", ascending=False)  # Most recent first

    cards = []
    for _, row in df.iterrows():
        card = html.Div([
            html.H4(pd.to_datetime(row['day']).strftime("%b %d"), style={"margin": "5px", "textAlign": "center"}),
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
        "height": "765px",  # adjust as needed
        "overflowY": "scroll",
        "display": "inline-block",
        "verticalAlign": "top",
        "paddingRight": "10px"
    })

# Create top statistics bar
def create_top_stats_bar():
    # Extract data from JSON (single row each)
    weekly_avg = weekly_averages_data.iloc[0] if not weekly_averages_data.empty else {}
    week_comp = week_comparison_data.iloc[0] if not week_comparison_data.empty else {}
    sleep_brkdwn = sleep_breakdown_data.iloc[0] if not sleep_breakdown_data.empty else {}
    chrono = chronotype_data.iloc[0] if not chronotype_data.empty else {}
    
    # Helper to format delta with arrow
    def format_delta(val):
        if pd.isna(val) or val == 0:
            return "—"
        return f"+{int(val)}" if val > 0 else f"{int(val)}"
    
    # Calculate sleep stage percentages
    total_sleep = sleep_brkdwn.get('avg_total_seconds', 1)
    if total_sleep > 0:
        deep_pct = (sleep_brkdwn.get('avg_deep_seconds', 0) / total_sleep) * 100
        rem_pct = (sleep_brkdwn.get('avg_rem_seconds', 0) / total_sleep) * 100
        light_pct = (sleep_brkdwn.get('avg_light_seconds', 0) / total_sleep) * 100
    else:
        deep_pct = rem_pct = light_pct = 0
    
    return html.Div([
        # Row 1: Week Averages & Comparison
        html.Div([
            # 7-Day Averages Card
            html.Div([
                html.H4("7-Day Averages", style={"margin": "0 0 10px 0", "fontSize": "16px", "color": "#555"}),
                html.Div([
                    html.Span("Sleep: ", style={"fontWeight": "normal", "color": "#666"}),
                    html.Span(f"{int(weekly_avg.get('avg_sleep_score', 0))}", style={"fontWeight": "bold", "fontSize": "24px", "color": "#333"}),
                ], style={"marginBottom": "5px"}),
                html.Div([
                    html.Span("Activity: ", style={"fontWeight": "normal", "color": "#666"}),
                    html.Span(f"{int(weekly_avg.get('avg_activity_score', 0))}", style={"fontWeight": "bold", "fontSize": "24px", "color": "#333"}),
                ], style={"marginBottom": "5px"}),
                html.Div([
                    html.Span("Readiness: ", style={"fontWeight": "normal", "color": "#666"}),
                    html.Span(f"{int(weekly_avg.get('avg_readiness_score', 0))}", style={"fontWeight": "bold", "fontSize": "24px", "color": "#333"}),
                ]),
            ], style={"flex": "1", "padding": "15px", "backgroundColor": "#f9f9f9", "borderRadius": "8px", "marginRight": "10px"}),
            
            # This Week vs Last Week Card
            html.Div([
                html.H4("This Week vs Last", style={"margin": "0 0 10px 0", "fontSize": "16px", "color": "#555"}),
                html.Div([
                    html.Span("Sleep: ", style={"fontWeight": "normal", "color": "#666"}),
                    html.Span(format_delta(week_comp.get('sleep_delta')), style={"fontWeight": "bold", "fontSize": "20px", "color": "#2ecc71" if week_comp.get('sleep_delta', 0) > 0 else "#e74c3c" if week_comp.get('sleep_delta', 0) < 0 else "#333"}),
                ], style={"marginBottom": "5px"}),
                html.Div([
                    html.Span("Activity: ", style={"fontWeight": "normal", "color": "#666"}),
                    html.Span(format_delta(week_comp.get('activity_delta')), style={"fontWeight": "bold", "fontSize": "20px", "color": "#2ecc71" if week_comp.get('activity_delta', 0) > 0 else "#e74c3c" if week_comp.get('activity_delta', 0) < 0 else "#333"}),
                ], style={"marginBottom": "5px"}),
                html.Div([
                    html.Span("Readiness: ", style={"fontWeight": "normal", "color": "#666"}),
                    html.Span(format_delta(week_comp.get('readiness_delta')), style={"fontWeight": "bold", "fontSize": "20px", "color": "#2ecc71" if week_comp.get('readiness_delta', 0) > 0 else "#e74c3c" if week_comp.get('readiness_delta', 0) < 0 else "#333"}),
                ]),
            ], style={"flex": "1", "padding": "15px", "backgroundColor": "#f9f9f9", "borderRadius": "8px", "marginRight": "10px"}),
            
            # Sleep Breakdown Card
            html.Div([
                html.H4("Sleep Breakdown (7-day avg)", style={"margin": "0 0 10px 0", "fontSize": "16px", "color": "#555"}),
                html.Div([
                    html.Div([
                        html.Span(f"Deep: {deep_pct:.0f}%", style={"marginRight": "15px", "color": "#666"}),
                        html.Span(f"REM: {rem_pct:.0f}%", style={"marginRight": "15px", "color": "#666"}),
                        html.Span(f"Light: {light_pct:.0f}%", style={"color": "#666"}),
                    ], style={"marginBottom": "8px"}),
                    html.Div([
                        html.Span(f"Total: {sleep_brkdwn.get('avg_total_hours', 0):.1f} hrs", style={"fontWeight": "bold", "fontSize": "20px", "color": "#333"}),
                    ]),
                ]),
            ], style={"flex": "1", "padding": "15px", "backgroundColor": "#f9f9f9", "borderRadius": "8px", "marginRight": "10px"}),
            
            # Chronotype/Sleep Timing Card
            html.Div([
                html.H4("Sleep Timing (7-day avg)", style={"margin": "0 0 10px 0", "fontSize": "16px", "color": "#555"}),
                html.Div([
                    html.Span("Bedtime: ", style={"fontWeight": "normal", "color": "#666"}),
                    html.Span(f"{chrono.get('avg_bedtime', 'N/A')}", style={"fontWeight": "bold", "fontSize": "18px", "color": "#333"}),
                ], style={"marginBottom": "5px"}),
                html.Div([
                    html.Span("Wake Time: ", style={"fontWeight": "normal", "color": "#666"}),
                    html.Span(f"{chrono.get('avg_wake_time', 'N/A')}", style={"fontWeight": "bold", "fontSize": "18px", "color": "#333"}),
                ], style={"marginBottom": "5px"}),
                html.Div([
                    html.Span("Efficiency: ", style={"fontWeight": "normal", "color": "#666"}),
                    html.Span(f"{int(chrono.get('avg_efficiency', 0))}%", style={"fontWeight": "bold", "fontSize": "18px", "color": "#333"}),
                ]),
            ], style={"flex": "1", "padding": "15px", "backgroundColor": "#f9f9f9", "borderRadius": "8px"}),
            
        ], style={"display": "flex", "marginBottom": "20px"}),
    ])

# Layout
app.layout = html.Div([
    html.H1("Sleep Dashboard", style={"textAlign": "center", "marginBottom": "20px"}),

    # Top Statistics Bar
    create_top_stats_bar(),

    html.Div([
        # Sleep Calendar
        html.Div([
            html.Div([
                html.H4("Sleep Score Calendar", style={"textAlign": "center"}),
                dcc.Graph(figure=create_sleep_score_heatmap(sleep_calendar_data))
            ])
        ], style={"display": "flex", "alignItems": "flex-start"}),

        # Heart rate figure
        html.H4("Average Sleep Heart Rate", style={"textAlign": "center"}),
        dcc.Graph(figure=hr_fig, config={"displayModeBar": False}),
    ], style={"width": "70%", "display": "inline-block", "padding": "0 20px"}),

    # Summary cards on the right
    html.Div(summary_cards(), style={"width": "25%", "display": "inline-block", "verticalAlign": "top"}),

], style={"padding": "20px", "fontFamily": "Arial"})

# Run server
if __name__ == '__main__':
    app.run(debug=True, port=8050)