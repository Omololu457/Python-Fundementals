'''this is a code for a game that is based on guessing a random number between 1 and 10
Lottery Game'''

import random
user_chance = 0
user_num_choice_1 = int(input("Enter a number for the front: "))
user_num_choice_2 = int(input(f"Enter a number from {user_num_choice_1} to: "))
user_choice = int(input("Enter a number: "))
while user_chance <= 10:
    num = random.randint(user_num_choice_1, user_num_choice_2)
    print(f"The random number was {num}")
    print(f"Your number was {user_choice}")
    user_choice = int(input("Enter a number: "))
    if user_choice == num:
        print("You win!")
        break
    else:
        print("You lose!")
        user_chance = user_chance + 1



