import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# Database Functions
def initialize_database():
    """Create database tables if they don't exist"""
    conn = sqlite3.connect('finance.db')
    cursor = conn.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS records (
                      id INTEGER PRIMARY KEY AUTOINCREMENT,
                      date TEXT,
                      amount REAL,
                      category TEXT,
                      type TEXT)''')  # 'expense' or 'income'

    cursor.execute('''CREATE TABLE IF NOT EXISTS settings (
                      key TEXT PRIMARY KEY,
                      value REAL)''')  # For budget setting

    conn.commit()
    conn.close()

def add_transaction(transaction_type):
    """Add income or expense entries to the database"""
    conn = sqlite3.connect('finance.db')
    cursor = conn.cursor()

    try:
        count = int(input(f"\nHow many {transaction_type}s do you want to add? "))
    except ValueError:
        print("Invalid number.")
        return

    print(f"Enter {transaction_type} in the format: YYYY-MM-DD Category Amount")
    for _ in range(count):
        data = input("> ")
        try:
            date_str, category, amount = data.strip().split()
            datetime.strptime(date_str, "%Y-%m-%d")  # Validate date format
            amount = float(amount)
            cursor.execute("INSERT INTO records (date, amount, category, type) VALUES (?, ?, ?, ?)",
                          (date_str, amount, category, transaction_type))
        except ValueError:
            print("Invalid format. Please try again.")

    conn.commit()
    conn.close()
    print(f"{transaction_type.capitalize()}s added successfully.")

def set_monthly_budget():
    """Set or update the monthly budget"""
    conn = sqlite3.connect('finance.db')
    cursor = conn.cursor()

    try:
        amount = float(input("Set your monthly budget: ₹"))
        cursor.execute("REPLACE INTO settings (key, value) VALUES (?, ?)",
                       ('monthly_budget', amount))
        conn.commit()
        print("Budget set successfully.")
    except ValueError:
        print("Invalid input.")
    conn.close()

# Reporting Functions
def show_monthly_summary():
    """Display a summary of income and expenses by month"""
    conn = sqlite3.connect('finance.db')

    # Get all records
    df = pd.read_sql_query('SELECT * FROM records', conn)
    if df.empty:
        print("No data found.")
        conn.close()
        return

    # Process data
    df['date'] = pd.to_datetime(df['date'])
    df['month'] = df['date'].dt.to_period('M')

    monthly_data = df.groupby(['month', 'type'])['amount'].sum().unstack().fillna(0)
    monthly_data['savings'] = monthly_data.get('income', 0) - monthly_data.get('expense', 0)

    # Display summary
    print("\n--- Monthly Summary ---")
    print(monthly_data)

    # Check budget
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key='monthly_budget'")
    result = cursor.fetchone()

    if result:
        budget = result[0]
        current_month = df['month'].max()
        current_expense = df[(df['month'] == current_month) & (df['type'] == 'expense')]['amount'].sum()

        if current_expense > budget:
            print(f"\n⚠️ ALERT: You exceeded your budget of ₹{budget:,.2f} for {current_month}!")

    conn.close()

def visualize_expenses():
    """Create pie and bar charts of expenses"""
    conn = sqlite3.connect('finance.db')
    df = pd.read_sql_query('SELECT * FROM records WHERE type="expense"', conn)

    if df.empty:
        print("No expenses to visualize.")
        conn.close()
        return

    df['date'] = pd.to_datetime(df['date'])
    df['year'] = df['date'].dt.year

    for year in sorted(df['year'].unique()):
        year_data = df[df['year'] == year]
        expenses = year_data.groupby('category')['amount'].sum().reset_index()

        if expenses.empty:
            continue

        # Create figure with two subplots
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        fig.suptitle(f'Expense Analysis for {year}', fontsize=16)

        # Get consistent colors for both charts
        categories = expenses['category']
        colors = plt.cm.tab20.colors[:len(categories)]

        # Pie Chart
        ax1.pie(expenses['amount'], labels=categories, colors=colors,
                autopct=lambda p: f'₹{p * sum(expenses["amount"]) / 100:.0f}\n({p:.1f}%)',
                startangle=90)
        ax1.set_title('Expense Distribution')

        # Bar Chart
        bars = ax2.bar(categories, expenses['amount'], color=colors)
        ax2.set_title('Expense Amounts')
        ax2.set_ylabel('Amount (₹)')
        ax2.tick_params(axis='x', rotation=45)

        # Add value labels to bars
        for bar in bars:
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width() / 2., height,
                     f'₹{height:,.0f}', ha='center', va='bottom')

        plt.tight_layout()
        plt.show()

    conn.close()

def generate_financial_report():
    """Generate detailed financial report for a specific period"""
    conn = sqlite3.connect('finance.db')
    df = pd.read_sql_query('SELECT * FROM records', conn)

    if df.empty:
        print("No data available.")
        conn.close()
        return

    df['date'] = pd.to_datetime(df['date'])
    df['month'] = df['date'].dt.to_period('M')
    df['year'] = df['date'].dt.year

    print("\nGenerate report by:")
    print("1. Monthly")
    print("2. Annually")
    period_choice = input("Choose an option (1/2): ")

    if period_choice == '1':
        month_input = input("Enter month (YYYY-MM): ")
        try:
            period = pd.Period(month_input)
            filtered_data = df[df['month'] == period]
        except:
            print("Invalid month format.")
            return
    elif period_choice == '2':
        year_input = input("Enter year (YYYY): ")
        try:
            year = int(year_input)
            filtered_data = df[df['year'] == year]
        except:
            print("Invalid year.")
            return
    else:
        print("Invalid option.")
        return

    if filtered_data.empty:
        print("No data for selected period.")
    else:
        summary = filtered_data.groupby('type')['amount'].sum()

        print("\n--- Financial Report ---")
        print(filtered_data[['date', 'type', 'category', 'amount']].to_string(index=False))

        print("\nSummary:")
        print(summary)
        print(f"Savings: ₹{summary.get('income', 0) - summary.get('expense', 0):,.2f}")

    conn.close()

# Main Menu
def display_menu():
    """Display the main menu options"""
    print("\n======= Personal Finance Tracker =======")
    print("1. Add Expense")
    print("2. Add Income")
    print("3. Set Monthly Budget")
    print("4. Show Summary")
    print("5. Visualize Expenses")
    print("6. Generate Financial Report")
    print("7. Exit")

def main():
    initialize_database()

    while True:
        display_menu()
        choice = input("Enter your choice (1-7): ")

        if choice == '1':
            add_transaction('expense')
        elif choice == '2':
            add_transaction('income')
        elif choice == '3':
            set_monthly_budget()
        elif choice == '4':
            show_monthly_summary()
        elif choice == '5':
            visualize_expenses()
        elif choice == '6':
            generate_financial_report()
        elif choice == '7':
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()