class TextBiggener:
    def __init__(self):
        self._big_numbers = self._parse_file("big_numbers.txt")
        self._big_numbers_shadows = self._parse_file("big_numbers_shadows.txt")
        self._test_str = "1234567890abcdefghijklmnopqrstuvxyz.!?-/:"

    @staticmethod
    def _parse_file(filename: str, separator: str = "#", equal_width: bool = False):
        result = []
        with open(filename, "r", encoding="utf-8") as f:
            number = []
            the_longest_line = 0
            longest_line = 0
            for line in f:
                stripped_line = line.rstrip()
                if stripped_line != "#":
                    number.append(stripped_line)
                    if len(stripped_line) > longest_line:
                        longest_line = len(stripped_line)
                    if len(stripped_line) > the_longest_line:
                        the_longest_line = len(stripped_line)
                else:
                    if longest_line == 0:
                        longest_line = 5
                    if len(number) > 0:
                        for i in range(len(number)):
                            number[i] = f"{number[i]:<{longest_line}}"
                        result.append(number)
                        number = []
                        longest_line = 0

            if equal_width:
                for i in range(len(number)):
                   number[i] = f"{number[i]:<{longest_line}}"
            result.append(number)
        return result

    def _enbiggen(self, index: int, shadow: bool = False):
        if shadow:
            return self._big_numbers_shadows[index]
        else:
            return self._big_numbers[index]

    def biggen_text(self, text: str, shadow: bool = False, kerning: int = 1, monospace_size: int = 0, space_width: int = 3):
        big_str = []
        for i, n in enumerate(text):
            index = self._test_str.find(n.lower())
            if index != -1:
                biggened = self._enbiggen(index, shadow)
                if i == 0:
                    for line in biggened:
                        big_str.append(f"{line:>{monospace_size}}")
                else:
                    for j, line in enumerate(biggened):
                        big_str[j] = big_str[j] + " "*kerning + f"{line:>{monospace_size}}"
            if index == -1 and n == " ":
                for j in range(len(big_str)):
                    big_str[j] += " "*space_width
        return big_str

class LogoLoader:
    @staticmethod
    def load_logo(filename: str):
        with open(filename, 'r') as f:
            logo = f.readlines()
            longest_line = 0
            for l in logo:
                if len(l) > longest_line:
                    longest_line = len(l)
            for i in range(len(logo)):
                logo[i] = f"{logo[i].rstrip():<{longest_line-1}}"
            return logo

class WeatherSymbols:
    def __init__(self):
        self._symbols = TextBiggener._parse_file("weather_icons.txt", equal_width=True)

    def _find_symbol(self, weather_str: str):
        weather_str = weather_str.lower()
        if weather_str == "":
            return self._symbols[0]
        elif weather_str.find("overcast") != -1:
            return self._symbols[1]
        elif weather_str.find("clouds") != -1:
            return self._symbols[10]
        elif weather_str.find("fog") != -1:
            return self._symbols[2]
        elif weather_str.find("rain") != -1:
            if weather_str.find("light") != -1:
                return self._symbols[3]
            else:
                return self._symbols[4]
        elif weather_str.find("snow") != -1:
            if weather_str.find("light") != -1:
                return self._symbols[5]
            else:
                return self._symbols[6]
        elif weather_str == "thunderstorm":
            return self._symbols[7]
        elif weather_str.find('drizzle') != -1:
            return self._symbols[9]
        else:
            return self._symbols[8]

    def weather_string_to_symbol(self, weather_str: str, add_string: bool = False):
        symbol = self._find_symbol(weather_str)
        longest_line = 0
        for s in symbol:
            if len(s) > longest_line:
                longest_line = len(s)
        for i in range(len(symbol)):
            symbol[i] = f"{symbol[i]: <{longest_line}}"
        if add_string:
            if weather_str == "":
                weather_str = "Sunny"
            symbol.append("")
            symbol.append(f"{weather_str:^{longest_line}}")
        return symbol

if __name__ == "__main__":
    LogoLoader.load_logo("logo.txt")