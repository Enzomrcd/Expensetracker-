import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import datetime
from collections import defaultdict

def generate_category_chart(expenses):
    """Generate a pie chart for expense categories."""
    if not expenses:
        return None
    
    # Create a dictionary to store total amount by category
    category_totals = defaultdict(float)
    
    for expense in expenses:
        category_totals[expense.category] += expense.amount
    
    # Convert to DataFrame
    df = pd.DataFrame({
        'Category': list(category_totals.keys()),
        'Amount': list(category_totals.values())
    })
    
    # Create a pie chart
    fig = px.pie(
        df, 
        values='Amount', 
        names='Category',
        title='Expenses by Category',
        color_discrete_sequence=px.colors.sequential.Plasma
    )
    
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(
        margin=dict(l=50, r=50, t=50, b=50),
        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="right",
            x=1.1
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white', size=14),
        title=dict(
            font=dict(size=20)
        ),
        height=500
    )
    fig.update_traces(
        textfont=dict(size=14),
        hole=0.4
    )
    
    return fig.to_json()

def generate_trend_chart(expenses, period='month'):
    """Generate a trend chart for expenses over time."""
    if not expenses:
        return None
    
    # Create a DataFrame
    data = []
    for expense in expenses:
        try:
            if isinstance(expense.date, datetime.datetime):
                date = expense.date
            elif isinstance(expense.date, str):
                date = datetime.datetime.strptime(expense.date, '%Y-%m-%d')
            else:
                continue  # Skip invalid dates
                
            data.append({
                'date': date,
                'amount': expense.amount,
                'category': expense.category
            })
        except (ValueError, TypeError):
            continue  # Skip any date parsing errors
    
    df = pd.DataFrame(data)
    
    # Group by date and sum the amounts
    if period == 'week' or period == 'month':
        # Daily grouping for week or month
        df['date_group'] = df['date'].dt.date
        title = 'Daily Expenses'
    elif period == 'year':
        # Monthly grouping for year
        df['date_group'] = df['date'].dt.strftime('%Y-%m')
        title = 'Monthly Expenses'
    else:
        # Default to daily
        df['date_group'] = df['date'].dt.date
        title = 'Daily Expenses'
    
    daily_totals = df.groupby(['date_group', 'category'])['amount'].sum().reset_index()
    
    # Create a bar chart
    fig = px.bar(
        daily_totals, 
        x='date_group', 
        y='amount',
        color='category',
        title=title,
        labels={'date_group': 'Date', 'amount': 'Amount', 'category': 'Category'},
        color_discrete_sequence=px.colors.sequential.Plasma
    )
    
    fig.update_layout(
        xaxis_title='Date',
        yaxis_title='Amount',
        legend_title='Category',
        barmode='stack',
        margin=dict(l=40, r=20, t=40, b=40),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white')
    )
    
    return fig.to_json()

def get_expense_statistics(expenses):
    """Calculate expense statistics."""
    if not expenses:
        return {
            'total': 0,
            'average_daily': 0,
            'top_category': 'None',
            'largest_expense': 0
        }
    
    # Calculate total spent
    total = sum(expense.amount for expense in expenses)
    
    # Calculate average daily spending
    dates = set()
    for expense in expenses:
        if isinstance(expense.date, datetime.datetime):
            dates.add(expense.date.date())
        else:
            # If date is a string, parse it
            try:
                date = datetime.datetime.strptime(expense.date, '%Y-%m-%d').date()
                dates.add(date)
            except (ValueError, TypeError):
                # Skip invalid dates
                pass
    
    num_days = len(dates) if dates else 1
    average_daily = total / num_days
    
    # Find highest expense
    highest_expense = max(expenses, key=lambda x: x.amount) if expenses else None
    largest_expense = highest_expense.amount if highest_expense else 0
    
    # Calculate category totals
    category_totals = defaultdict(float)
    
    for expense in expenses:
        category_totals[expense.category] += expense.amount
    
    # Find top category
    top_category = max(category_totals.items(), key=lambda x: x[1])[0] if category_totals else 'None'
    
    # Sort categories by amount (descending)
    categories = [
        {'name': cat, 'amount': amount}
        for cat, amount in sorted(category_totals.items(), key=lambda x: x[1], reverse=True)
    ]
    
    return {
        'total': total,
        'average_daily': average_daily,
        'top_category': top_category,
        'largest_expense': largest_expense,
        'categories': categories
    }

def generate_spending_tips(expenses):
    """Generate spending tips based on expense patterns."""
    if not expenses:
        return ["Start tracking your expenses to get personalized saving tips!"]
    
    tips = []
    
    # Calculate category percentages
    total = sum(expense.amount for expense in expenses)
    
    if total <= 0:
        return ["Start tracking your expenses to get personalized saving tips!"]
    
    category_totals = defaultdict(float)
    
    for expense in expenses:
        category_totals[expense.category] += expense.amount
    
    # Calculate percentage for each category
    category_percentages = {cat: (amount / total) * 100 for cat, amount in category_totals.items()}
    
    # Generate tips based on spending patterns
    if 'Food' in category_percentages and category_percentages['Food'] > 30:
        tips.append("You're spending a lot on food. Consider meal planning and cooking at home more often.")
    
    if 'Transport' in category_percentages and category_percentages['Transport'] > 20:
        tips.append("Your transportation costs are high. Try carpooling, public transit, or biking when possible.")
    
    if 'Misc' in category_percentages and category_percentages['Misc'] > 20:
        tips.append("You have many miscellaneous expenses. Try categorizing them more specifically to identify saving opportunities.")
    
    if len(category_totals) <= 2:
        tips.append("Try to categorize your expenses more specifically to get better insights into your spending habits.")
    
    # Add general tips if we don't have specific ones
    if not tips:
        tips = [
            "Track your expenses regularly to get more personalized tips.",
            "Set a budget for each spending category and try to stick to it.",
            "Consider saving a fixed percentage of your income each month.",
            "Review your subscriptions and cancel those you don't use often."
        ]
    
    # Add a random general tip
    general_tips = [
        "Save receipts for major purchases for warranty purposes.",
        "Consider using cash for discretionary spending to better control your budget.",
        "Pay off high-interest debt first to save money on interest payments.",
        "Build an emergency fund to cover 3-6 months of expenses."
    ]
    
    import random
    tips.append(random.choice(general_tips))
    
    return tips
