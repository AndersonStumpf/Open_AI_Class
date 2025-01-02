import openai
import os
import json
import yfinance as yf
from dotenv import load_dotenv

load_dotenv(".env")

api_key=os.getenv('API_KEY')

client = openai.Client(api_key=api_key)

def return_quote_historical_price(ticker, period='1mo'):
    ticker_obj = yf.Ticker(f'{ticker}.SA')
    hist = ticker_obj.history(period=period)['Close']
    hist.index = hist.index.strftime('Y%-m%-%d')
    hist = round(hist, 2)
    if len(hist) > 30:
        slice_size = int(len(hist) / 30)
        hist = hist.iloc[::-slice_size][::-1]
    return hist.to_json()


tools = [
    {
        'type': 'function',
        'function': {
            'name': 'return_quote_historical_price',
            'description': 'Returns the daily historical quote for a Bovespa stock',
            'parameters': {
                'type': 'object',
                'properties': {
                    'ticker': {
                        'type': 'string',
                        'descrption': 'The stock ticker. Example: "ABEV3" for Ambev, "PETR4" for Petrobras, etc.',
                    },
                    'period': {
                        'type': 'string',
                        'descrption': 'The period for which historical data will be returned, with "1mo" equivalent to one month of data, "1d" to one day, and "1y" to one year',
                        'enun': ["1d","5d","1mo","6mo","1y","5y","10y","ytd","max"]
                    }
                }
            }
        }
    }
]


available_functions = {'return_quote_historical_price': return_quote_historical_price}


def text_generation(mensagens):

    answer = client.chat.completions.create(
        messages= mensagens,
        model='gpt-4o-mini',
        tools=tools,
        tool_choice='auto'
        )


    tool_calls = answer.choices[0].message.tool_calls

    if tool_calls:
        mensagens.append(answer.choices[0].message)
        for tool_call in tool_calls:
            func_name = tool_call.function.name
            function_to_call = available_functions[func_name]
            func_args = json.loads(tool_call.function.arguments)
            func_return = function_to_call(**func_args)
            mensagens.append({
                'tool_call_id': tool_call.id,
                'role': 'tool',
                'name': func_name,
                'content': func_return
            })

        next_answer = client.chat.completions.create(
            messages= mensagens,
            model='gpt-4o-mini',
            )
        mensagens.append(next_answer.choices[0].message)
    
    print(f'Assistant: {mensagens[-1].content}')

    return mensagens


if __name__ == '__main__':

    mensagens = [{'role': 'user', 'content': 'What is the current stock price of Ambev?'}]
    mensagens = text_generation(mensagens)
