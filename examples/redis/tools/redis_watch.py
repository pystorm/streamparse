from redis import StrictRedis
import sys
from pprint import pprint

r = StrictRedis()
pprint(r.zrevrange("words", 0, -1, withscores=True),
       indent=4,
       width=40)
sys.stdout.flush()
