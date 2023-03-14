class Utils():
    def conv_num_str(num):
        max_count = 1000
        min_count = 0.1
        formats = [['', 'm', 'μ', 'n', 'p', 'f'], ['', 'k', 'M', 'G']]
        index1 = 0
        index2 = 0
        if abs(num) < min_count and num != 0:
            index1 = 0
            while abs(num) < min_count and index2 < len(formats[index1]) - 1:
                index2 += 1
                num *= 1000
        elif abs(num) >= max_count:
            index1 = 1
            while abs(num) >= max_count and index2 < len(formats[index1]) - 1:
                index2 += 1
                num /= 1000

        return (str(round(num, 12)).rstrip('0').rstrip('.') if '.' in str(num) else str(num)) + formats[index1][index2]

    def add_num_safe(a, b):
        return round(a + b, 12)

    def map(x, from_low, from_high, to_low, to_high):
        return (x - from_low) * (to_high - to_low) / (from_high - from_low) + to_low
