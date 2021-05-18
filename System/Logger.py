import sys
import colorama

class Console:
    @staticmethod
    def info(message):
        print(colorama.Back.CYAN + colorama.Fore.BLACK + " INFO " + colorama.Style.RESET_ALL + f" {message}")
    
    @staticmethod
    def error(message):
        print(colorama.Back.RED + colorama.Fore.BLACK + " ERROR " + colorama.Style.RESET_ALL + f" {message}")

    @staticmethod
    def warn(message):
        print(colorama.Back.YELLOW + colorama.Fore.BLACK + " WARNING " + colorama.Style.RESET_ALL + f" {message}")
    
    @staticmethod
    def success(message):
        print(colorama.Back.GREEN + colorama.Fore.BLACK + " SUCCESS " + colorama.Style.RESET_ALL + f" {message}")

    @staticmethod
    def question(message):
        x = input(colorama.Style.BRIGHT + colorama.Fore.YELLOW + f"{message} [Y/n]").lower()
        if x in "ny":
            return "ny".index(x)
        else:
            return Console.question(message)
