import random
import time

start = time.time()


def exponent_rand(first_val, expand_from, step, varying_rate, expand_rate, multiplier):
    delta_var = int((expand_from * varying_rate) / 100)

    if first_val > delta_var:
        result_var = float(first_val) * float(multiplier / expand_rate)
        if result_var == 0:
            result_var = float(first_val) * float(multiplier / 10)
        return int(result_var)
    else:
        rand_val = random.randrange(first_val, expand_from, step)
        return exponent_rand(rand_val, expand_from, step, varying_rate, expand_rate, multiplier)


var_rate = random.randint(5, 50)
exp_rate = random.randint(4, 15)
expanding = random.randint(100, 5000)

print(exponent_rand(10, 200, 10, var_rate, exp_rate, 11))

# for i in range(10, 1000):
#     print(exponent_rand(10, expanding, 10, var_rate, exp_rate, i))

end = time.time()
print(end - start)


asd = 'personal/cgshort/freelance/props/Building_1-515_9/work/Sculpt/versions'

spl = asd.split('/')

jn = '/'.join(spl[:-3])

print(jn)

