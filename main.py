import pandas as pd
import yfinance as yf
from dotenv import load_dotenv
import writer as wf
import writer.ai

# 1. Load environment variables (if needed)
load_dotenv()

# 2. State Management: Initialize and manage the application's state


def initialize_state():
    """
    Initialize the application state with default values.
    """
    initial_state = wf.init_state({
        "app_title": "Stock Analysis Application",  # Application title
        "selected_stock": "",                       # User-selected stock ticker
        "time_frame": "",                           # User-selected time frame
        "timeframe_options": {                      # Time frame options for the user to select
            "1d": "Past Day",
            "5d": "Past Five Days",
            "1mo": "Past Month",
            "6mo": "6 Months",
            "1y": "1 Year",
        },
        "stock_info": {},                           # To store stock info
        "stock_history": None,                      # To store historical stock data
        # To store the DataFrame of stock history
        "stock_dataframe": None,
        "stock_summary": "",
        "stock_summary_visible": False,
        "msg": ""                                   # To store success/error messages
    })
    return initial_state

# 3. Updating the State: Modify state values


def _update_message(state, message=""):
    """
    Update the message state to display success or error messages.
    """
    state["msg"] = message

# 4. Event Handling: Handle user actions, such as selecting a stock and time frame


def handle_stock_selection(state, payload):
    """
    Handle the event when a user selects a stock ticker and time frame.
    """
    # Extract values from the payload (usually from UI events)
    stock_ticker = state['ticker']
    time_frame = state['time_frame']

    if not stock_ticker or not time_frame:
        # Set an error message if the input is invalid
        _update_message(
            state, "-Please provide both stock ticker and timeframe.")
        return

    try:
        # Fetch stock data using the provided stock ticker and time frame
        stock_info, stock_history = fetch_stock_data(stock_ticker, time_frame)

        # Store the fetched data in the state
        state["selected_stock"] = stock_ticker
        state["time_frame"] = time_frame
        state["stock_info"] = stock_info
        state["stock_history"] = stock_history

        # Convert stock history to a DataFrame and store it in the state
        stock_dataframe = pd.DataFrame(stock_history)
        state["stock_dataframe"] = stock_dataframe

        # Generate a summary and store it in the state
        state["stock_summary"] = generate_summary(state)

        # Set a success message
        _update_message(
            state, f"+Data for {stock_ticker} has been retrieved successfully.")
        state["stock_summary_visible"] = True
    except Exception as e:
        # Set an error message in case of failure
        _update_message(state, f"-Failed to retrieve data: {str(e)}")

# 5. Functionality: Fetching data and interacting with APIs


def fetch_stock_data(stock_ticker, time_frame):
    """
    Fetch stock data from yFinance using the provided stock ticker and time frame.
    """
    stock_data = yf.Ticker(stock_ticker)

    # Get basic stock information
    stock_info = {
        "name": stock_data.info.get("longName"),
        "sector": stock_data.info.get("sector"),
        "industry": stock_data.info.get("industry"),
        "market_cap": stock_data.info.get("marketCap"),
        "pe_ratio": stock_data.info.get("trailingPE"),
        "dividend_yield": stock_data.info.get("dividendYield")
    }

    # Get historical stock data
    stock_history = stock_data.history(period=time_frame)
    # Convert index to a normal column for easier handling
    stock_history.reset_index(inplace=True)
    print(stock_info)

    return stock_info, stock_history

# 6. LLM Interaction: Generate a summary using a language model


def generate_summary(state):
    """
    Generate a financial summary using an AI model.
    """
    # Prepare the prompt with the necessary stock data
    prompt_data = f"""
    Company: {state['stock_info']['name']}
    Sector: {state['stock_info']['sector']}
    Industry: {state['stock_info']['industry']}
    Stock Ticker: {state['selected_stock']}
    Market Capitalization: {state['stock_info']['market_cap']}
    P/E Ratio: {state['stock_info']['pe_ratio']}
    Dividend Yield: {state['stock_info']['dividend_yield']}
    """

    # Initialize a conversation with the AI model
    config = {'model': 'palmyra-x-002-32k'}
    conversation = writer.ai.Conversation(
        "You are an assistant that helps financial analysts with stock analysis based on the provided stock information", config)
    conversation += {"role": "user", "content": prompt_data}

    # Get the response from the model and return it
    response = conversation.complete()
    return response


# 7. Application Start: Initialize the state and handle an event
state = initialize_state()
