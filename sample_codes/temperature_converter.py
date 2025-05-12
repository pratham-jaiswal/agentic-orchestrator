def convert_to_fahrenheit(celsius):
    '''Converts Celsius to Fahrenheit.'''
    return (celsius * 9/5) + 32

def process_temperature_input(temp_input):
    '''Validates and processes temperature input.'''
    try:
        celsius = float(temp_input)
        fahrenheit = convert_to_fahrenheit(celsius)
        return f"{celsius}°C = {fahrenheit:.2f}°F"
    except ValueError:
        return "❌ Invalid input. Please enter a numeric value."

def start_conversion(temp_input):
    '''Initiates the temperature conversion process.'''
    result = process_temperature_input(temp_input)
    return result


if __name__ == "__main__":
    temperature = input("Enter temperature in Celsius: ")
    start_conversion(temperature)
