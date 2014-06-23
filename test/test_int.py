def to_n_dig_float(num):

    if isinstance(num, str):
        return "{0:032.11f}".format(num) if num.isdigit() else num
    else:
        return num_str % num

def to_n_dig_int(num, digits=6):
    num_str = "%0" + str(digits) + "d"
    if isinstance(num, str):
        return num_str % int(num) if num.isdigit() else num
    else:
        return num_str % num


data_dicts = {'a':889, 'b':'567', 'c':'some_string' }
converted_ints = []
converted_ints.append( dict( (k, to_n_dig_int(v) ) for k, v in data_dicts.items() ) )

print converted_ints
