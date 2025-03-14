"""
non-business logic functions, e.g. response normalization, data enrichment, etc.
"""
from string import ascii_letters, digits


async def hash_of_names(username: str, chatname: str) -> str:
    y = ''
    z = ''
    alphabet = {letter: ind for ind, letter in enumerate(list(ascii_letters) + list(digits))}
    for i in list(username):
        y += str(alphabet[i])
    for i in list(chatname):
        z += str(alphabet[i])

    return str(int(y) + int(z))



