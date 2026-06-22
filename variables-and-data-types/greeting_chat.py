from datetime import datetime
#from os import name
name = input("Enter your name: ")

# Get current date and time
now = datetime.now()

# Extract just the time component
current_time = now.time()
if current_time.hour <= 12:
    print(f"Good Morning {name}")
elif current_time.hour < 18:
    print(f"Good afternoon {name}")
else:
    print(f"Good Evening {name}")


