import dash
from dash import html, dcc
import plotly.graph_objects as go
import plotly.express as px
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

def create_mini_calendar(month_data):
    # Ensure 'day' is a datetime object using .loc[] to modify safely
    month_data.loc[:, 'day'] = pd.to_datetime(month_data['day'])
    
    # Create a copy of the DataFrame to prevent the warning
    month_data = month_data.copy()
    
    # Use .loc[] to modify safely
    month_data.loc[:, 'year_month'] = month_data['day'].dt.to_period('M')

    # Get the most recent 6 months (you can adjust the period if needed)
    current_month = pd.to_datetime('today').normalize().to_period('M')
    recent_months = pd.period_range(current_month - 5, current_month, freq='M')
    
    # Create a copy of the filtered data
    month_data_filtered = month_data.loc[month_data['year_month'].isin(recent_months)].copy()
    
    if month_data_filtered.empty:
        return px.imshow(
            [[None]*7]*6,  # Empty grid
            labels=dict(x="Day of Week", y="Day", color="Sleep Score"),
            x=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
            color_continuous_scale="Viridis",
            aspect="auto"
        ).update_layout(
            title="No Data Available",
            height=250,
            width=250,
            margin=dict(l=10, r=10, t=30, b=10),
            xaxis=dict(showticklabels=False),
            yaxis=dict(showticklabels=False),
            showlegend=False
        )

    # Loop over each month, including months with sparse data
    calendar_figs = []
    for period in recent_months:
        month_data_period = month_data_filtered[month_data_filtered['year_month'] == period].copy()
        
        # Skip empty months
        if month_data_period.empty:
            continue
        
        # Pivot the data to create a grid format (rows = days, columns = weekdays)
        month_data_pivot = month_data_period.pivot_table(
            index=month_data_period['day'].dt.day,
            columns=month_data_period['day'].dt.weekday,
            values='sleep_score',
            aggfunc='first'
        )

        # Fill missing columns for weekdays (if any)
        for weekday in range(7):
            if weekday not in month_data_pivot.columns:
                month_data_pivot[weekday] = None
        
        # Reindex columns to ensure the order is correct (Mon-Sun)
        month_data_pivot = month_data_pivot.reindex(columns=[0, 1, 2, 3, 4, 5, 6])

        # Add the figure for this month to the list
        calendar_figs.append(px.imshow(
            month_data_pivot,
            labels=dict(x="Day of Week", y="Day", color="Sleep Score"),
            x=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
            color_continuous_scale="Viridis",
            aspect="auto"
        ).update_layout(
            title=period.strftime('%b %Y'),
            height=250,
            width=250,
            margin=dict(l=10, r=10, t=30, b=10),
            xaxis=dict(showticklabels=False),
            yaxis=dict(showticklabels=False),
            showlegend=False
        ))

    return calendar_figs

# Generate mini calendars for each of the last 6 months
calendar_figs = []
# Get the last 6 months including the current month
recent_months = pd.period_range(pd.to_datetime("today").to_period("M") - 5, pd.to_datetime("today").to_period("M"), freq="M")

for period in recent_months:
    month_data = sleep_calendar_data[sleep_calendar_data['day'].dt.to_period('M') == period]
    fig_list = create_mini_calendar(month_data)
    if isinstance(fig_list, list):
        calendar_figs.extend(fig_list)
    else:
        calendar_figs.append(fig_list)

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
        "width": "25%",
        "height": "600px",  # adjust as needed
        "overflowY": "scroll",
        "display": "inline-block",
        "verticalAlign": "top",
        "paddingRight": "10px"
    })
    

# Layout
app.layout = html.Div([
    html.H1("Sleep Dashboard", style={"textAlign": "center"}),

    html.Div([
        # Display the mini calendars in a grid
        html.Div([dcc.Graph(figure=fig, config={"displayModeBar": False}) for fig in calendar_figs],
                 style={"display": "flex", "flexWrap": "wrap", "justifyContent": "space-between"}),

        # Heart rate figure
        dcc.Graph(figure=hr_fig, config={"displayModeBar": False}),
    ], style={"width": "70%", "display": "inline-block", "padding": "0 20px"}),

    html.Div(summary_cards(), style={"width": "25%", "display": "inline-block", "verticalAlign": "top"}),

], style={"padding": "20px", "fontFamily": "Arial"})

# Run server
if __name__ == '__main__':
    app.run(debug=True, port=8050)
