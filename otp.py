import random
def genotp():
    u_case=[chr(i) for i in range(ord('A'),ord('Z')+1)]
    l_case=[chr(i) for i in range(ord('a'),ord('z')+1)]
    otp=''
    for i in range(2):
        otp=otp+random.choice(u_case)+str(random.randint(0,9))+random.choice(l_case)
    return otp